import smtplib
from email.mime.text import MIMEText
from flask import current_app

# Utility function to send email
def send_email(to_email, subject, body):
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_user = current_app.config.get('SMTP_USER')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    from_email = smtp_user
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False