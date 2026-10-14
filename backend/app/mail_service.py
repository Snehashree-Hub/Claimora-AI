import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# SEND CLAIM EMAIL
# ============================================================

def send_claim_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_paths: list[str] | None = None,
):

    # --------------------------------------------------------
    # SMTP CONFIGURATION
    # --------------------------------------------------------

    smtp_host = os.getenv("SMTP_HOST")

    smtp_port = int(
        os.getenv("SMTP_PORT", "587")
    )

    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    smtp_from = (
        os.getenv("SMTP_FROM")
        or smtp_username
    )

    smtp_use_tls = (
        os.getenv(
            "SMTP_USE_TLS",
            "true"
        ).lower()
        == "true"
    )


    # --------------------------------------------------------
    # VALIDATE SMTP SETTINGS
    # --------------------------------------------------------

    if not smtp_host:
        raise ValueError(
            "SMTP_HOST is not configured in .env"
        )

    if not smtp_username:
        raise ValueError(
            "SMTP_USERNAME is not configured in .env"
        )

    if not smtp_password:
        raise ValueError(
            "SMTP_PASSWORD is not configured in .env"
        )

    if not smtp_from:
        raise ValueError(
            "SMTP_FROM is not configured in .env"
        )


    # --------------------------------------------------------
    # CREATE EMAIL
    # --------------------------------------------------------

    message = EmailMessage()

    message["From"] = smtp_from

    message["To"] = recipient_email

    message["Subject"] = subject

    message.set_content(body)


    # --------------------------------------------------------
    # ADD ATTACHMENTS
    # --------------------------------------------------------

    if attachment_paths:

        for file_path in attachment_paths:

            if not file_path:
                continue

            if not os.path.exists(file_path):
                continue

            try:

                with open(
                    file_path,
                    "rb"
                ) as file:

                    file_data = file.read()

                file_name = os.path.basename(
                    file_path
                )

                message.add_attachment(
                    file_data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=file_name,
                )

            except Exception as error:

                raise ValueError(
                    f"Unable to attach file "
                    f"{file_path}: {error}"
                )


    # --------------------------------------------------------
    # CONNECT TO SMTP SERVER
    # --------------------------------------------------------

    if smtp_use_tls:

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=30
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                smtp_username,
                smtp_password
            )

            server.send_message(
                message
            )

    else:

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=30
        ) as server:

            server.ehlo()

            server.login(
                smtp_username,
                smtp_password
            )

            server.send_message(
                message
            )


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return True