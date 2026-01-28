import pandas as pd
import numpy as np

# --- 1. IO Level PG Lag Check ---
def calculate_io_pg_lag(df, target_date_str, lag_threshold=-20.0):
    """
    Calculates Impression Lag for IOs on a specific date.
    Derives Total Impression Goal from (Budget / CPM).
    Alerts if Lag is worse than threshold (e.g., -5%).
    """
    df = df.copy()
    
    # 1. Date Parsing & Filtering
    target_date = pd.to_datetime(target_date_str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Filter for data "Uptill" target date for cumulative calculations
    # We need the full history to sum impressions, but only the specific IO settings
    history_df = df[df['Date'] <= target_date].copy()
    
    if history_df.empty:
        return pd.DataFrame()

    # 2. Get IO Static Details (Budget, Dates, Goal)
    # We take the latest settings for each IO (assuming rows might change)
    io_meta = history_df.sort_values('Date').groupby('Insertion_Order_Name').tail(1)
    io_meta = io_meta[[
        'Insertion_Order_Name', 'Planned_Budget', 
        'Insertion_Order_Goal_Value(KPI)', 'IO_Start_Date', 'IO_End_Date'
    ]].copy()

    # Clean numeric columns
    io_meta['Planned_Budget'] = pd.to_numeric(io_meta['Planned_Budget'], errors='coerce').fillna(0)
    io_meta['Insertion_Order_Goal_Value(KPI)'] = pd.to_numeric(io_meta['Insertion_Order_Goal_Value(KPI)'], errors='coerce').fillna(1) # avoid div/0
    io_meta['IO_Start_Date'] = pd.to_datetime(io_meta['IO_Start_Date'])
    io_meta['IO_End_Date'] = pd.to_datetime(io_meta['IO_End_Date'])

    # 3. Derive Total Impression Goal (The PG Target)
    # Formula: (Budget / CPM) * 1000
    io_meta['Derived_Impression_Goal'] = (io_meta['Planned_Budget'] / io_meta['Insertion_Order_Goal_Value(KPI)']) * 1000
    io_meta['Derived_Impression_Goal'] = io_meta['Derived_Impression_Goal'].round(0)

    # 4. Calculate Flight Metrics
    io_meta['Total_Flight_Days'] = (io_meta['IO_End_Date'] - io_meta['IO_Start_Date']).dt.days + 1
    io_meta['Days_Passed'] = (target_date - io_meta['IO_Start_Date']).dt.days + 1
    
    # Clip days passed
    io_meta['Days_Passed'] = io_meta['Days_Passed'].clip(lower=0)
    io_meta['Days_Passed'] = io_meta[['Days_Passed', 'Total_Flight_Days']].min(axis=1)

    # 5. Calculate Ideal FTD Impressions
    io_meta['Ideal_FTD_Impressions'] = (io_meta['Derived_Impression_Goal'] / io_meta['Total_Flight_Days']) * io_meta['Days_Passed']

    # 6. Get Actual FTD Impressions (Sum from history)
    actual_imps = history_df.groupby('Insertion_Order_Name')['Impressions'].sum().reset_index()
    actual_imps.rename(columns={'Impressions': 'Actual_FTD_Impressions'}, inplace=True)

    # 7. Merge & Calculate Lag
    result = pd.merge(io_meta, actual_imps, on='Insertion_Order_Name', how='left')
    result['Actual_FTD_Impressions'] = result['Actual_FTD_Impressions'].fillna(0)

    # Lag % = (Actual - Ideal) / Ideal
    result['Impression_Lag_%'] = np.where(
        result['Ideal_FTD_Impressions'] > 0,
        ((result['Actual_FTD_Impressions'] - result['Ideal_FTD_Impressions']) / result['Ideal_FTD_Impressions']) * 100,
        0.0
    )

    # 8. Generate Alert
    result['Alert_Status'] = np.where(
        result['Impression_Lag_%'] < lag_threshold,
        "PG Lag Alert: Under-pacing",
        "Stable"
    )

    # Formatting
    cols = [ 'Derived_Impression_Goal', 'Ideal_FTD_Impressions', 'Actual_FTD_Impressions', 'Impression_Lag_%', 'Alert_Status']
    result[cols[1:5]] = result[cols[1:5]].round(1)
    
    return result[cols]


# --- 2. LI Level PG Lag Check ---
def calculate_li_pg_lag(df, target_date_str, lag_threshold=-20.0):
    """
    Calculates Impression Lag for LI Level.
    Uses IO Planned Budget as the base for the goal (assuming LI contributes to IO).
    """
    df = df.copy()
    
    # 1. Date Parsing & Filtering
    target_date = pd.to_datetime(target_date_str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    history_df = df[df['Date'] <= target_date].copy()
    
    if history_df.empty:
        return pd.DataFrame()

    # 2. Get Meta Data (Group by Line Item)
    # Note: We use IO_Planned_Budget / Goal to get the goal
    li_meta = history_df.sort_values('Date').groupby('Line_Item_Name').tail(1)
    li_meta = li_meta[[
        'Line_Item_Name', 'IO_Planned_Budget', 'Insertion_Order_Goal_Value',
        'Line_Item_Start_Date', 'Line_Item_End_Date'
    ]].copy()

    # Clean numeric/date columns
    li_meta['IO_Planned_Budget'] = pd.to_numeric(li_meta['IO_Planned_Budget'], errors='coerce').fillna(0)
    li_meta['Insertion_Order_Goal_Value'] = pd.to_numeric(li_meta['Insertion_Order_Goal_Value'], errors='coerce').fillna(1)
    li_meta['Line_Item_Start_Date'] = pd.to_datetime(li_meta['Line_Item_Start_Date'])
    li_meta['Line_Item_End_Date'] = pd.to_datetime(li_meta['Line_Item_End_Date'])

    # 3. Derive Goal & Flight Info
    # WARNING: This assumes the LI is the only item running against this budget.
    # If multiple LIs share an IO, this 'Ideal' will be very high for a single LI.
    li_meta['Derived_Impression_Goal'] = (li_meta['IO_Planned_Budget'] / li_meta['Insertion_Order_Goal_Value']) * 1000
    
    li_meta['Total_LI_Days'] = (li_meta['Line_Item_End_Date'] - li_meta['Line_Item_Start_Date']).dt.days + 1
    li_meta['Days_Passed'] = (target_date - li_meta['Line_Item_Start_Date']).dt.days + 1
    li_meta['Days_Passed'] = li_meta['Days_Passed'].clip(lower=0)
    li_meta['Days_Passed'] = li_meta[['Days_Passed', 'Total_LI_Days']].min(axis=1)

    li_meta['Ideal_FTD_Impressions'] = (li_meta['Derived_Impression_Goal'] / li_meta['Total_LI_Days']) * li_meta['Days_Passed']

    # 4. Get Actual Stats
    actual_imps = history_df.groupby('Line_Item_Name')['Impressions'].sum().reset_index()
    actual_imps.rename(columns={'Impressions': 'Actual_FTD_Impressions'}, inplace=True)

    # 5. Merge & Calculate
    result = pd.merge(li_meta, actual_imps, on='Line_Item_Name', how='left')
    result['Actual_FTD_Impressions'] = result['Actual_FTD_Impressions'].fillna(0)

    result['Impression_Lag_%'] = np.where(
        result['Ideal_FTD_Impressions'] > 0,
        ((result['Actual_FTD_Impressions'] - result['Ideal_FTD_Impressions']) / result['Ideal_FTD_Impressions']) * 100,
        0.0
    )

    # 6. Alert
    result['Alert_Status'] = np.where(
        result['Impression_Lag_%'] < lag_threshold,
        "PG Lag Alert: Under-pacing",
        "Stable"
    )

    cols = [ 'Derived_Impression_Goal', 'Ideal_FTD_Impressions', 'Actual_FTD_Impressions', 'Impression_Lag_%', 'Alert_Status']
    result[cols[1:5]] = result[cols[1:5]].round(1)
    
    return result[cols]

# --- Execution ---

# Load Data
io_df = pd.read_csv('Data.csv')
li_df = pd.read_csv('LI_Data.csv')

target_date = '4/1/2025'

print(f"\n--- IO Level PG Lag Check for {target_date} ---")
io_check = calculate_io_pg_lag(io_df, target_date)
# Using to_string() to ensure all columns are visible
print(io_check.to_string())

print(f"\n--- LI Level PG Lag Check for {target_date} ---")
li_check = calculate_li_pg_lag(li_df, target_date)
print(li_check.to_string())