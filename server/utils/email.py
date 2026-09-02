import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from server.config import settings

logger = logging.getLogger(__name__)

SMTP_SERVER = settings.MAIL_SERVER
SMTP_PORT = settings.MAIL_PORT
SMTP_USERNAME = settings.MAIL_USERNAME
SMTP_PASSWORD = settings.MAIL_PASSWORD
SENDER_EMAIL = settings.MAIL_DEFAULT_SENDER
BASE_URL = settings.BASE_URL
SMTP_TIMEOUT_SECONDS = 10


def _send_smtp(recipient: str, message_str: str) -> None:
    """Blocking SMTP send. Caller is responsible for offloading to a worker thread."""
    if settings.MAIL_USE_SSL:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, message_str)
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            if settings.MAIL_USE_TLS:
                server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, message_str)


async def send_verification_email(
    email: str, username: str, verification_token: str
) -> bool:
    """
    Send a verification email to a newly registered user.

    Returns True on a successful send or when SMTP is not configured (dev fallback).
    Propagates smtplib / socket exceptions on actual send failure so the caller
    can decide how to surface the error.
    """
    verification_url = f"{BASE_URL}/verify-email?token={verification_token}"

    subject = "Verify your GWTM account"

    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #f8fafc;
            }}
            .email-card {{
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .title {{
                color: #1a202c;
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 10px 0;
            }}
            .subtitle {{
                color: #4a5568;
                font-size: 16px;
                margin: 0;
            }}
            .button {{
                display: inline-block;
                background-color: #3182ce;
                color: white;
                padding: 14px 28px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                font-size: 16px;
                margin: 24px 0;
                transition: background-color 0.2s;
            }}
            .button:hover {{
                background-color: #2c5aa0;
            }}
            .info-text {{
                color: #4a5568;
                font-size: 14px;
                margin: 20px 0 0 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                color: #718096;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="email-card">
                <div class="header">
                    <h1 class="title">Welcome to GWTM!</h1>
                    <p class="subtitle">Gravitational-Wave Treasure Map</p>
                </div>

                <p>Hi {username},</p>

                <p>Thank you for registering with the Gravitational-Wave Treasure Map. To complete your registration and start coordinating telescope observations, please verify your email address.</p>

                <div style="text-align: center;">
                    <a href="{verification_url}" class="button" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">Verify Email Address</a>
                </div>

                <p class="info-text">This verification link will expire in 24 hours for security reasons.</p>

                <p class="info-text">If you didn't create a GWTM account, you can safely ignore this email.</p>

                <div class="footer">
                    <p>GWTM Team<br>
                    Gravitational-Wave Treasure Map Platform</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to GWTM!

    Hi {username},

    Thank you for registering with the Gravitational-Wave Treasure Map. To complete your registration and start coordinating telescope observations, please verify your email address.

    Please click the link below to verify your account:
    {verification_url}

    This verification link will expire in 24 hours for security reasons.

    If you didn't create a GWTM account, you can safely ignore this email.

    ---
    GWTM Team
    Gravitational-Wave Treasure Map Platform
    """

    logger.info("Sending verification email to %s", email)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL
    message["To"] = email
    message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

    if not SMTP_SERVER:
        if settings.DEVELOPMENT_MODE:
            # Dev fallback only: log the full URL so developers can verify manually.
            logger.warning(
                "SMTP not configured — verification URL for %s: %s", email, verification_url
            )
        else:
            logger.warning("SMTP not configured — skipping verification email to %s", email)
        return True

    # smtplib is blocking; run the send in a worker thread so we don't stall
    # the event loop while we wait on the network.
    await asyncio.to_thread(_send_smtp, email, message.as_string())

    return True
