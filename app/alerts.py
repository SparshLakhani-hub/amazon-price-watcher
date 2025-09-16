import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings

def send_email(subject: str, body_html: str):
    if not settings.ALERT_EMAIL_TO or not settings.ALERT_EMAIL_FROM:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.ALERT_EMAIL_FROM
    msg["To"] = settings.ALERT_EMAIL_TO
    msg.attach(MIMEText(body_html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.ALERT_EMAIL_SMTP, settings.ALERT_EMAIL_PORT) as server:
        server.starttls(context=ctx)
        server.login(settings.ALERT_EMAIL_USER, settings.ALERT_EMAIL_PASS)
        server.sendmail(settings.ALERT_EMAIL_FROM, [settings.ALERT_EMAIL_TO], msg.as_string())
