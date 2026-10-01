import pandas as pd
import numpy as np

def load_and_process_data(uploaded_file, observation_end_date='2026-06-30'):
    """Parses raw subscriptions CSV stream buffer and computes lifetime values and tenure."""
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file)
    
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['canceled_at'] = pd.to_datetime(df['canceled_at'])
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    
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