import smtplib
import imaplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Retrieve Credentials from Environment Variables ---
sender_email = os.getenv('GMAIL_EMAIL')
app_password = os.getenv('GMAIL_APP_PASSWORD')

# Basic check to ensure credentials are loaded
if not sender_email or not app_password:
    raise ValueError("Gmail email or app password not found in environment variables. "
                     "Please check your .env file and ensure GMAIL_EMAIL and GMAIL_APP_PASSWORD are set.")

# --- IMAP (Receiving Email) ---
print("\n--- Receiving Email (IMAP) ---")

def get_filtered_unread_emails(
    email_address,
    app_password,
    filter_by='today', # 'today', 'date_range', or 'all'
    start_date=None,   # datetime object for date_range
    end_date=None,     # datetime object for date_range
    mark_as_read=False # New parameter: True to mark as read, False to peek only
):
    """
    Connects to Gmail via IMAP and retrieves unread emails,
    optionally filtered by today's date or a specific date range.
    """
    imap_server = 'imap.gmail.com'
    imap_port = 993 # For SSL
    unread_emails = []

    try:
        with imaplib.IMAP4_SSL(imap_server, imap_port) as mail:
            mail.login(email_address, app_password)
            mail.select('inbox') # Select the inbox

            search_criteria = ['UNSEEN'] # Start with unread filter

            if filter_by == 'today':
                # Current date for SENTSINCE. Using 2025-08-14 as per context.
                today_date = datetime(2025, 8, 14).strftime('%d-%b-%Y')
                search_criteria.append('SENTSINCE')
                search_criteria.append(today_date)
                print(f"Searching for unread emails sent since: {today_date}")
            elif filter_by == 'date_range':
                if not start_date or not end_date:
                    raise ValueError("start_date and end_date must be provided for 'date_range' filter.")
                start_date_str = start_date.strftime('%d-%b-%Y')
                end_date_str = end_date.strftime('%d-%b-%Y')
                search_criteria.append('SENTSINCE')
                search_criteria.append(start_date_str)
                search_criteria.append('SENTBEFORE')
                search_criteria.append(end_date_str)
                print(f"Searching for unread emails sent between {start_date_str} and {end_date_str}")
            elif filter_by == 'all':
                print("Searching for all unread emails.")
            else:
                raise ValueError("Invalid filter_by option. Use 'today', 'date_range', or 'all'.")

            status, email_ids = mail.search(None, *search_criteria)
            email_id_list = email_ids[0].split()

            if not email_id_list:
                print("No matching unread emails found.")
                return []

            for email_id in email_id_list:
                fetch_command = '(BODY.PEEK[])' if not mark_as_read else '(RFC822)'
                status, msg_data = mail.fetch(email_id, fetch_command)

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        email_info = {
                            'From': msg.get('from'),
                            'Subject': msg.get('subject'),
                            'Body': ''
                        }

                        if msg.is_multipart():
                            for part in msg.walk():
                                ctype = part.get_content_type()
                                cdisp = str(part.get('Content-Disposition'))
                                if ctype == 'text/plain' and 'attachment' not in cdisp:
                                    try:
                                        email_info['Body'] = part.get_payload(decode=True).decode()
                                    except UnicodeDecodeError:
                                        email_info['Body'] = "[Could not decode email body (non-UTF-8 content)]"
                                    break
                        else:
                            try:
                                email_info['Body'] = msg.get_payload(decode=True).decode()
                            except UnicodeDecodeError:
                                email_info['Body'] = "[Could not decode email body (non-UTF-8 content)]"

                        unread_emails.append(email_info)

                        if mark_as_read and fetch_command == '(BODY.PEEK[])':
                            mail.store(email_id, '+FLAGS', '\\Seen')

            print(f"Found {len(unread_emails)} matching unread emails.")
            return unread_emails

    except ValueError as ve:
        print(f"Configuration Error: {ve}")
        return []
    except Exception as e:
        print(f"Error getting emails: {e}")
        return []

# --- Example Usage (with credentials from .env) ---
if __name__ == "__main__":
    print("\n--- Peeking Today's Unread Emails (will remain unread) ---")
    # Using sender_email and app_password loaded from .env
    today_unread_peek = get_filtered_unread_emails(sender_email, app_password, filter_by='today', mark_as_read=False)
    for i, mail in enumerate(today_unread_peek):
        print(f"\n--- Email {i+1} ---")
        print(f"From: {mail['From']}")
        print(f"Subject: {mail['Subject']}")
        print(f"Body (first 200 chars): {mail['Body']}...") #[:200]
    print(f"\nTotal emails peeked: {len(today_unread_peek)}")

    print("\n" + "="*50 + "\n")

    # print("--- Reading All Unread Emails (will be marked as read) ---")
    # all_unread_read = get_filtered_unread_emails(sender_email, app_password, filter_by='all', mark_as_read=True)
    # for i, mail in enumerate(all_unread_read):
    #     print(f"\n--- Email {i+1} ---")
    #     print(f"From: {mail['From']}")
    #     print(f"Subject: {mail['Subject']}")
    #     print(f"Body (first 200 chars): {mail['Body'][:200]}...")
    # print(f"\nTotal emails read and marked: {len(all_unread_read)}")

    # print("\n" + "="*50 + "\n")

    # print("--- Peeking Unread Emails from a Specific Date Range (will remain unread) ---")
    # # Example: Unread emails from August 1, 2025 to August 13, 2025 (yesterday)
    # start_of_month = datetime(2025, 8, 1) # August 1, 2025
    # yesterday = datetime(2025, 8, 13) # August 13, 2025
    # range_unread_peek = get_filtered_unread_emails(
    #     sender_email, app_password, filter_by='date_range',
    #     start_date=start_of_month, end_date=yesterday, mark_as_read=False
    # )
    # for i, mail in enumerate(range_unread_peek):
    #     print(f"\n--- Email {i+1} ---")
    #     print(f"From: {mail['From']}")
    #     print(f"Subject: {mail['Subject']}")
    #     print(f"Body (first 200 chars): {mail['Body'][:200]}...")
    # print(f"\nTotal emails peeked: {len(range_unread_peek)}")


    def sending_email(receiver_email = 'recipient@example.com'):
    # --- SMTP (Sending Email) ---
    print("--- Sending Email (SMTP) ---")

     # Recipient's email address
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587 # For TLS

    try:
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = 'Test Email from Python SMTP (using .env)'

        body = "This is a test email sent from Python using Gmail SMTP, with credentials from .env."
        message.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            text = message.as_string()
            server.sendmail(sender_email, receiver_email, text)
        print(f"Email sent successfully to {receiver_email}!")

    except Exception as e:
        print(f"Error sending email: {e}")

    print("-" * 30)