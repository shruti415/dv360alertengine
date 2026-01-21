import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

SENDER_EMAIL = os.getenv('EMAIL_USER')
SENDER_PASSWORD = 'your_app_password' 
RECEIVER_EMAIL = 'your_email@gmail.com'