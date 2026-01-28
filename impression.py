import pandas as pd
import numpy as np

def get_daily_impression_deviation(df, target_date_str, entity_col, date_col='Date', imp_col='Impressions'):
    """
    Returns deviation report for a specific date by comparing it strictly with (date - 1).
    """
    # 1. Parse Dates
    target_date = pd.to_datetime(target_date_str)
    previous_date = target_date - pd.Timedelta(days=1)
    
    # Ensure dataframe dates are datetime objects
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # 2. Extract Data for Target Date (Today) and Previous Date (Yesterday)
    today_data = df[df[date_col] == target_date].copy()
    yesterday_data = df[df[date_col] == previous_date].copy()

    # 3. Handle case where no data exists for target date
    if today_data.empty:
        return pd.DataFrame(columns=[entity_col, "Date", "Today's Impressions", "Yesterday's Impressions", "Deviation %"])

    # 4. Merge Data (Left Join ensures we keep all active entities from Today)
    # Suffixes help distinguish columns automatically: _today, _yesterday
    merged_df = pd.merge(
        today_data[[entity_col, imp_col, date_col]], 
        yesterday_data[[entity_col, imp_col]], 
        on=entity_col, 
        how='left', 
        suffixes=('', '_yesterday')
    )

    # 5. Clean up columns
    merged_df = merged_df.rename(columns={
        imp_col: "Today's Impressions",
        f'{imp_col}_yesterday': "Yesterday's Impressions"
    })

    # Fill NaNs for yesterday with 0 (implies it's a new entity or paused yesterday)
    merged_df["Yesterday's Impressions"] = merged_df["Yesterday's Impressions"].fillna(0)

    # 6. Calculate Deviation %
    merged_df['Deviation %'] = np.where(
        merged_df["Yesterday's Impressions"] > 0,
        ((merged_df["Today's Impressions"] - merged_df["Yesterday's Impressions"]) / merged_df["Yesterday's Impressions"]) * 100,
        0.0
    )

    return merged_df

# # --- Execution Example ---
# # Load Data
# io_df = pd.read_csv('Impression_Data.csv')
# li_df = pd.read_csv('LI_Data.csv')
# # 1. Calculate for IO Level for specific date
# print("--- IO Report for 4/1/2025 ---")
# io_report = get_daily_impression_deviation(
#     df=io_df, 
#     target_date_str='12/23/2025', 
#     entity_col='Campaign'
# )
# print(io_report[["Today's Impressions", "Yesterday's Impressions", "Deviation %"]].to_string())

# # 2. Calculate for LI Level for specific date (Example with 4/2/2025 to see deviation)
# print("\n--- LI Report for 4/2/2025 ---")
# li_report = get_daily_impression_deviation(
#     df=li_df, 
#     target_date_str='4/2/2025', 
#     entity_col='Line_Item_Name'
# )
# print(li_report[["Today's Impressions", "Yesterday's Impressions", "Deviation %"]].to_string())