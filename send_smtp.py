import csv
import time
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
    FROM_NAME,
    FROM_EMAIL,
    SUBJECT
)

CSV_FILE = "data/contacts.csv"
HTML_TEMPLATE_FILE = "templates/template.html"
TEXT_TEMPLATE_FILE = "templates/template.txt"
LOG_FILE = "logs/sent.log"

# Sicherheits-Delay (50 Mails / Stunde = 72 Sekunden)
SEND_DELAY = 80


def load_template(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def log_result(email: str, status: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {email} | {status}\n")


def already_sent(email: str) -> bool:
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            return email in f.read()
    except FileNotFoundError:
        return False


def send_mail(smtp: smtplib.SMTP_SSL, recipient: str, html_body: str, text_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = recipient

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    smtp.send_message(msg)


def main():
    html_template = load_template(HTML_TEMPLATE_FILE)
    text_template = load_template(TEXT_TEMPLATE_FILE)

    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            if not SMTP_USER or not SMTP_PASS:
                raise ValueError("SMTP_USER and SMTP_PASS must be set in config")
            smtp.login(SMTP_USER, SMTP_PASS)  

            for row in reader:
                email = row["EMAIL"]

                if already_sent(email):
                    print(f"[SKIP] {email} wurde bereits versendet.")
                    continue

                html_body = html_template
                text_body = text_template

                for key, value in row.items():
                    html_body = html_body.replace(f"{{{{{key}}}}}", value)
                    text_body = text_body.replace(f"{{{{{key}}}}}", value)

                try:
                    send_mail(smtp, email, html_body, text_body)
                    log_result(email, "OK")
                    print(f"[OK] Gesendet an {email}")
                except Exception as e:
                    log_result(email, f"ERROR: {e}")
                    print(f"[FEHLER] {email}: {e}")

                time.sleep(SEND_DELAY)


if __name__ == "__main__":
    main()
