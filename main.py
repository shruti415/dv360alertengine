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
from gemini_api import generate_prompt_from_dataframe, send_prompt_and_store

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

IO_df = pd.read_csv('Data.csv')
LI_df = pd.read_csv('LI_Data.csv')

# io_df_processed = calculate_io_metrics(IO_df, target_date_str='4/2/2025')
# pacing_ftd_IO =filter_above_threshold(io_df_processed, 'Deviation %', 20)[['Date', 'Insertion_Order_Name','Ideal Flight-to-Date Pacing', 'Actual Flight to Date Spend', 'Deviation %']]
# pacing_DoD_IO = filter_above_threshold(io_df_processed, 'DoD Deviation %', 25)[['Date','Insertion_Order_Name', 'Today Spend', 'Yesterday Spend', 'DoD Deviation %']]

# li_df_processed = calculate_li_metrics(LI_df, target_date_str='4/2/2025')
# pacing_DoD_LI = filter_above_threshold(li_df_processed, 'DoD Deviation %', 25)[['Date','Insertion_Order', 'Today Spend', 'Yesterday Spend', 'DoD Deviation %']]

kpi_df = analyze_cpm_performance(IO_df, '4/2/2025')

# # Creating one list from all dataframes:
df_list = []
df_list.append("### This is the CPM Data for IO Level, reports alert where CPM DoD deviation is over 20 percent and FTD achieved CPM is less than target FTD CPM :\n" + kpi_df.to_csv(index=False))

generate_prompt_from_dataframe(df_list)
print(send_prompt_and_store(df_list))