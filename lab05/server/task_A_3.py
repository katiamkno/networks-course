import socket
import base64
import sys
import ssl
import os

SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 587
SENDER_EMAIL = "k.doinikova@mail.ru"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")


def send_smtp_command(sock, cmd, expected_code=None):
    sock.send((cmd + "\r\n").encode())
    response = sock.recv(4096).decode()

    if expected_code and not response.startswith(str(expected_code)):
        raise Exception(f"Expected {expected_code}, got: {response}")
    return response


def send_email_with_image(recipient, subject, body, image_path):
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

        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()

        if image_path.lower().endswith('.png'):
            content_type = "image/png"
        elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        else:
            content_type = "image/octet-stream"

        filename = os.path.basename(image_path)
        boundary = "NextPart_000_1234"

        email_content = f"""From: {SENDER_EMAIL}
To: {recipient}
Subject: {subject}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{boundary}"

--{boundary}
Content-Type: text/plain; charset="utf-8"

{body}

--{boundary}
Content-Type: {content_type}; name="{filename}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{filename}"

{img_data}
--{boundary}--
"""
        send_smtp_command(sock, email_content + "\r\n.", 250)

        print("Письмо с изображением успешно отправлено")

        send_smtp_command(sock, "QUIT", 221)

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python task_A_3.py <recipient_email> <image_path>")
        sys.exit(1)

    recipient = sys.argv[1]
    image_path = sys.argv[2]

    send_email_with_image(
        recipient=recipient,
        subject="Test Email with Image from Raw SMTP Socket Client",
        body="Hello!",
        image_path=image_path
    )