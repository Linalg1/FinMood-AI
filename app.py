"""Run with: streamlit run app.py"""
from datetime import date
import pandas as pd
import streamlit as st
from storage import add_expense, add_mood, get_expenses, get_moods, seed_demo
from risk import forecast

st.set_page_config(page_title='FinMood AI', page_icon='💠', layout='wide')
st.title('FinMood AI')
st.caption('A prototype for conversational financial wellness + quantitative liquidity risk. Local demo, not a real Alexa+ connection.')

with st.sidebar:
    st.header('Scenario settings')
    balance = st.number_input('Current balance (€)', min_value=0., value=1800., step=100.)
    income = st.number_input('Monthly income (€; received on the 1st)', min_value=0., value=2200., step=100.)
    reserve = st.number_input('Minimum reserve (€)', min_value=0., value=200., step=50.)
    horizon = st.slider('Forecast days', 7, 90, 30)
    lookback = st.slider(
        "Historical lookback (days)",
        min_value=30,
        max_value=365,
        value=180,
        step=30
    )
    reduction = st.slider('Discretionary spending reduction scenario (%)', 0, 50, 15, 5)
    if st.button('Load synthetic demo data'):
        created = seed_demo()
        st.success('Synthetic demo data loaded.' if created else 'Data already exists. Demo data was not added.')
        st.rerun()

t1, t2, t3 = st.tabs(['Risk dashboard', 'Log transactions & mood', 'Voice-demo conversation'])

with t1:
    expenses = get_expenses()
    if not expenses:
        st.info('Start by loading synthetic demo data in the sidebar or logging an expense.')
    result = forecast(
        balance,
        expenses,
        monthly_income=income,
        reserve=reserve,
        horizon=horizon,
        lookback_days=lookback
    )    
    c1, c2, c3 = st.columns(3)
    c1.metric('Mean ending balance', f"€{result['expected_ending_balance']:,.0f}")
    c2.metric('Chance of dipping below reserve', f"{result['probability_reserve_breach']:.1%}")
    c3.metric('5th percentile ending balance', f"€{result['p05_ending_balance']:,.0f}")
    
    st.divider()

    st.subheader("Quantitative Risk Analytics")

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    with risk_col1:
        st.metric(
            "Liquidity-at-Risk (95%)",
            f"€{result['liquidity_at_risk_95']:,.2f}",
            help="95th percentile of simulated net cash deterioration, floored at zero."
        )

    with risk_col2:
        st.metric(
            "Expected Shortfall (95%)",
            f"€{result['expected_shortfall_95']:,.2f}",
            help="Average simulated net cash deterioration in the worst 5% of outcomes, including ties."
        )

    with risk_col3:
        st.metric(
            "Ending Balance Volatility",
            f"€{result['ending_balance_volatility']:,.2f}",
            help="Standard deviation of simulated ending balances."
        )

    st.caption(
        "These are illustrative risk estimates based on historical "
        "spending bootstrapping, not guarantees of future financial outcomes."
    )
    
    df = pd.DataFrame({'Date': pd.to_datetime(result['dates']), 'Mean': result['mean_path'],
                       'Low (5th percentile)': result['p05_path'], 'High (95th percentile)': result['p95_path']}).set_index('Date')
    st.line_chart(df)
    alternative = forecast(
        balance,
        expenses,
        monthly_income=income,
        reserve=reserve,
        horizon=horizon,
        spending_multiplier=1 - reduction / 100,
        lookback_days=lookback
    )
    st.write(f"**What-if scenario:** Reducing all simulated spending by {reduction}% changes reserve-breach probability from "
             f"**{result['probability_reserve_breach']:.1%}** to **{alternative['probability_reserve_breach']:.1%}**. "
             'This simplification reduces all spending, not just discretionary purchases.')
    st.subheader("Stress Scenario Comparison")

    comparison = pd.DataFrame({
        "Metric": [
            "Expected Ending Balance",
            "Liquidity-at-Risk (95%)",
            "Expected Shortfall (95%)",
            "Reserve Breach Probability"
        ],
        "Baseline": [
            result["expected_ending_balance"],
            result["liquidity_at_risk_95"],
            result["expected_shortfall_95"],
            result["probability_reserve_breach"]
        ],
        "Reduced Spending": [
            alternative["expected_ending_balance"],
            alternative["liquidity_at_risk_95"],
            alternative["expected_shortfall_95"],
            alternative["probability_reserve_breach"]
        ]
    })

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )
    st.caption(result['model'] + '. ' + result['limitations'])
    st.caption(
        f"Historical lookback: {result['lookback_days']} days. "
        f"Days with recorded expenses: {result['sample_expense_days']}. "
        "These estimates require sufficient historical data and "
        "independent validation before real-world use."
    )
with t2:
    a, b = st.columns(2)
    with a:
        st.subheader('New expense')
        with st.form('expense'):
            amount = st.number_input('Amount (€)', min_value=.01, value=12., step=1.)
            category = st.selectbox('Category', ['Food', 'Transport', 'Shopping', 'Bills', 'Other'])
            note = st.text_input('Note (optional)')
            if st.form_submit_button('Save expense'):
                add_expense(amount, category, note)
                st.success('Expense saved. Refresh or switch tabs to update the chart.')
    with b:
        st.subheader('Optional mood check-in')
        with st.form('mood'):
            mood = st.selectbox('How are you feeling?', ['Neutral', 'Happy', 'Calm', 'Stressed', 'Sad', 'Anxious'])
            note_m = st.text_input('Reflection (optional)')
            if st.form_submit_button('Save check-in'):
                add_mood(mood, note_m)
                st.success('Check-in saved privately in the local demo database.')
    st.subheader('Recent expenses')
    st.dataframe(pd.DataFrame(get_expenses()).head(20), use_container_width=True)
    st.subheader('Recent optional check-ins')
    st.dataframe(pd.DataFrame(get_moods()).head(10), use_container_width=True)

with t3:
    st.subheader('Alexa+ conversation storyboard (not yet integrated)')
    st.write('**You:** Alexa, what is my risk of running low on money this month?')
    st.write(f"**FinMood:** With the assumptions shown, the estimated chance of dipping below €{reserve:,.0f} "
             f"in the next {horizon} days is {result['probability_reserve_breach']:.1%}. "
             'This is a simulation, not a certainty.')
    st.write(f'**You:** What if I reduce spending by {reduction}%?')
    st.write(f"**FinMood:** In that scenario, the estimated probability changes to {alternative['probability_reserve_breach']:.1%}.")
    st.info('Next integration step: expose the API operations as an MCP server or supported Alexa+ agent tools. This storyboard is not an Alexa+ skill.')
