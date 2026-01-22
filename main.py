import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from email_body import generate_email_body
from pacing_alert import pre_process_data, calculate_deviation

load_dotenv()       

SENDER = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASSWORD')
RECEIVER = os.getenv('RECEIVER_EMAIL')

df = pre_process_data('Data.csv')
df[['Pacing_Status', 'Deviation_%', 'Expected_Spend']] = df.apply(calculate_deviation, axis=1)

# print(df[['IO_Pacing', 'Planned_Budget', 'Spends', 'Expected_Spend', 'Deviation_%', 'Pacing_Status']])

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

if __name__ == "__main__":
    send_alert()