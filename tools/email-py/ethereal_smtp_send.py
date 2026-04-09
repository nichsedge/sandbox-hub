import smtplib
import os
import random
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

smtp_host = os.getenv("SMTP_HOST")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
to_email = os.getenv("IMAP_USER")  # recipient is the IMAP account

rin = random.randint(1, 10)
msg = MIMEText("Hello! This is a test email sent via Ethereal between two accounts.")

msg["Subject"] = f"[TICKET] something {rin}"
msg["From"] = smtp_user
msg["To"] = to_email

with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, to_email, msg.as_string())

print("✅ Email sent successfully!")
