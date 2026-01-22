import pandas as pd
import io

def generate_impression_alert(file_path_or_buffer):
    """
    Analyzes CSV data to calculate Day-on-Day impression deviation 
    and determines pacing status.
    """
    
    # 1. Load Data
    try:
        df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        return f"Error reading CSV: {e}"

    # 2. Preprocessing
    # Ensure Date is in datetime format for proper sorting
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    
    # Sort data by Insertion Order and Date to ensure correct calculation order
    df = df.sort_values(by=['Insertion_Order_Name', 'Date'])

    # 3. Calculate Metrics
    # Group by Insertion Order to isolate calculations per campaign
    
    # A. Current Day Impressions (Already in 'Impressions')
    
    # B. Cumulative Average Impressions (Expanding Mean till that date)
    df['Average_Impressions_Till_Date'] = df.groupby('Insertion_Order_Name')['Impressions']\
                                            .expanding().mean().reset_index(level=0, drop=True)

    # C. Previous Day Impressions (Shift down by 1 within the group)
    df['Prev_Day_Impressions'] = df.groupby('Insertion_Order_Name')['Impressions'].shift(1)

    # D. DoD Deviation %: ((Current - Previous) / Previous) * 100
    df['Deviation_Pct'] = ((df['Impressions'] - df['Prev_Day_Impressions']) / df['Prev_Day_Impressions']) * 100

    # 4. Status Logic
    def get_status(row):
        # If it's the first day (NaN deviation), assume On Track or N/A
        if pd.isna(row['Deviation_Pct']):
            return "On Track"
            
        dev = row['Deviation_Pct']
        
        # Check thresholds
        if dev > 20:
            return f"Overpacing by {dev:.2f}%"
        elif dev < -20:
            # Absolute value for readability, or keep negative sign as preferred. 
            # Usually underpacing implies a drop.
            return f"Underpacing by {abs(dev):.2f}%"
        else:
            return "On Track"

    df['Status'] = df.apply(get_status, axis=1)

    # 5. Formatting & Cleanup
    # Select only the relevant columns requested
    final_columns = [
        'Date', 
        'Insertion_Order_Name', 
        'Impressions', 
        'Average_Impressions_Till_Date', 
        'Deviation_Pct', 
        'Status'
    ]
    
    result_df = df[final_columns].copy()
    
    # Format numbers for better readability
    result_df['Average_Impressions_Till_Date'] = result_df['Average_Impressions_Till_Date'].round(0).astype(int)
    result_df['Deviation_Pct'] = result_df['Deviation_Pct'].round(2)
    
    return result_df