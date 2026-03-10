from pydantic import BaseModel
from typing import List
import imaplib
import email
import os
from dotenv import load_dotenv


# --- Define your Pydantic model ---
class EmailMessage(BaseModel):
    id: str
    subject: str
    from_: str  # Can't use 'from' since it's a reserved keyword in Python
    body: str
    messageId: str


load_dotenv()

imap_host = os.getenv("IMAP_HOST")
imap_user = os.getenv("IMAP_USER")
imap_pass = os.getenv("IMAP_PASS")

mail = imaplib.IMAP4_SSL(imap_host)
mail.login(imap_user, imap_pass)
mail.select("INBOX")

status, messages = mail.search(None, "UNSEEN")
email_ids = messages[0].split()

print(f"📬 Found {len(email_ids)} unread emails (peeked, not marked as read)")

results: List[EmailMessage] = []

for email_id in email_ids:
    # Use BODY.PEEK[] so the \Seen flag isn't set
    status, msg_data = mail.fetch(email_id, "(BODY.PEEK[])")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            # Extract plain text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if (
                        part.get_content_type() == "text/plain"
                        and not part.get_filename()
                    ):
                        body = part.get_payload(decode=True).decode(errors="replace")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="replace")

            # Add to results list as Pydantic object
            results.append(
                EmailMessage(
                    id=email_id.decode(),
                    subject=msg.get("Subject", ""),
                    from_=msg.get("From", ""),
                    body=body,
                    messageId=msg.get("Message-ID", ""),
                )
            )

mail.logout()

# Print results as JSON
for r in results:
    print(r.model_dump_json(indent=2))
