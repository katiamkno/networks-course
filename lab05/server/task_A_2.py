import socket
import base64
import sys
import ssl

SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 587
SENDER_EMAIL = "k.doinikova@mail.ru"
import os

SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_smtp_command(sock, cmd, expected_code=None):
    sock.send((cmd + "\r\n").encode())
    response = sock.recv(4096).decode()

    if expected_code and not response.startswith(str(expected_code)):
        raise Exception(f"Expected {expected_code}, got: {response}")
    return response


def send_email_via_socket(recipient, subject, body):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((SMTP_SERVER, SMTP_PORT))
        banner = sock.recv(1024).decode()
        print(f"[RECV] {banner.strip()}")

        send_smtp_command(sock, "EHLO client", 250)

        send_smtp_command(sock, "STARTTLS", 220)

        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=SMTP_SERVER)

        send_smtp_command(sock, "EHLO client", 250)

        send_smtp_command(sock, "AUTH LOGIN", 334)

        login_b64 = base64.b64encode(SENDER_EMAIL.encode()).decode()
        send_smtp_command(sock, login_b64, 334)

        password_b64 = base64.b64encode(SENDER_PASSWORD.encode()).decode()
        send_smtp_command(sock, password_b64, 235)

        send_smtp_command(sock, f"MAIL FROM:<{SENDER_EMAIL}>", 250)
        send_smtp_command(sock, f"RCPT TO:<{recipient}>", 250)

        send_smtp_command(sock, "DATA", 354)

        email_content = f"""From: {SENDER_EMAIL}
To: {recipient}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

{body}
"""
        send_smtp_command(sock, email_content + "\r\n.", 250)

        print("Письмо успешно отправлено")

        send_smtp_command(sock, "QUIT", 221)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python task_A_2.py <recipient_email>")
        sys.exit(1)

    recipient = sys.argv[1]

    send_email_via_socket(
        recipient=recipient,
        subject="Test Email from Raw SMTP Socket Client",
        body="Hello!\n\nThis email was sent using raw TCP sockets and SMTP protocol."
    )