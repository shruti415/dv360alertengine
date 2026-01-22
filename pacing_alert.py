import pandas as pd
import numpy as np
from datetime import datetime

def pre_process_data(file_path):
    df = pd.read_csv(file_path)

    # 2. Pre-processing: Convert columns to DateTime
    date_cols = ['Date', 'IO_Start_Date', 'IO_End_Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
    return df

def calculate_deviation(row):
    # We add 1 to include the current day/end day in the duration
    total_flight_days = (row['IO_End_Date'] - row['IO_Start_Date']).days + 1
    days_elapsed = (row['Date'] - row['IO_Start_Date']).days + 1
    
    # Safety Check: Prevent division by zero
    if total_flight_days <= 0: return pd.Series(["Error", 0.0])
    
    # Calculate % Time Elapsed (Capped at 1.0/100%)
    time_progress = min(max(days_elapsed / total_flight_days, 0.0), 1.0)
    
    # B. Calculate Expected Spend based on Pacing Type
    budget = row['Planned_Budget']
    pacing_type = row['IO_Pacing'].lower()
    
    expected_spend = 0.0
    
    if 'even' in pacing_type:
        # Linear: If 10% time passed, expect 10% spend
        expected_spend = budget * time_progress
        
    elif 'ahead' in pacing_type:
        # Front-loaded: Inverted Parabola logic (y = x(2-x))
        # Spending is aggressive early, then tapers
        curve_factor = time_progress * (2 - time_progress)
        expected_spend = budget * curve_factor
        
    elif 'asap' in pacing_type:
        # ASAP expects 100% of budget to be spent immediately
        # (Or as much as possible). We compare against the full budget.
        expected_spend = budget
        
    else:
        # Fallback for unknown types
        expected_spend = budget * time_progress

    # C. Calculate Deviation %
    # Formula: (Actual - Expected) / Expected
    if expected_spend == 0:
        deviation = 0.0
    else:
        deviation = ((row['Spends'] - expected_spend) / expected_spend) * 100

    # D. Determine Flag (The +/- 20% Rule)
    status = "On Track"
    
    if 'asap' in pacing_type:
        # ASAP Logic: You generally can't be "Overpaced" (faster is better).
        # You are only "Underpaced" if you have budget left.
        # However, for a strict +/- 20 check:
        if deviation < -20: 
            status = f"Underpaced by {round(abs(deviation), 2)}%"
        # We ignore positive deviation for ASAP as it's usually impossible 
        # (unless you spent more than the total IO budget)
    else:
        # Standard Logic for Even/Ahead
        if deviation > 20:
            status = f"Overpaced by {round(abs(deviation), 2)}%"
        elif deviation < -20:
            status = f"Underpaced by {round(abs(deviation), 2)}%"
            
    return pd.Series([status, round(deviation, 2), round(expected_spend, 2)])

# Apply the function
# df = pre_process_data('Data.csv')
# df[['Pacing_Status', 'Deviation_%', 'Expected_Spend']] = df.apply(calculate_deviation, axis=1)

# # # Display the result
# print(df[['IO_Pacing', 'Planned_Budget', 'Spends', 'Expected_Spend', 'Deviation_%', 'Pacing_Status']])