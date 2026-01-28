import pandas as pd
import numpy as np

def analyze_cpm_performance(df, analysis_date_str):
    """
    Analyzes CPM performance for a specific date, calculating DoD changes,
    FTD metrics, and generating alerts based on custom logic.
    
    Args:
        df (pd.DataFrame): The raw dataset containing ad performance data.
        analysis_date_str (str): The specific date to analyze (format: 'm/d/yyyy' or 'yyyy-mm-dd').
        
    Returns:
        pd.DataFrame: A filtered dataframe containing metrics and status for the requested date.
    """
    
    # 1. Data Cleaning & Type Conversion
    # Ensure dates are datetime objects for correct sorting and comparison
    df['Date'] = pd.to_datetime(df['Date'])
    df['IO_Start_Date'] = pd.to_datetime(df['IO_Start_Date'])
    
    # Ensure numeric columns are floats/ints to prevent math errors
    numeric_cols = ['Spends', 'Impressions', 'Insertion_Order_Goal_Value(KPI)']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Convert analysis date to datetime
    target_date = pd.to_datetime(analysis_date_str)
    
    # ---------------------------------------------------------
    # 1. Calculate Daily Achieved CPM
    # Formula: (Spends / Impressions) * 1000
    # We use np.where to handle division by zero safely
    # ---------------------------------------------------------
    df['Daily_Achieved_CPM'] = np.where(
        df['Impressions'] > 0,
        (df['Spends'] / df['Impressions']) * 1000,
        0.0
    )

    # ---------------------------------------------------------
    # 2. Compare DoD Achieved CPM Percentage
    # We must sort by IO and Date to ensure we compare correctly
    # ---------------------------------------------------------
    df = df.sort_values(by=['Insertion_Order_Name', 'Date'])
    
    # Group by IO to ensure we don't shift data between different campaigns
    df['Prev_Day_CPM'] = df.groupby('Insertion_Order_Name')['Daily_Achieved_CPM'].shift(1)
    
    # Calculate DoD Change %: ((Current - Prev) / Prev) * 100
    # Handle cases where Prev_Day_CPM is 0 or NaN
    df['DoD_CPM_Change_Pct'] = np.where(
        df['Prev_Day_CPM'] > 0,
        ((df['Daily_Achieved_CPM'] - df['Prev_Day_CPM']) / df['Prev_Day_CPM']) * 100,
        0.0
    )

    # ---------------------------------------------------------
    # 3 & 4. Calculate Flight-to-Date (FTD) Metrics
    # We use cumulative sums grouped by IO to get running totals up to each date
    # ---------------------------------------------------------
    
    # Filter only data relevant to the flight (Date >= Start Date)
    # This ensures we don't count pre-flight testing if any exists
    flight_mask = df['Date'] >= df['IO_Start_Date']
    
    # Calculate Cumulative Spends and Impressions per IO
    df['FTD_Spends'] = df[flight_mask].groupby('Insertion_Order_Name')['Spends'].cumsum()
    df['FTD_Impressions'] = df[flight_mask].groupby('Insertion_Order_Name')['Impressions'].cumsum()
    
    # Calculate FTD Achieved CPM
    df['FTD_Achieved_CPM'] = np.where(
        df['FTD_Impressions'] > 0,
        (df['FTD_Spends'] / df['FTD_Impressions']) * 1000,
        0.0
    )
    
    # Get FTD Goal CPM
    # Assuming 'Insertion_Order_Goal_Value(KPI)' is the target CPM
    df['FTD_Goal_CPM'] = df['Insertion_Order_Goal_Value(KPI)']

    # ---------------------------------------------------------
    # 5. Filter for Target Date & Apply Alert Logic
    # ---------------------------------------------------------
    
    # Filter dataset for the specific date requested
    report_df = df[df['Date'] == target_date].copy()
    
    if report_df.empty:
        return f"No data found for date: {analysis_date_str}"

    # Alert Logic:
    # DoD CPM change percentage > 20% AND FTD Achieved CPM < FTD Goal CPM
    
    # Note: 'DoD_CPM_Change_Pct' is percentage (e.g., 25.0 for 25%).
    # Condition: > 20
    
    condition_high_volatility = report_df['DoD_CPM_Change_Pct'] > 20
    condition_under_goal = report_df['FTD_Achieved_CPM'] < report_df['FTD_Goal_CPM']
    
    report_df['Status'] = np.where(
        condition_high_volatility & condition_under_goal,
        'Alert',
        'OK'
    )
    
    # ---------------------------------------------------------
    # formatting Output for readability
    # ---------------------------------------------------------
    output_columns = [
        'Date','Insertion_Order_Name' ,'Daily_Achieved_CPM', 
        'DoD_CPM_Change_Pct', 'FTD_Goal_CPM', 'FTD_Achieved_CPM', 'Status'
    ]
    
    # Rounding for clean display
    report_df['Daily_Achieved_CPM'] = report_df['Daily_Achieved_CPM'].round(2)
    report_df['DoD_CPM_Change_Pct'] = report_df['DoD_CPM_Change_Pct'].round(2)
    report_df['FTD_Achieved_CPM'] = report_df['FTD_Achieved_CPM'].round(2)
    
    return report_df[output_columns]

# --- Usage Example with your Data ---

# # Create DataFrame
# df = pd.read_csv('Data.csv')

# # Run the function for the second date (so we can see DoD changes)
# result = analyze_cpm_performance(df, '4/2/2025')

# # Display
# print(result.to_string())