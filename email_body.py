import pandas as pd

def generate_email_body(df):
    alert_columns = ['Spend Alert', 'Impression Alert', 'KPI Alert', 'Placement Alert', 'Deal Health']
    
    # Filter: Keep only rows where at least one alert is NOT 'OK'
    # This removes completely healthy Line Items from the dataset entirely
    mask = df[alert_columns].ne("OK").any(axis=1)
    df_errors = df[mask]

    if df_errors.empty:
        return None  # No email needed

    # Start HTML
    html_content = "<h2>🚨 Daily IO Scorecards</h2>"
    
    # Group by IO_ID
    for io_id, group in df_errors.groupby('IO_ID'):
        
        # Start a table for this IO
        io_table = f"""
        <div style="margin-bottom: 25px; border: 1px solid #ccc; border-radius: 5px; overflow: hidden;">
            <div style="background-color: #eee; padding: 10px; font-weight: bold; border-bottom: 1px solid #ccc;">
                IO ID: {io_id}
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="background-color: #f9f9f9; text-align: left;">
                    <th style="padding: 8px; border-bottom: 1px solid #ddd;">Alert Type</th>
                    <th style="padding: 8px; border-bottom: 1px solid #ddd; color: #d9534f;">Issue Detected</th>
                </tr>
        """
        
        # Loop through each Line Item in this IO
        for _, row in group.iterrows():
            # Check each of the 5 alert types
            for col in alert_columns:
                if row[col] != "OK":
                    # Add a row for this specific error
                    io_table += f"""
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{col}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; color: #d9534f; font-weight: bold;">{row[col]}</td>
                    </tr>
                    """
        
        io_table += "</table></div>"
        html_content += io_table

    return html_content