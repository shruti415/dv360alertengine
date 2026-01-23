import pandas as pd
import numpy as np

# Load Data
io_df = pd.read_csv('Data.csv')
li_df = pd.read_csv('LI_Data.csv')

# --- 1. IO Level Function ---
def calculate_io_metrics(df, target_date_str): # <--- CHANGED: Added target_date_str
    """
    Calculates metrics for IO Level for a SPECIFIC DATE.
    """
    # 1. Configuration
    entity_col = 'Insertion_Order_Name'
    date_col = 'Date'
    spend_col = 'Spends'
    budget_col = 'Planned_Budget'
    start_col = 'IO_Start_Date'
    end_col = 'IO_End_Date'

    # 2. Date Parsing
    # <--- CHANGED: Parse target and previous dates
    target_date = pd.to_datetime(target_date_str)
    prev_date = target_date - pd.Timedelta(days=1)
    
    for col in [date_col, start_col, end_col]:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3. FTD Calculations (Must run on FULL dataset first to get correct cumsum)
    df = df.sort_values(by=[entity_col, date_col])
    
    # Actual FTD Spend (Cumulative Sum of history)
    df['Actual Flight to Date Spend'] = df.groupby(entity_col)[spend_col].cumsum()
    
    # Ideal FTD Pacing
    df['Total_Flight_Days'] = (df[end_col] - df[start_col]).dt.days + 1
    df['Days_Passed'] = (df[date_col] - df[start_col]).dt.days + 1
    df['Days_Passed'] = df['Days_Passed'].clip(lower=0)
    df['Days_Passed'] = df[['Days_Passed', 'Total_Flight_Days']].min(axis=1)
    
    daily_run_rate = df[budget_col] / df['Total_Flight_Days']
    df['Ideal Flight-to-Date Pacing'] = daily_run_rate * df['Days_Passed']
    
    # Calculate FTD Deviation %
    df['Deviation %'] = np.where(
        df['Ideal Flight-to-Date Pacing'] > 0,
        ((df['Actual Flight to Date Spend'] - df['Ideal Flight-to-Date Pacing']) / df['Ideal Flight-to-Date Pacing']) * 100,
        0.0
    )

    # --- CHANGED: DoD Logic (Strict Merge for Specific Date) ---
    
    # A. Filter for Today's Data (Retaining the FTD calculations made above)
    today_df = df[df[date_col] == target_date].copy()
    
    # B. Fetch Yesterday's Spend strictly from the previous date
    yesterday_df = df[df[date_col] == prev_date][[entity_col, spend_col]].copy()
    yesterday_df = yesterday_df.rename(columns={spend_col: 'Yesterday Spend'})
    
    # C. Merge to bring "Yesterday Spend" into "Today's" row
    final_df = pd.merge(today_df, yesterday_df, on=entity_col, how='left')
    
    # D. Renaming and Clean up
    final_df['Yesterday Spend'] = final_df['Yesterday Spend'].fillna(0)
    final_df['Today Spend'] = final_df[spend_col] # Create explicit column
    
    # E. Calculate DoD Deviation
    final_df['DoD Deviation %'] = np.where(
        final_df['Yesterday Spend'] > 0,
        ((final_df['Today Spend'] - final_df['Yesterday Spend']) / final_df['Yesterday Spend']) * 100,
        0.0
    )

    # Cleanup temporary columns
    final_df.drop(columns=['Total_Flight_Days', 'Days_Passed'], inplace=True, errors='ignore')
    
    return final_df


# --- 2. Line Item (LI) Level Function ---
def calculate_li_metrics(df, target_date_str): # <--- CHANGED: Added target_date_str
    """
    Calculates metrics for Line Item Level for a SPECIFIC DATE.
    """
    # 1. Configuration
    entity_col = 'Line_Item_Name'
    date_col = 'Date'
    spend_col = 'LI_Spends'
    budget_col = 'IO_Planned_Budget' 
    start_col = 'Line_Item_Start_Date'
    end_col = 'Line_Item_End_Date'

    # 2. Date Parsing
    # <--- CHANGED: Parse target and previous dates
    target_date = pd.to_datetime(target_date_str)
    prev_date = target_date - pd.Timedelta(days=1)

    for col in [date_col, start_col, end_col]:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3. FTD Calculations (Must run on FULL dataset)
    df = df.sort_values(by=[entity_col, date_col])
    
    # Actual FTD Spend
    df['Actual Flight to Date Spend'] = df.groupby(entity_col)[spend_col].cumsum()
    
    # Ideal FTD Pacing
    df['Total_LI_Days'] = (df[end_col] - df[start_col]).dt.days + 1
    df['Days_Passed'] = (df[date_col] - df[start_col]).dt.days + 1
    df['Days_Passed'] = df['Days_Passed'].clip(lower=0)
    df['Days_Passed'] = df[['Days_Passed', 'Total_LI_Days']].min(axis=1)

    daily_run_rate = df[budget_col] / df['Total_LI_Days']
    df['Ideal Flight-to-Date Pacing'] = daily_run_rate * df['Days_Passed']

    df['Deviation %'] = np.where(
        df['Ideal Flight-to-Date Pacing'] > 0,
        ((df['Actual Flight to Date Spend'] - df['Ideal Flight-to-Date Pacing']) / df['Ideal Flight-to-Date Pacing']) * 100,
        0.0
    )

    # --- CHANGED: DoD Logic (Strict Merge for Specific Date) ---
    
    # A. Filter for Today
    today_df = df[df[date_col] == target_date].copy()
    
    # B. Fetch Yesterday
    yesterday_df = df[df[date_col] == prev_date][[entity_col, spend_col]].copy()
    yesterday_df = yesterday_df.rename(columns={spend_col: 'Yesterday Spend'})
    
    # C. Merge
    final_df = pd.merge(today_df, yesterday_df, on=entity_col, how='left')
    
    # D. Clean up
    final_df['Yesterday Spend'] = final_df['Yesterday Spend'].fillna(0)
    final_df['Today Spend'] = final_df[spend_col]

    # E. Calculate DoD
    final_df['DoD Deviation %'] = np.where(
        final_df['Yesterday Spend'] > 0,
        ((final_df['Today Spend'] - final_df['Yesterday Spend']) / final_df['Yesterday Spend']) * 100,
        0.0
    )

    # Cleanup
    final_df.drop(columns=['Total_LI_Days', 'Days_Passed'], inplace=True, errors='ignore')

    return final_df

# --- Execution ---

# <--- CHANGED: Passing the specific date parameter
# print("Processing IO Metrics for 4/1/2025...")
# # Note: 4/1 is the start, so Yesterday Spend should be 0 and DoD 0%
# io_df_processed = calculate_io_metrics(io_df.copy(), target_date_str='4/2/2025')

# print("Processing LI Metrics for 4/2/2025...")
# # Note: 4/2 will compare against 4/1
# li_df_processed = calculate_li_metrics(li_df.copy(), target_date_str='4/2/2025')

# # --- Display Results ---
# cols_to_show = ['Date', 'Today Spend', 'Yesterday Spend', 'DoD Deviation %', 'Ideal Flight-to-Date Pacing', 'Actual Flight to Date Spend', 'Deviation %']

# print("\n--- IO Results (4/1/2025) ---")
# print(io_df_processed[cols_to_show].to_string())

# print("\n--- LI Results (4/2/2025) ---")
# print(li_df_processed[cols_to_show].to_string())