"""Rebuild the whole pipeline and save a dated board pack.

Usage:
    python src\run_pipeline.py                 # rebuild + save dated copy
    python src\run_pipeline.py --email         # also email it (needs env vars)

Email needs these environment variables (never hard-code them):
    SMTP_USER, SMTP_APP_PASSWORD, EMAIL_TO
"""
import argparse
import os
import shutil
import smtplib
import subprocess
import sys
from datetime import date
from email.message import EmailMessage
from pathlib import Path

STEPS = ["generate_data", "load_db", "run_queries", "credit_risk", "build_board_pack"]
ARCHIVE = Path("reports/archive")


def run_step(name):
    print(f"--> {name}")
    result = subprocess.run([sys.executable, f"src/{name}.py"])
    if result.returncode != 0:
        sys.exit(f"Step failed: {name}. Is board_pack.xlsx open in Excel?")


def send_email(path):
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_APP_PASSWORD"]
    to = os.environ["EMAIL_TO"]
    msg = EmailMessage()
    msg["Subject"] = f"Board pack - {date.today():%d %b %Y}"
    msg["From"], msg["To"] = user, to
    msg.set_content("Please find the latest financial and risk board pack attached.")
    msg.add_attachment(path.read_bytes(), maintype="application",
                       subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       filename=path.name)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print("Email sent to", to)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", action="store_true", help="email the board pack")
    args = parser.parse_args()

    for step in STEPS:
        run_step(step)

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    dated = ARCHIVE / f"board_pack_{date.today():%Y-%m-%d}.xlsx"
    shutil.copy("reports/board_pack.xlsx", dated)
    print("Saved", dated)

    if args.email:
        send_email(dated)
