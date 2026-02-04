# Looking to send emails in production? Check out our Email API/SMTP product!
import smtplib

sender = "Private Person <from@example.com>"
receiver = "A Test User <to@example.com>"

message = f"""\
Subject: Hi Mailtrap
To: {receiver}
From: {sender}

This is a test e-mail message."""

with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
    server.starttls()
    server.login("b54c2403c11adb", "****88ac")
    server.sendmail(sender, receiver, message)