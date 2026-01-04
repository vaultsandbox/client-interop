"""SMTP helper for sending test emails."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional


def get_smtp_config() -> tuple[str, int]:
    """Get SMTP host and port from environment."""
    host = os.environ.get("SMTP_HOST", "localhost")
    port = int(os.environ.get("SMTP_PORT", "25"))
    return host, port


def send_test_email(
    to_address: str,
    subject: str,
    body: str,
    from_address: str = "test@example.com",
) -> None:
    """
    Send a plain text test email via SMTP.

    Args:
        to_address: Recipient email address
        subject: Email subject line
        body: Plain text email body
        from_address: Sender email address
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    host, port = get_smtp_config()

    with smtplib.SMTP(host, port) as smtp:
        smtp.send_message(msg)


def send_email_with_attachment(
    to_address: str,
    subject: str,
    body: str,
    attachment_name: str,
    attachment_content: bytes,
    attachment_mime_type: str = "application/octet-stream",
    from_address: str = "test@example.com",
) -> None:
    """
    Send an email with an attachment via SMTP.

    Args:
        to_address: Recipient email address
        subject: Email subject line
        body: Plain text email body
        attachment_name: Filename for the attachment
        attachment_content: Raw bytes of the attachment
        attachment_mime_type: MIME type of the attachment
        from_address: Sender email address
    """
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    # Add text body
    msg.attach(MIMEText(body))

    # Add attachment
    maintype, subtype = attachment_mime_type.split("/", 1)
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(attachment_content)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=attachment_name,
    )
    msg.attach(attachment)

    host, port = get_smtp_config()

    with smtplib.SMTP(host, port) as smtp:
        smtp.send_message(msg)


def send_html_email(
    to_address: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    from_address: str = "test@example.com",
) -> None:
    """
    Send an HTML email via SMTP.

    Args:
        to_address: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Optional plain text fallback
        from_address: Sender email address
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    # Add plain text version if provided
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))

    # Add HTML version
    msg.attach(MIMEText(html_body, "html"))

    host, port = get_smtp_config()

    with smtplib.SMTP(host, port) as smtp:
        smtp.send_message(msg)
