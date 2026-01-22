import pandas as pd
import numpy as np

def check_spend_pacing(df):
    """
    Alert 1: Spend and Pacing Alert
    Condition: Daily spend deviates ±20% from ideal pacing; Sudden day-on-day spend spike (>25%)
    """
    df_metrics = df.copy()
    
    # Calculate flight duration and ideal daily spend (Linear Pacing)
    # Assumption: Ideal Daily Spend = Planned Budget / Total Days in Flight
    df_metrics['Flight_Days'] = (df_metrics['IO End Date'] - df_metrics['IO Start Date']).dt.days + 1
    df_metrics['Ideal_Daily_Spend'] = df_metrics['Planned Budget'] / df_metrics['Flight_Days']
    
    # 1. Daily Deviation Calculation
    df_metrics['Spend_Deviation_Pct'] = (df_metrics['Spends'] - df_metrics['Ideal_Daily_Spend']) / df_metrics['Ideal_Daily_Spend']
    
    # 2. Day-on-Day Spike Calculation
    df_metrics['Prev_Spend'] = df_metrics.groupby('Insertion Order Name')['Spends'].shift(1)
    df_metrics['DoD_Spend_Change'] = (df_metrics['Spends'] - df_metrics['Prev_Spend']) / df_metrics['Prev_Spend']
    
    # Filter Alerts
    pacing_alerts = df_metrics[abs(df_metrics['Spend_Deviation_Pct']) > 0.20].copy()
    pacing_alerts['Alert_Description'] = 'Spend Deviation > 20% from Ideal'
    
    spike_alerts = df_metrics[df_metrics['DoD_Spend_Change'] > 0.25].copy()
    spike_alerts['Alert_Description'] = 'DoD Spend Spike > 25%'
    
    return pd.concat([pacing_alerts, spike_alerts])

def check_impression_alert(df):
    """
    Alert 2: Impression Alert Agent
    Condition: Alert when impression deviates by 20% on a d-o-d basis
    """
    df_metrics = df.copy()
    
    # Calculate DoD Change
    df_metrics['Prev_Imps'] = df_metrics.groupby('Insertion Order Name')['Impressions'].shift(1)
    df_metrics['DoD_Imp_Change'] = (df_metrics['Impressions'] - df_metrics['Prev_Imps']) / df_metrics['Prev_Imps']
    
    # Filter Alerts (Absolute deviation > 20%)
    alerts = df_metrics[abs(df_metrics['DoD_Imp_Change']) > 0.20].copy()
    alerts['Alert_Description'] = 'Impression DoD Deviation > 20%'
    
    return alerts

def check_kpi_spikes(df):
    """
    Alert 3: CPM/CPC/VTR Spike Alert Agent
    Condition: D-o-D 20% increase / decrease
    """
    df_metrics = df.copy()
    
    # Calculate Metrics (Handling division by zero)
    df_metrics['CPM'] = np.where(df_metrics['Impressions'] > 0, (df_metrics['Spends'] / df_metrics['Impressions']) * 1000, 0)
    df_metrics['CPC'] = np.where(df_metrics['Clicks'] > 0, df_metrics['Spends'] / df_metrics['Clicks'], 0)
    df_metrics['VTR'] = np.where(df_metrics['Impressions'] > 0, df_metrics['Complete Views (Video)'] / df_metrics['Impressions'], 0)
    
    alerts_list = []
    
    for metric in ['CPM', 'CPC', 'VTR']:
        prev_col = f'Prev_{metric}'
        change_col = f'{metric}_DoD_Change'
        
        # Calculate Shift and Change
        df_metrics[prev_col] = df_metrics.groupby('Insertion Order Name')[metric].shift(1)
        df_metrics[change_col] = (df_metrics[metric] - df_metrics[prev_col]) / df_metrics[prev_col]
        
        # Filter Alerts
        temp_alerts = df_metrics[abs(df_metrics[change_col]) > 0.20].copy()
        if not temp_alerts.empty:
            temp_alerts['Alert_Description'] = f'{metric} Spike > 20%'
            temp_alerts['Metric_Value'] = temp_alerts[metric]
            temp_alerts['Change_Pct'] = temp_alerts[change_col]
            alerts_list.append(temp_alerts)
            
    if alerts_list:
        return pd.concat(alerts_list)
    return pd.DataFrame()

# def check_placement_alert(df):


def check_impression_lag(df):
    """
    Alert 5: PG Deal Check Agent
    Condition: Check flight to date impression lag
    """
    df_metrics = df.copy()
    
    # Derive Total Impression Goal (Budget / Target CPM * 1000)
    df_metrics['Est_Total_Imp_Goal'] = (df_metrics['Planned Budget'] / df_metrics['Insertion Order Goal Value']) * 1000
    
    # Calculate Expected Cumulative Impressions (Linear Pacing)
    df_metrics['Flight_Days'] = (df_metrics['IO End Date'] - df_metrics['IO Start Date']).dt.days + 1
    df_metrics['Day_Of_Flight'] = (df_metrics['Date'] - df_metrics['IO Start Date']).dt.days + 1
    df_metrics['Expected_Cum_Imps'] = (df_metrics['Est_Total_Imp_Goal'] / df_metrics['Flight_Days']) * df_metrics['Day_Of_Flight']
    
    # Calculate Actual Cumulative Impressions
    df_metrics['Actual_Cum_Imps'] = df_metrics.groupby('Insertion Order Name')['Impressions'].cumsum()
    
    # Calculate Lag %
    df_metrics['Impression_Lag_Pct'] = (df_metrics['Actual_Cum_Imps'] - df_metrics['Expected_Cum_Imps']) / df_metrics['Expected_Cum_Imps']
    
    # Alert if lag is significant (e.g., lagging by more than 10%)
    alerts = df_metrics[df_metrics['Impression_Lag_Pct'] < -0.10].copy()
    alerts['Alert_Description'] = 'Impression Lag > 10%'
    
    return alerts

# --- Example Usage ---
# Assuming 'df' is your loaded DataFrame with dates parsed
# df['Date'] = pd.to_datetime(df['Date'])
# df['IO Start Date'] = pd.to_datetime(df['IO Start Date'])
# df['IO End Date'] = pd.to_datetime(df['IO End Date'])
# df = df.sort_values(by=['Insertion Order Name', 'Date'])

# spend_alerts = check_spend_pacing(df)
# imp_alerts = check_impression_alert(df)
# kpi_alerts = check_kpi_spikes(df)
# lag_alerts = check_impression_lag(df)