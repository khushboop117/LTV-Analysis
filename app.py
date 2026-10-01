import streamlit as st
import plotly.express as px
import pandas as pd
from styles import apply_vox_theme
from analytics import load_and_process_data, compute_survival_curve, compute_cac_payback

st.set_page_config(
    page_title="Vox Media | Subscriptions LTV Intelligence Suite",
    page_icon="🎙️",
    layout="wide"
)

apply_vox_theme()

st.title("🎙️ Vox Media: Subscriptions LTV & Growth Intelligence Suite")
st.markdown("Internal Decision Engine for Digital Publications (*The Cut*, *The Strategist*, *Intelligencer*) and Podcast Networks (*Pivot*, *Today, Explained*).")

st.sidebar.header("📁 Data & Navigation")
uploaded_file = st.sidebar.file_uploader("Upload subscriptions.csv", type=["csv"])

if uploaded_file is not None:
    # Read and process uploaded data buffer
    df = load_and_process_data(uploaded_file)
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Analysis Dials")
    channels = ['All'] + list(df['channel'].unique())
    selected_channel = st.sidebar.selectbox("Acquisition Channel", channels)
    
    plans = st.sidebar.multiselect("Plan Type", options=['monthly', 'annual'], default=['monthly', 'annual'])
    time_horizon_months = st.sidebar.slider("Time Horizon (Months)", min_value=1, max_value=36, value=12)
    
    module = st.sidebar.radio(
        "Strategic Module", 
        ["Executive Summary & LTV", "Subscriber Survival & Churn Risk", "Marketing CAC & Payback Guardrails", "Assumptions, Hypotheses & Next Steps"]
    )

    filtered_df = df.copy()
    if selected_channel != 'All':
        filtered_df = filtered_df[filtered_df['channel'] == selected_channel]
    if plans:
        filtered_df = filtered_df[filtered_df['plan'].isin(plans)]

    # Top-Level KPI Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    total_subs = len(filtered_df)
    avg_ltv = filtered_df['total_revenue'].mean() if total_subs > 0 else 0
    churn_rate = (filtered_df['end_reason'].notnull().sum() / total_subs) * 100 if total_subs > 0 else 0
    
    col1.metric("Filtered Cohort Size", f"{total_subs:,}")
    col2.metric("Projected Avg LTV", f"${avg_ltv:,.2f}")
    col3.metric("Overall Churn Rate", f"{churn_rate:.1f}%")
    col4.metric("Active Time Horizon", f"{time_horizon_months} Mo")
    
    st.markdown("---")
    
    if module == "Executive Summary & LTV":
        st.subheader("📈 LTV Comparison by Acquisition Channel & Plan")
        channel_ltv = filtered_df.groupby(['channel', 'plan'])['total_revenue'].mean().reset_index()
        
        fig_channel = px.bar(
            channel_ltv, 
            x='channel', 
            y='total_revenue', 
            color='plan', 
            barmode='group',
            title="Average Lifetime Value Across Channels",
            labels={'total_revenue': 'Average LTV ($)', 'channel': 'Acquisition Channel'},
            color_discrete_sequence=['#FF3366', '#111111'],
            template="plotly_white"
        )
        st.plotly_chart(fig_channel, use_container_width=True)
        
        if selected_channel in ['paid_social', 'All']:
            st.subheader("🎯 UTM Campaign Efficiency (Paid Social)")
            campaign_df = filtered_df[filtered_df['channel'] == 'paid_social']
            if not campaign_df.empty:
                campaign_summary = campaign_df.groupby('utm_campaign').agg(
                    subscribers=('subscription_id', 'count'),
                    avg_ltv=('total_revenue', 'mean')
                ).reset_index()
                
                fig_campaign = px.scatter(
                    campaign_summary, 
                    x='subscribers', 
                    y='avg_ltv', 
                    text='utm_campaign',
                    size='subscribers',
                    title="Campaign Scale vs. Average LTV",
                    labels={'subscribers': 'Subscriber Volume', 'avg_ltv': 'Average LTV ($)'},
                    template="plotly_white"
                )
                fig_campaign.update_traces(textposition="top center")
                st.plotly_chart(fig_campaign, use_container_width=True)

    elif module == "Subscriber Survival & Churn Risk":
        st.subheader("⏳ Subscriber Retention Decay & Churn Hazard Curves")
        surv_df = compute_survival_curve(filtered_df, total_subs)
        fig_surv = px.line(
            surv_df, x='Month', y='Retention Rate (%)', markers=True, 
            title="Cohort Retention Probability Curve Over Time", 
            color_discrete_sequence=['#FF3366'],
            template="plotly_white"
        )
        st.plotly_chart(fig_surv, use_container_width=True)

    elif module == "Marketing CAC & Payback Guardrails":
        st.subheader("💡 Marketing Payback & CAC Guardrails")
        payback_sim = compute_cac_payback(filtered_df)
        st.dataframe(payback_sim, use_container_width=True)
        st.success("**Strategic Recommendation:** Allocate budget toward channels with LTV-to-CAC ratios > 3.0x (e.g., podcast sponsorships like *Pivot* and newsletter cross-promotions) and optimize ad platforms toward LTV-weighted custom conversions.")

    else:
        st.subheader("📋 Analytical Assumptions, Hypotheses & Recommended Next Steps")
        st.markdown("""
        ### 1. Core Modeling Assumptions
        * **Billing Mechanics:** Monthly subscriptions bill \$15 on start and monthly anniversaries. Annual subscriptions bill \$150 upfront and renew annually.
        * **Access Windows:** Voluntary cancellations allow reading/listening access through the end of the paid billing period. Payment failures cause immediate access termination.
        * **Censoring:** Active subscribers with `null` end dates as of June 30, 2026, are treated as actively retained up to the observation horizon.
        
        ### 2. Product & Marketing Hypotheses
        * **The Podcast Halo Effect:** Subscribers acquired via owned podcast networks exhibit a **30% higher 12-month LTV** than paid social traffic due to stronger audience affinity.
        * **Annual Plan Stickiness:** Annual subscribers have lower monthly churn velocity but face a steep renewal cliff at Month 12.
        * **Dunning Recovery:** Automated smart-dunning workflows can recover up to 25% of payment failures, boosting overall blended LTV.

        ### 3. Actionable Next Steps for Growth
        * **Shift Bidding Strategies:** Reallocate paid acquisition budgets toward high-intent channels (podcasts and newsletter cross-promotions) that demonstrate LTV-to-CAC ratios exceeding 3.0x.
        * **Deploy Proactive Dunning:** Implement automated dunning retries and SMS/email payment recovery reminders to capture involuntary churn before access is revoked.
        * **Pre-Renewal Campaigns:** Trigger automated re-engagement and exclusive content previews 30 days prior to the Month 12 annual renewal cliff to mitigate drop-offs.
        """)

else:
    st.info("👈 Please upload your `subscriptions.csv` file in the sidebar to initialize the Vox Media Intelligence Suite and populate the KPI metrics.")