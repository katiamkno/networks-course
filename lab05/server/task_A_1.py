import smtplib
from email.mime.text import MIMEText
import sys

SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 587
SENDER_EMAIL = "k.doinikova@mail.ru"
import os

SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_email(recipient, msg_format):
    subject = "Test email from Python"

    if msg_format == "txt":
        body = """Hello!        
        This is a plain text email sent from Python.
        """
        msg = MIMEText(body, "plain", "utf-8")

    elif msg_format == "html":
        html_body = """
        <html>
          <body>
            <h2 style="color:blue;">Hello!</h2>
            <p>This is an <b>HTML email</b> sent from Python.</p>
          </body>
        </html>
        """
        msg = MIMEText(html_body, "html", "utf-8")

    else:
        print("Error: format must be 'txt' or 'html'")
        return

    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        server.quit()

        print(f"Email successfully sent to {recipient} in format: {msg_format}")

    except Exception as e:
        print("Error while sending email:")
        print(e)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python task_A_1.py <recipient_email> <txt|html>")
        sys.exit(1)

    recipient = sys.argv[1]
    format_type = sys.argv[2].lower()

    send_email(recipient, format_type)