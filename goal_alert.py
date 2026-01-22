import pandas as pd
import numpy as np

def calculate_cpm(df):
    """
    Calculates Cost Per Mille (CPM).
    Formula: (Spends / Impressions) * 1000
    """
    # Avoid division by zero by replacing 0 impressions with NaN temporarily
    safe_impressions = df['Impressions'].replace(0, np.nan)
    cpm = (df['Spends'] / safe_impressions) * 1000
    return cpm.fillna(0)  # Return 0 if calculation failed

def calculate_vtr(df):
    """
    Calculates View Through Rate (VTR).
    Formula: Complete Views / Impressions
    """
    # Avoid division by zero
    safe_impressions = df['Impressions'].replace(0, np.nan)
    vtr = (df['Complete_Views'] / safe_impressions)
    return vtr.fillna(0) * 100 # returning as percentage for easier comparison if needed

def analyze_kpi_deviations(df):
    """
    Main driver function to calculate achieved KPIs and flag deviations based on Goal Type.
    
    Logic:
    - If Goal Type is CPM: Calculate CPM. Flag if Actual > Expected * 1.15 (+15%)
    - If Goal Type is VTR: Calculate VTR. Flag if Actual < Expected * 0.85 (-15%)
    """
    # 1. Preprocessing
    df = df.copy()
    
    # Ensure numeric types
    num_cols = ['Spends', 'Impressions', 'Complete_Views', 'Insertion_Order_Goal_Value(KPI)']
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. Vectorized Calculation of both Metrics
    # We calculate both columns for the whole dataset first (fastest way in Pandas)
    df['Achieved_CPM'] = calculate_cpm(df)
    
    # Note: If your Goal Value for VTR is in %, ensure consistency. 
    # Usually VTR goal in IOs is like '70' for 70% or '0.7'. 
    # Assuming the input data 'Insertion_Order_Goal_Value(KPI)' for VTR is a percentage like 70.
    # The calculate_vtr function returns a percentage (0-100).
    df['Achieved_VTR'] = calculate_vtr(df)

    # 3. Determine 'Actual_KPI' based on Goal Type
    # We select the relevant metric based on the 'Insertion_Order_Goal_Type' column
    conditions_kpi = [
        df['Insertion_Order_Goal_Type'].str.upper() == 'CPM',
        df['Insertion_Order_Goal_Type'].str.upper() == 'VTR'
    ]
    
    choices_kpi = [
        df['Achieved_CPM'],
        df['Achieved_VTR']
    ]
    
    df['Actual_KPI_Value'] = np.select(conditions_kpi, choices_kpi, default=0)

    # 4. Calculate Deviation Percentage
    # Formula: (Actual - Expected) / Expected
    expected = df['Insertion_Order_Goal_Value(KPI)'].replace(0, np.nan)
    df['Deviation_%'] = ((df['Actual_KPI_Value'] - expected) / expected) * 100
    df['Deviation_%'] = df['Deviation_%'].fillna(0)

    # 5. Generate Status Flags
    # Rule 1: CPM > 15% deviation (Overspending/Expensive)
    # Rule 2: VTR < -15% deviation (Underperforming/Low Engagement)
    
    cpm_high_mask = (df['Insertion_Order_Goal_Type'].str.upper() == 'CPM') & (df['Deviation_%'] > 15)
    vtr_low_mask = (df['Insertion_Order_Goal_Type'].str.upper() == 'VTR') & (df['Deviation_%'] < -15)
    
    conditions_status = [
        cpm_high_mask,
        vtr_low_mask
    ]
    
    choices_status = [
        "High CPM Alert (>15%)",
        "Low VTR Alert (<-15%)"
    ]
    
    df['Status'] = np.select(conditions_status, choices_status, default="On Track")

    return df


# Simulate reading the CSV
# df = pd.read_csv('Data.csv')
# # Apply the function
# results = analyze_kpi_deviations(df)

# # Formatting for display
# cols_to_show = ['Date', 'Insertion_Order_Goal_Type', 'Insertion_Order_Goal_Value(KPI)', 'Actual_KPI_Value', 'Deviation_%', 'Status']
# print(results[cols_to_show].round(2).to_string())