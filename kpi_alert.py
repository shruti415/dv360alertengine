import pandas as pd
import numpy as np

def calculate_kpi_metrics(df, target_date_str): # <--- CHANGED: Renamed function to reflect new purpose
    """
    Calculates Achieved KPI, Yesterday's KPI, and Last Week's KPI for a SPECIFIC DATE.
    Also calculates DoD and WoW deviation percentages.
    """
    # 1. Preprocessing & Date Setup
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    target_date = pd.to_datetime(target_date_str)
    prev_day_date = target_date - pd.Timedelta(days=1)
    prev_week_date = target_date - pd.Timedelta(days=7)

    # Ensure numeric columns
    num_cols = ['Spends', 'Impressions', 'Clicks', 'Complete_Views']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. Calculate "Achieved KPI" (Logic Unchanged)
    conditions = [
        df['Insertion_Order_Goal_Type'] == 'CPM',
        df['Insertion_Order_Goal_Type'] == 'CPC',
        df['Insertion_Order_Goal_Type'] == 'CPV'
    ]
    
    cpm_calc = np.where(df['Impressions'] > 0, (df['Spends'] / df['Impressions']) * 1000, 0)
    cpc_calc = np.where(df['Clicks'] > 0, df['Spends'] / df['Clicks'], 0)
    cpv_calc = np.where(df['Complete_Views'] > 0, df['Spends'] / df['Complete_Views'], 0)
    
    choices = [cpm_calc, cpc_calc, cpv_calc]
    df['Achieved_KPI'] = np.select(conditions, choices, default=0)

    # 3. Split Data for Merge (Target, Yesterday, Last Week)
    
    # A. Target Date (Today's KPI)
    today_df = df[df['Date'] == target_date].copy()
    today_df = today_df.rename(columns={'Achieved_KPI': "Today's KPI"}) # <--- CHANGED: Renamed for final output
    
    # B. Previous Day Data (Yesterday's KPI)
    yesterday_df = df[df['Date'] == prev_day_date][['Insertion_Order_Name', 'Achieved_KPI']].copy()
    yesterday_df = yesterday_df.rename(columns={'Achieved_KPI': "Yesterday's KPI"}) # <--- CHANGED: Renamed
    
    # C. Previous Week Data (Last Week KPI)
    last_week_df = df[df['Date'] == prev_week_date][['Insertion_Order_Name', 'Achieved_KPI']].copy()
    last_week_df = last_week_df.rename(columns={'Achieved_KPI': "Last Week KPI"}) # <--- CHANGED: Renamed

    # 4. Merge Logic
    final_df = pd.merge(today_df, yesterday_df, on='Insertion_Order_Name', how='left')
    final_df = pd.merge(final_df, last_week_df, on='Insertion_Order_Name', how='left')

    # Fill NaNs for missing history
    final_df["Yesterday's KPI"] = final_df["Yesterday's KPI"].fillna(0)
    final_df["Last Week KPI"] = final_df["Last Week KPI"].fillna(0)

    # 5. Calculate Deviation Percentage
    
    # DoD Deviation
    final_df['DoD Deviation %'] = np.where(
        final_df["Yesterday's KPI"] > 0,
        ((final_df["Today's KPI"] - final_df["Yesterday's KPI"]) / final_df["Yesterday's KPI"]) * 100,
        0.0
    )

    # WoW Deviation
    final_df['WoW Deviation %'] = np.where(
        final_df["Last Week KPI"] > 0,
        ((final_df["Today's KPI"] - final_df["Last Week KPI"]) / final_df["Last Week KPI"]) * 100,
        0.0
    )

    # <--- CHANGED: Removed Status/Threshold logic completely

    # Formatting (Rounding for clean output)
    cols_to_round = ["Today's KPI", "Yesterday's KPI", "Last Week KPI", 'DoD Deviation %', 'WoW Deviation %']
    final_df[cols_to_round] = final_df[cols_to_round].round(2)
    
    return final_df

# --- Execution Example ---
# df = pd.read_csv('Data.csv')

# # # Calculate for a specific date
# result_df = calculate_kpi_metrics(df, target_date_str='4/8/2025') 

# cols = ['Date', "Today's KPI", "Yesterday's KPI", 'DoD Deviation %', "Last Week KPI", 'WoW Deviation %']
# print(result_df[cols].to_string())