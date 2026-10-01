import pandas as pd
import numpy as np

def load_and_process_data(uploaded_file_or_path, observation_end_date='2026-06-30'):
    if isinstance(uploaded_file_or_path, str):
        df = pd.read_csv(uploaded_file_or_path)
    else:
        uploaded_file_or_path.seek(0)
        df = pd.read_csv(uploaded_file_or_path)
    
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['canceled_at'] = pd.to_datetime(df['canceled_at'], errors='coerce')
    df['ended_at'] = pd.to_datetime(df['ended_at'], errors='coerce')
    
    obs_end = pd.to_datetime(observation_end_date)
    df['effective_end'] = df['ended_at'].fillna(obs_end)
    df['lifetime_days'] = (df['effective_end'] - df['created_at']).dt.days
    df['lifetime_months'] = np.ceil(df['lifetime_days'] / 30.44).astype(int)
    
    def calculate_revenue(row):
        months = max(1, row['lifetime_months'])
        if row['plan'] == 'monthly':
            return months * 15.0
        else:
            years_active = np.ceil(months / 12.0)
            return years_active * 150.0
            
    df['total_revenue'] = df.apply(calculate_revenue, axis=1)
    return df

def compute_survival_curve(df, total_subs):
    months_range = list(range(1, 25))
    survival_data = []
    for m in months_range:
        active_at_m = len(df[df['lifetime_months'] >= m])
        retention_rate = (active_at_m / total_subs) * 100 if total_subs > 0 else 0
        survival_data.append({'Month': m, 'Retention Rate (%)': retention_rate})
    return pd.DataFrame(survival_data)

def compute_cac_payback(filtered_df):
    payback_sim = filtered_df.groupby('channel').agg(
        Subscribers=('subscription_id', 'count'),
        Avg_LTV=('total_revenue', 'mean')
    ).reset_index()
    
    benchmark_cac = {
        'organic': 10.0, 
        'paid_social': 45.0, 
        'newsletter': 25.0, 
        'podcast': 60.0, 
        'direct': 5.0
    }
    payback_sim['Estimated_CAC'] = payback_sim['channel'].map(benchmark_cac).fillna(30.0)
    payback_sim['LTV_to_CAC_Ratio'] = (payback_sim['Avg_LTV'] / payback_sim['Estimated_CAC']).round(2)
    payback_sim['Payback_Period (Mo)'] = (payback_sim['Estimated_CAC'] / (payback_sim['Avg_LTV'] / 12)).round(1)
    
    payback_sim['Avg_LTV'] = payback_sim['Avg_LTV'].map('${:,.2f}'.format)
    payback_sim['Estimated_CAC'] = payback_sim['Estimated_CAC'].map('${:,.2f}'.format)
    payback_sim['LTV_to_CAC_Ratio'] = payback_sim['LTV_to_CAC_Ratio'].astype(str) + 'x'
    payback_sim['Payback_Period (Mo)'] = payback_sim['Payback_Period (Mo)'].astype(str) + ' mo'
    
    return payback_sim

def compute_churn_risk_scoring(df):
    """Scores active subscribers for churn risk based on plan, tenure, and historical drop-off risk."""
    active_df = df[df['ended_at'].isnull()].copy()
    
    # Heuristic scoring model: Monthly plans near month 1 or annual plans near month 12 have higher risk
    def risk_score(row):
        tenure = row['lifetime_months']
        if row['plan'] == 'monthly':
            # Monthly risk peaks around month 1 and month 3
            score = 0.45 if tenure <= 1 else (0.30 if tenure <= 3 else 0.15)
        else:
            # Annual risk peaks near renewal (month 11-12)
            score = 0.60 if (tenure >= 10 and tenure <= 12) else 0.20
        return round(score * 100, 1)
        
    active_df['Churn_Risk_Score (%)'] = active_df.apply(risk_score, axis=1)
    
    def risk_tier(score):
        if score >= 40:
            return 'High Risk 🚨'
        elif score >= 25:
            return 'Medium Risk ⚠️'
        else:
            return 'Low Risk ✅'
            
    active_df['Risk_Tier'] = active_df['Churn_Risk_Score (%)'].apply(risk_tier)
    return active_df[['subscription_id', 'channel', 'plan', 'lifetime_months', 'Churn_Risk_Score (%)', 'Risk_Tier']]
