import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()       

SENDER = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASSWORD')
RECEIVER = os.getenv('RECEIVER_EMAIL')

def get_processed_data():
    df = pd.read_csv('daily_sales_mock.csv')
    df = df.sort_values(by=['LI_ID', 'date'])
    df['prev_spend'] = df.groupby('LI_ID')['spend'].shift(1)
    df['prev_impressions'] = df.groupby('LI_ID')['impressions'].shift(1)
    df['prev_cpm'] = (df['prev_spend'] / df['prev_impressions']) * 1000

    # -- LOGIC FUNCTIONS --
    def check_spend(row):
        if row['flight_days'] == 0: return "OK"
        ideal = row['total_budget'] / row['flight_days']
        if ideal > 0 and abs(row['spend'] - ideal)/ideal > 0.20: return "Pacing Deviation > 20%"
        if row['prev_spend'] > 0 and (row['spend'] - row['prev_spend'])/row['prev_spend'] > 0.25: return "Spend Spike > 25%"
        return "OK"

    def check_impr(row):
        if row['prev_impressions'] > 0:
            change = (row['impressions'] - row['prev_impressions']) / row['prev_impressions']
            if abs(change) > 0.20: return f"Impression Deviation {change:.0%}"
        return "OK"

    def check_kpi(row):
        curr_cpm = (row['spend']/row['impressions'])*1000 if row['impressions'] > 0 else 0
        if row['prev_cpm'] > 0:
            change = (curr_cpm - row['prev_cpm']) / row['prev_cpm']
            if abs(change) > 0.20: return f"CPM Spike {change:.0%}"
        return "OK"

    def check_action(row):
        curr_cpm = (row['spend']/row['impressions'])*1000 if row['impressions'] > 0 else 0
        if row['io_goal_cpm'] > 0 and (curr_cpm - row['io_goal_cpm'])/row['io_goal_cpm'] > 0.15:
            return "High CPM - Check URL"
        return "OK"

    def check_deal(row):
        if row['flight_days'] == 0 or row['io_goal_cpm'] == 0: return "OK"
        pct_time = row['days_elapsed'] / row['flight_days']
        exp_impr = (row['total_budget'] / (row['io_goal_cpm']/1000)) * pct_time
        if row['impressions'] < (exp_impr * 0.80): return "Major Impression Lag"
        return "OK"

    # Calculate Alerts
    df['Spend Alert'] = df.apply(check_spend, axis=1)
    df['Impression Alert'] = df.apply(check_impr, axis=1)
    df['KPI Alert'] = df.apply(check_kpi, axis=1)
    df['Placement Alert'] = df.apply(check_action, axis=1)
    df['Deal Health'] = df.apply(check_deal, axis=1)

    return df

# --- 2. GENERATE HTML REPORT (The New Part) ---

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


def send_alert():
    if not SENDER or not PASSWORD:
        print("Error: Credentials missing! Check your .env file.")
        return

    message = MIMEMultipart()
    message["From"] = SENDER
    message["To"] = RECEIVER
    message["Subject"] = "DV360 Alerts"

    body = email_body
    message.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECEIVER, message.as_string())
        print("Email sent successfully!")
        server.quit()
    except Exception as e:
        print(f"Error: {e}")


data = get_processed_data()
email_html = generate_email_body(data)

if email_html:
    # Basic CSS wrapper
    email_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        {email_html}
        <p style="font-size: 12px; color: #888;">Automated Report. IOs with no issues are hidden.</p>
    </body>
    </html>
    """

    # Send the email
    send_alert()

# if __name__ == "__main__":
#     send_alert()