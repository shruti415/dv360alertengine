import pandas as pd
import numpy as np

def calculate_pg_impression_lag(df):
    """
    Calculates Programmatic Guaranteed (PG) Impression Lag.
    Derives Total Impression Goal from Budget & CPM if not explicitly present.
    """
    # 1. Preprocessing
    df = df.copy()
    date_cols = ['Date', 'IO_Start_Date', 'IO_End_Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
        
    num_cols = ['Planned_Budget', 'Insertion_Order_Goal_Value(KPI)', 'Impressions']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Sort for Cumulative Sum
    df = df.sort_values(by=['Insertion_Order_Name', 'Date'])

    # 2. Derive Total Impression Goal (Budget / CPM * 1000)
    # Note: If your dataset has a specific 'Impression Goal' column, use that instead.
    # Here we infer it from the planned budget and the target CPM.
    df['Total_Impression_Goal'] = (df['Planned_Budget'] / df['Insertion_Order_Goal_Value(KPI)']) * 1000
    
    # Handle cases where Goal Value is 0 to avoid infinity
    df['Total_Impression_Goal'] = df['Total_Impression_Goal'].replace([np.inf, -np.inf], 0).fillna(0)

    # 3. Calculate Cumulative Actual Impressions
    df['Cumulative_Impressions'] = df.groupby('Insertion_Order_Name')['Impressions'].cumsum()

    # 4. Calculate Expected Impressions (Flight-to-Date)
    # Time Progress
    df['Days_Elapsed'] = (df['Date'] - df['IO_Start_Date']).dt.days + 1
    df['Total_Days'] = (df['IO_End_Date'] - df['IO_Start_Date']).dt.days + 1
    
    # Cap Days to avoid errors
    df['Days_Elapsed'] = df['Days_Elapsed'].clip(lower=1, upper=df['Total_Days'])
    
    # Calculate Linear Expected Progress
    linear_target = (df['Total_Impression_Goal'] / df['Total_Days']) * df['Days_Elapsed']

    # Apply Pacing Logic (Even vs ASAP)
    # ASAP usually expects full delivery immediately, but for lag checks, 
    # we often compare against the full goal or a front-loaded curve.
    # Here we use: Even = Linear, ASAP = Full Goal immediately (strict check)
    
    conditions = [
        df['IO_Pacing_Rate'].str.lower() == 'even',
        df['IO_Pacing_Rate'].str.lower() == 'asap'
    ]
    
    choices = [
        linear_target,
        df['Total_Impression_Goal'] # Strict ASAP expectation
        #(linear_target * 2.0).clip(upper=df['Total_Impression_Goal']) # Lenient ASAP expectation
    ]
    
    df['Expected_Impressions_FD'] = np.select(conditions, choices, default=linear_target)

    # 5. Calculate Lag %
    # Formula: (Actual - Expected) / Expected
    safe_expected = df['Expected_Impressions_FD'].replace(0, np.nan)
    df['Impression_Lag_%'] = ((df['Cumulative_Impressions'] - safe_expected) / safe_expected) * 100
    df['Impression_Lag_%'] = df['Impression_Lag_%'].fillna(0)

    # 6. Determine Status
    # Threshold: If Actual is >5% below Expected, it's LAGGING.
    # (Using -5% allows for a small margin of error/reporting delay)
    lag_threshold = -5.0 
    
    df['PG_Status'] = np.where(df['Impression_Lag_%'] < lag_threshold, 'LAGGING', 'OK')
    
    # Optional: Add specific lag amount to status for clarity
    df['Status'] = np.where(
        df['PG_Status'] == 'LAGGING',
        "LAGGING (" + df['Impression_Lag_%'].round(1).astype(str) + "%)",
        "OK"
    )

    return df

# --- Test with your data ---
# df = pd.read_csv('Data.csv')
# results = calculate_pg_impression_lag(df)

# # Show Results
# cols = ['Date', 'Total_Impression_Goal', 'Cumulative_Impressions', 'Expected_Impressions_FD', 'Impression_Lag_%', 'PG_Status_Detail']
# print(results[cols].round(0).to_string())