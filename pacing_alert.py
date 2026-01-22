import pandas as pd
import numpy as np

def calculate_pacing_alerts(df):
    # 1. Pre-processing: Date Conversion
    date_cols = ['Date', 'IO_Start_Date', 'IO_End_Date']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])

    # 2. Sort to ensure Cumulative Calculation is correct
    df = df.sort_values(by=['Insertion_Order_Name', 'Date'])

    # 3. Calculate Key Time Metrics
    # Add 1 to include the current day
    df['Total_Days'] = (df['IO_End_Date'] - df['IO_Start_Date']).dt.days + 1
    df['Days_Elapsed'] = (df['Date'] - df['IO_Start_Date']).dt.days + 1
    
    # Cap Days_Elapsed to ensure we don't calculate past the flight end
    df['Days_Elapsed'] = df['Days_Elapsed'].clip(lower=1, upper=df['Total_Days'])

    # 4. Calculate Cumulative Spend (The "Apples-to-Apples" Fix)
    # We must compare Cumulative Target vs Cumulative Spend
    df['Cumulative_Spend'] = df.groupby('Insertion_Order_Name')['Spends'].cumsum()

    # 5. Calculate "Even" Linear Target
    # (Total Budget / Total Days) * Days Elapsed
    even_target = (df['Planned_Budget'] / df['Total_Days']) * df['Days_Elapsed']

    # 6. Apply Pacing Logic (Vectorized)
    # Ahead = 120% of Even Pace (capped at Planned Budget)
    # ASAP = 100% of Budget immediately
    
    pacing_type = df['IO_Pacing'].str.lower()
    
    conditions = [
        pacing_type.str.contains('ahead'),
        pacing_type.str.contains('asap')
    ]
    
    choices = [
        (even_target * 1.2).clip(upper=df['Planned_Budget']), # Ahead Logic
        df['Planned_Budget']                                  # ASAP Logic
    ]
    
    # Default to 'even_target' if neither condition is met
    df['Ideal_Spend_to_Date'] = np.select(conditions, choices, default=even_target)

    # 7. Calculate Deviation
    # Formula: (Actual - Expected) / Expected
    # We replace 0 with NaN to avoid ZeroDivisionError
    safe_ideal = df['Ideal_Spend_to_Date'].replace(0, np.nan)
    df['Deviation_%'] = ((df['Cumulative_Spend'] - safe_ideal) / safe_ideal) * 100
    df['Deviation_%'] = df['Deviation_%'].fillna(0).round(2)

    # 8. Generate Alert Status (Vectorized)
    # Deviation > 20% = Overspending
    # Deviation < -20% = Underspending
    # ASAP is special: You can't really "overspend" unless you exceed total budget
    
    conditions_status = [
        (pacing_type.str.contains('asap')) & (df['Deviation_%'] < -20), # ASAP Underspend
        (df['Deviation_%'] > 20),  # General Overspend
        (df['Deviation_%'] < -20)  # General Underspend
    ]
    
    choices_status = [
        "Underspending (ASAP)",
        "Overspending",
        "Underspending"
    ]
    
    df['Pacing_Status'] = np.select(conditions_status, choices_status, default="On Track")
    
    # Optional: Add the specific % to the status string for readability
    # (Note: This step is slower, do only if necessary for export)
    mask_alert = df['Pacing_Status'] != "On Track"
    df.loc[mask_alert, 'Pacing_Status'] = df.loc[mask_alert, 'Pacing_Status'] + " by " + df['Deviation_%'].abs().astype(str) + "%"

    return df

# Usage
# df = pd.read_csv('Data.csv')
# df_result = calculate_pacing_alerts(df)
# print(df_result[['Date', 'IO_Pacing_Rate', 'Cumulative_Spend', 'Ideal_Spend_to_Date', 'Deviation_%', 'Pacing_Status']])