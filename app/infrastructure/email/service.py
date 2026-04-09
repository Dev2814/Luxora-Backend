"""
Email Service

Handles sending emails for the application.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

from app.core.config import settings
from app.infrastructure.email.renderer import render_template


def send_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    attachment_path: str | None = None
) -> bool:

    try:

        if not settings.MAIL_SERVER:
            print("Email server not configured")
            return False

        html_content = render_template(template_name, context)

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to_email

        msg.attach(MIMEText(html_content, "html"))

        # ------------------------------------------------
        # ATTACH PDF IF PROVIDED
        # ------------------------------------------------

        if attachment_path and os.path.isfile(attachment_path):

            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())

            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(attachment_path)}"'
            )

            msg.attach(part)

        if settings.MAIL_SSL_TLS:
            server = smtplib.SMTP_SSL(
                settings.MAIL_SERVER,
                settings.MAIL_PORT,
                timeout=10
            )
        else:
            server = smtplib.SMTP(
                settings.MAIL_SERVER,
                settings.MAIL_PORT,
                timeout=10
            )

            if settings.MAIL_STARTTLS:
                server.starttls()

        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        server.sendmail(
            settings.MAIL_FROM,
            to_email,
            msg.as_string()
        )

        server.quit()

        return True

    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False