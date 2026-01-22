import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from email_body import generate_email_body
from pacing_alert import calculate_pacing_alerts
from impression_alert import generate_impression_alert
from kpi_alert import detect_kpi_anomalies

load_dotenv()       

SENDER = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASSWORD')
RECEIVER = os.getenv('RECEIVER_EMAIL')

pacing_df = calculate_pacing_alerts(pd.read_csv('Data.csv'))
impression_df = generate_impression_alert('Data.csv')
kpi_df = detect_kpi_anomalies(pd.read_csv('Data.csv'))
# print(df[['IO_Pacing', 'Planned_Budget', 'Spends', 'Expected_Spend', 'Deviation_%', 'Pacing_Status']])
# print(pacing_df.iloc[0])
# print(impression_df.iloc[0])

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