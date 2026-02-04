import os
import threading
import time
import logging
import json
from typing import Optional, List

import requests
from imapclient import IMAPClient
import email
from email.header import decode_header, make_header
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# Config
IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

TICKET_API_URL = os.getenv("TICKET_API_URL")
TICKET_POLL_INTERVAL = int(os.getenv("TICKET_POLL_INTERVAL", "30"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# -------------------------
# Helpers
# -------------------------
def decode_mime_words(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def extract_plain_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ct == "text/plain" and "attachment" not in disp:
                try:
                    parts.append(part.get_payload(decode=True).decode(errors="replace"))
                except Exception:
                    pass
        return "\n\n".join(parts).strip()
    else:
        try:
            return msg.get_payload(decode=True).decode(errors="replace")
        except Exception:
            return ""


# -------------------------
# Ticket API integration
# -------------------------
def create_ticket_api(data: dict):
    try:
        r = requests.post(TICKET_API_URL, json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.exception("Failed to create ticket via API: %s", e)
        return None


def list_tickets_api():
    try:
        r = requests.get(TICKET_API_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.exception("Ticket list failed: %s", e)
        return []


# -------------------------
# SMTP: send completion email
# -------------------------
def send_completion_email(to_email: str, ticket_id: str, ticket_title: str):
    subject = f"Ticket #{ticket_id} Completed"
    body = f"Hello,\n\nYour ticket #{ticket_id} ({ticket_title}) has been marked as completed ✅.\n\nThanks!\n"
    msg = MIMEText(body)
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        logging.info("Sent completion email to %s for ticket %s", to_email, ticket_id)
    except Exception:
        logging.exception("Failed to send completion email to %s", to_email)


# -------------------------
# IMAP listener
# -------------------------
class EmailTicketListener:
    def __init__(self):
        self.client = IMAPClient(IMAP_HOST, ssl=True, use_uid=True)

    def start(self):
        self.client.login(IMAP_USER, IMAP_PASS)
        self.client.select_folder("INBOX")
        logging.info("IMAP connected and folder selected. Listening for UNSEEN [TICKET] mails...")

        try:
            while True:
                self.client.idle()
                responses = self.client.idle_check(timeout=60)
                self.client.idle_done()

                if responses:
                    uids = self.client.search(['UNSEEN'])
                    for uid in uids:
                        fetch_data = self.client.fetch(uid, ['BODY.PEEK[]'])
                        raw = fetch_data[uid][b'BODY[]']
                        msg = email.message_from_bytes(raw)
                        subject = decode_mime_words(msg.get("Subject", ""))
                        from_addr = decode_mime_words(msg.get("From", ""))
                        body = extract_plain_text(msg)

                        if "[TICKET]" not in subject.upper():
                            logging.debug("Skipping non-ticket email (leaving unread): %s", subject)
                            continue

                        # Simple title from subject
                        title = subject.replace("[TICKET]", "").strip()

                        ticket_payload = {
                            "title": title,
                            "description": body,
                            "priority": "medium",
                            "reporter_email": from_addr,
                            "source_email_uid": uid,
                        }
                        created = create_ticket_api(ticket_payload)
                        if created:
                            logging.info("Created ticket: %s", created)
                            self.client.add_flags(uid, "\\Seen")
                        else:
                            logging.warning("Ticket creation failed for uid=%s", uid)
                time.sleep(1)

        except KeyboardInterrupt:
            logging.info("Stopping IMAP listener")
        finally:
            try:
                self.client.logout()
            except Exception:
                pass


# -------------------------
# Ticket watcher
# -------------------------
class TicketWatcher:
    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self.last_seen = {}

    def start(self):
        logging.info("Ticket watcher started with poll interval %s s", self.poll_interval)
        while True:
            try:
                tickets = list_tickets_api()
                for t in tickets:
                    tid = str(t.get("id"))
                    status = (t.get("status") or "").upper()
                    prev = self.last_seen.get(tid)
                    if prev is None:
                        self.last_seen[tid] = status
                        continue

                    if prev != status:
                        logging.info("Ticket %s changed: %s -> %s", tid, prev, status)
                        self.last_seen[tid] = status
                        if status in ("DONE", "COMPLETED"):
                            reporter = t.get("reporter_email")
                            title = t.get("title", "")
                            if reporter:
                                send_completion_email(reporter, tid, title)
            except Exception:
                logging.exception("Ticket watcher error")
            time.sleep(self.poll_interval)


# -------------------------
# Entrypoint
# -------------------------
def main():
    listener = EmailTicketListener()
    watcher = TicketWatcher(poll_interval=TICKET_POLL_INTERVAL)

    t1 = threading.Thread(target=listener.start, daemon=True)
    t2 = threading.Thread(target=watcher.start, daemon=True)

    t1.start()
    t2.start()

    logging.info("Service started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")


if __name__ == "__main__":
    main()
