import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from email_body import generate_email_body
from pacing import calculate_io_metrics, calculate_li_metrics
from impression import get_daily_impression_deviation
from kpi_alert import analyze_cpm_performance
from goal_alert import calculate_li_daily_metrics

load_dotenv()       

SENDER = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASSWORD')
RECEIVER = os.getenv('RECEIVER_EMAIL')

def filter_above_threshold(df, column_name, threshold):
    """
    Filters a DataFrame to return rows where the specified column exceeds the threshold.
    """
    # Create a copy to avoid SettingWithCopy warnings on the original dataframe
    filtered_df = df[abs(df[column_name]) > threshold].copy()
    
    return filtered_df


def send_alert():
    if not SENDER or not PASSWORD:
        print("Error: Credentials missing! Check your .env file.")
        return

    message = MIMEMultipart()
    message["From"] = SENDER
    message["To"] = RECEIVER
    message["Subject"] = "DV360 Alerts"
    
    body = "testing"
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECEIVER, message.as_string())
        print("Email sent successfully!")
        server.quit()
    except Exception as e:
        print(f"Error: {e}")

# if __name__ == "__main__":
#     send_alert()

# io_df_processed = calculate_io_metrics(pd.read_csv('Data.csv'), target_date_str='4/2/2025')
# #print('--- IO Results (4/2/2025) ---')
# print(filter_above_threshold(io_df_processed, 'Deviation %', 20)[['Date','Ideal Flight-to-Date Pacing', 'Actual Flight to Date Spend', 'Deviation %']])
# print(filter_above_threshold(io_df_processed, 'DoD Deviation %', 25)[['Date', 'Today Spend', 'Yesterday Spend', 'DoD Deviation %']])
# li_df_processed = calculate_li_metrics(pd.read_csv('LI_Data.csv'), target_date_str='4/2/2025')
# #print('--- LI Results (4/2/2025) ---')
# print(filter_above_threshold(li_df_processed, 'DoD Deviation %', 25)[['Date', 'Today Spend', 'Yesterday Spend', 'DoD Deviation %']])

# io_df_processed = get_daily_impression_deviation(pd.read_csv('Data.csv'), target_date_str='4/2/2025', entity_col='Insertion_Order_Name')
# li_df_processed = get_daily_impression_deviation(pd.read_csv('LI_Data.csv'), target_date_str='4/2/2025', entity_col='Line_Item_Name')
# #print('--- IO Results (4/2/2025) ---')
# print(filter_above_threshold(io_df_processed, 'Deviation %', 20)[["Today's Impressions", "Yesterday's Impressions", "Deviation %"]])
# #print('--- LI Results (4/2/2025) ---')
# print(filter_above_threshold(li_df_processed, 'Deviation %', 20)[["Today's Impressions", "Yesterday's Impressions", "Deviation %"]])

# li_df_processed = calculate_li_daily_metrics(pd.read_csv('Placement_Data.csv'), target_date_str='4/2/2025')
# print(filter_above_threshold(li_df_processed, 'CPM_Deviation%', 15)[['LI_CPM_Goal', 'Achieved_CPM', 'CPM_Deviation%']])
# print(filter_above_threshold(li_df_processed, 'CTR_Deviation%', 15)[['LI_CTR_Goal','Achieved_CTR%', 'CTR_Deviation%']])
