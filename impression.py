import pandas as pd
import numpy as np

def check_daily_impression_deviation(df: pd.DataFrame, target_date: str):
    """
    Calculates daily impression goals and flags deviations > 20% for a specific date.
    
    Args:
        df (pd.DataFrame): The raw dataframe containing campaign data.
        target_date (str): The date to analyze (format flexible, e.g., '12/5/2025' or '2025-12-05').
        
    Returns:
        pd.DataFrame: A filtered dataframe containing the calculations and status for the target date.
    """
    # 1. Create a copy to avoid SettingWithCopy warnings on the original df
    #    and ensure Date column is in datetime format for accurate comparison
    df_processed = df.copy()
    df_processed['Date'] = pd.to_datetime(df_processed['Date'])
    target_date_dt = pd.to_datetime(target_date)
    
    # 2. OPTIMIZATION: Filter by date first to reduce computation on large datasets
    daily_data = df_processed[df_processed['Date'] == target_date_dt].copy()
    
    if daily_data.empty:
        print(f"No data found for date: {target_date}")
        return daily_data

    # 3. Ensure calculation columns are numeric and handle dates
    daily_data['IO_Start_Date'] = pd.to_datetime(daily_data['IO_Start_Date'])
    daily_data['IO_End_Date'] = pd.to_datetime(daily_data['IO_End_Date'])
    
    # 4. Calculate Flight Duration (Inclusive of start and end date)
    #    Adding 1 day because 12/5 to 12/5 is usually considered 1 day of activity
    daily_data['Total_Flight_Duration'] = (daily_data['IO_End_Date'] - daily_data['IO_Start_Date']).dt.days + 1
    
    # 5. Calculate Daily Impression Goal
    #    Formula: impression budget / (IO goal value * total flight duration)
    #    Using .div() to handle potential division by zero gracefully if needed
    denominator = daily_data['IO_Goal_Value'] * daily_data['Total_Flight_Duration']
    daily_data['Daily_Impression_Goal'] = daily_data['IO_Impr_Budget'] / denominator
    
    # 6. Calculate % Deviation
    #    Formula: |(Actual - Goal) / Goal| * 100
    daily_data['Deviation_Pct'] = (
        abs(daily_data['Impressions'] - daily_data['Daily_Impression_Goal']) 
        / daily_data['Daily_Impression_Goal']
    ) * 100
    
    # 7. Set Status ('Alert' if > 20%, else 'OK')
    daily_data['Status'] = np.where(daily_data['Deviation_Pct'] > 20, 'Alert', 'OK')
    
    # Optional: Formatting for readability (rounding)
    daily_data['Daily_Impression_Goal'] = daily_data['Daily_Impression_Goal'].round(0)
    daily_data['Deviation_Pct'] = daily_data['Deviation_Pct'].round(2)

    return daily_data

# --- Example Usage ---

df = pd.read_csv('Impression_Data.csv')

# 2. Running the function for a specific date
result_df = check_daily_impression_deviation(df, '12/18/2025')

# 3. Displaying relevant columns
cols_to_show = ['Date', 'Impressions', 'Daily_Impression_Goal', 'Deviation_Pct', 'Status']
print(result_df[cols_to_show].to_string(index=False))