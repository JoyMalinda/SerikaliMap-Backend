from flask_mail import Message
from flask_mail import Mail

mail = Mail()

def send_contact_email(user_email, message_content):
    msg = Message(
        subject="New Form Submission",
        sender=user_email,
        recipients=["serikalimap@proton.me"],
        body=message_content
    )
    mail.send(msg)

def is_spam(message, honeypot):
    if honeypot:
        return True

    if len(message.strip()) < 10:
        return True

    if "http://" in message or "https://" in message:
        return True

    return False

