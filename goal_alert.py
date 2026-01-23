import pandas as pd
import numpy as np

def calculate_li_daily_metrics(df, target_date_str):
    """
    Calculates CPM, CTR, and VTR percentages for Line Items for a specific date.
    Also calculates deviations from goals if goal columns exist.
    """
    # 1. Efficient Date Filtering
    # We convert the target date once and filter strictly for that day
    target_date = pd.to_datetime(target_date_str)
    
    # Ensure Date column is datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Filter for the specific date
    daily_df = df[df['Date'] == target_date].copy()
    
    if daily_df.empty:
        print(f"No data found for {target_date_str}")
        return pd.DataFrame()

    # 2. Preprocessing & Data Cleaning
    # Handle numeric columns (fill NaNs with 0)
    # Note: 'Revenue' is typically used as 'Spend' in DV360 data
    metric_cols = ['Revenue', 'Impressions', 'Clicks']
    
    # Add Complete_Views if it exists, otherwise ignore safely
    if 'Complete_Views' in df.columns:
        metric_cols.append('Complete_Views')
        
    for col in metric_cols:
        daily_df[col] = pd.to_numeric(daily_df[col], errors='coerce').fillna(0)

    # 3. Aggregation
    # Group by Line Item to sum metrics across multiple Apps/URLs for that day
    # We preserve Goal columns by including them in groupby
    group_cols = ['Line_Item', 'LI_CPM_Goal', 'LI_CTR_Goal']
    
    # If dataset has missing goals, fill them to avoid dropping rows during groupby
    daily_df['LI_CPM_Goal'] = daily_df['LI_CPM_Goal'].fillna(0)
    daily_df['LI_CTR_Goal'] = daily_df['LI_CTR_Goal'].fillna(0)
    
    agg_df = daily_df.groupby(group_cols)[metric_cols].sum().reset_index()

    # 4. Metric Calculations
    
    # A. CPM (Cost Per Mille) = (Revenue / Impressions) * 1000
    agg_df['Achieved_CPM'] = np.where(
        agg_df['Impressions'] > 0,
        (agg_df['Revenue'] / agg_df['Impressions']) * 1000,
        0.0
    )

    # B. CTR % (Click Through Rate) = (Clicks / Impressions) * 100
    agg_df['Achieved_CTR%'] = np.where(
        agg_df['Impressions'] > 0,
        (agg_df['Clicks'] / agg_df['Impressions']) * 100,
        0.0
    )

    # C. VTR % (View Through Rate) - Checks if column exists
    if 'Complete_Views' in agg_df.columns:
        agg_df['Achieved_VTR%'] = np.where(
            agg_df['Impressions'] > 0,
            (agg_df['Complete_Views'] / agg_df['Impressions']) * 100,
            0.0
        )
    else:
        agg_df['Achieved_VTR%'] = 0.0 # Default if column missing

    # 5. Deviation Calculations (vs Goals)
    
    # Clean Goal Columns (Remove '%' and convert to float)
    def clean_goal(col):
        return pd.to_numeric(col.astype(str).str.replace('%', '', regex=False), errors='coerce').fillna(0)

    agg_df['Goal_CPM_Clean'] = clean_goal(agg_df['LI_CPM_Goal'])
    agg_df['Goal_CTR_Clean'] = clean_goal(agg_df['LI_CTR_Goal'])

    # CPM Deviation %
    agg_df['CPM_Deviation%'] = np.where(
        agg_df['Goal_CPM_Clean'] > 0,
        ((agg_df['Achieved_CPM'] - agg_df['Goal_CPM_Clean']) / agg_df['Goal_CPM_Clean']) * 100,
        0.0
    )

    # CTR Deviation %
    agg_df['CTR_Deviation%'] = np.where(
        agg_df['Goal_CTR_Clean'] > 0,
        ((agg_df['Achieved_CTR%'] - agg_df['Goal_CTR_Clean']) / agg_df['Goal_CTR_Clean']) * 100,
        0.0
    )

    # 6. Formatting
    cols_to_round = ['Achieved_CPM', 'Achieved_CTR%', 'Achieved_VTR%', 'CPM_Deviation%', 'CTR_Deviation%']
    agg_df[cols_to_round] = agg_df[cols_to_round].round(2)

    # Select final columns for output
    final_cols = ['LI_CPM_Goal', 'Achieved_CPM', 'CPM_Deviation%', 'LI_CTR_Goal','Achieved_CTR%', 'CTR_Deviation%']
    
    return agg_df[final_cols]

# --- Example Usage ---
df = pd.read_csv('Placement_Data.csv')
results = calculate_li_daily_metrics(df, target_date_str='2025/03/25')
print(results.to_string())