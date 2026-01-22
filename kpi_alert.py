import pandas as pd
import numpy as np

def detect_kpi_anomalies(df):
    """
    Calculates Achieved KPI and detects 20% deviation DoD and WoW.
    Returns the specific checklist message for anomalies.
    """
    # 1. Preprocessing
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ensure numeric columns (handle potential bad formatting)
    num_cols = ['Spends', 'Impressions', 'Clicks', 'Complete_Views']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Sort to ensure Shift operations work chronologically per IO
    df = df.sort_values(by=['Insertion_Order_Name', 'Date'])

    # 2. Calculate "Achieved KPI" based on Goal Type
    # We use np.select for vectorized performance (faster than .apply)
    # Formula: CPM = (Spend/Imp)*1000, CPC = Spend/Click, CPV = Spend/View
    
    conditions = [
        df['Insertion_Order_Goal_Type'] == 'CPM',
        df['Insertion_Order_Goal_Type'] == 'CPC',
        df['Insertion_Order_Goal_Type'] == 'CPV'
    ]
    
    # Avoid Division by Zero using np.where inside the calculation choices
    cpm_calc = np.where(df['Impressions'] > 0, (df['Spends'] / df['Impressions']) * 1000, 0)
    cpc_calc = np.where(df['Clicks'] > 0, df['Spends'] / df['Clicks'], 0)
    cpv_calc = np.where(df['Complete_Views'] > 0, df['Spends'] / df['Complete_Views'], 0)
    
    choices = [cpm_calc, cpc_calc, cpv_calc]
    
    df['Achieved_KPI'] = np.select(conditions, choices, default=0)

    # 3. Calculate DoD (Day over Day) and WoW (Week over Week) Metrics
    # We group by IO so we don't compare different campaigns
    g = df.groupby('Insertion_Order_Name')['Achieved_KPI']
    
    df['Prev_Day_KPI'] = g.shift(1)
    df['Prev_Week_KPI'] = g.shift(7) # 7 days ago

    # 4. Calculate Deviation Percentage
    # Formula: (Current - Previous) / Previous
    # We replace infinity (caused by 0 previous value) with 0
    df['DoD_Deviation'] = ((df['Achieved_KPI'] - df['Prev_Day_KPI']) / df['Prev_Day_KPI']).replace([np.inf, -np.inf], 0).fillna(0)
    df['WoW_Deviation'] = ((df['Achieved_KPI'] - df['Prev_Week_KPI']) / df['Prev_Week_KPI']).replace([np.inf, -np.inf], 0).fillna(0)

    # 5. Generate Alert
    # Condition: Absolute deviation > 20% (0.20)
    threshold = 0.20
    alert_msg = 'Inventory-wise CPM check, Deal/ Open Auction CPM check'
    
    anomaly_mask = (df['DoD_Deviation'].abs() > threshold) | (df['WoW_Deviation'].abs() > threshold)
    
    df['Status'] = np.where(anomaly_mask, alert_msg, 'Stable')

    # Formatting for readability (Optional)
    df['Achieved_KPI'] = df['Achieved_KPI'].round(2)
    df['DoD_Deviation_%'] = (df['DoD_Deviation'] * 100).round(2)
    df['WoW_Deviation_%'] = (df['WoW_Deviation']*100).round(2)
    
    return df

# df = pd.read_csv('Data.csv')
# result_df = detect_kpi_anomalies(df)

# # Display relevant columns
# cols = ['Date', 'Achieved_KPI', 'DoD_Deviation_%','WoW_Deviation_%', 'Status']
# print(result_df[cols].to_string())