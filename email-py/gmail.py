import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- SMTP (Sending Email) ---
print("--- Sending Email (SMTP) ---")

sender_email = os.getenv("GMAIL_EMAIL")
app_password = os.getenv("GMAIL_APP_PASSWORD")
receiver_email = "dashboard@gmail.com"  # Recipient's email address
smtp_server = "smtp.gmail.com"
smtp_port = 587  # For TLS

try:
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Python SMTP"

    # Add body to email
    body = "This is a test email sent from Python using Gmail SMTP."
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, app_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
    print(f"Email sent successfully to {receiver_email}!")

except Exception as e:
    print(f"Error sending email: {e}")

print("-" * 30)

# --- IMAP (Receiving Email) ---
print("\n--- Receiving Email (IMAP) ---")

imap_server = "imap.gmail.com"
imap_port = 993  # For SSL

try:
    with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
        mail.login(sender_email, app_password)
        mail.select("inbox")  # Select the inbox

        status, email_ids = mail.search(None, "ALL")  # Get all email IDs
        email_id_list = email_ids[0].split()

        if not email_id_list:
            print("No emails found in the inbox.")
        else:
            # Fetch the latest email
            latest_email_id = email_id_list[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    print(f"From: {msg['from']}")
                    print(f"Subject: {msg['subject']}")
                    # Optionally, print the body of the email
                    if msg.is_multipart():
                        for part in msg.walk():
                            ctype = part.get_content_type()
                            cdisp = str(part.get("Content-Disposition"))

                            # handle plain text email
                            if ctype == "text/plain" and "attachment" not in cdisp:
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    print(
                                        f"Body: {body[:200]}..."
                                    )  # Print first 200 chars
                                except UnicodeDecodeError:
                                    print(
                                        "Could not decode email body (non-UTF-8 content)."
                                    )
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                            print(f"Body: {body[:200]}...")  # Print first 200 chars
                        except UnicodeDecodeError:
                            print("Could not decode email body (non-UTF-8 content).")
            print("Successfully fetched the latest email.")

except Exception as e:
    print(f"Error receiving email: {e}")

print("-" * 30)
