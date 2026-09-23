import asyncio
import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from server.config import settings
from server.utils.tokens import RESET_TOKEN_EXPIRY_TEXT

logger = logging.getLogger(__name__)

SMTP_SERVER = settings.MAIL_SERVER
SMTP_PORT = settings.MAIL_PORT
SMTP_USERNAME = settings.MAIL_USERNAME
SMTP_PASSWORD = settings.MAIL_PASSWORD
SENDER_EMAIL = settings.MAIL_DEFAULT_SENDER
BASE_URL = settings.BASE_URL
SMTP_TIMEOUT_SECONDS = 10

RESEND_API_KEY = settings.RESEND_API_KEY
RESEND_FROM = settings.RESEND_FROM


def _send_resend(recipient: str, subject: str, html: str, text: str) -> None:
    """Blocking Resend send. Caller is responsible for offloading to a worker thread."""
    import resend

    resend.api_key = RESEND_API_KEY
    resend.Emails.send(
        {
            "from": RESEND_FROM,
            "to": [recipient],
            "subject": subject,
            "html": html,
            "text": text,
        }
    )


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


async def _send_email(
    recipient: str,
    subject: str,
    title: str,
    username: str,
    paragraph: str,
    button_text: str,
    url: str,
    notes: list[str],
) -> bool:
    """
    Render the shared GWTM email layout and send it.

    Returns True on a successful send or when no transport is configured (dev
    fallback). Propagates transport exceptions on actual send failure so the
    caller can decide how to surface the error.
    """
    # Legacy accounts predate the username character rules, so escape it.
    safe_username = html.escape(username)
    notes_html = "\n".join(f'<p class="info-text">{note}</p>' for note in notes)
    notes_text = "\n\n    ".join(notes)

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
                    <h1 class="title">{title}</h1>
                    <p class="subtitle">Gravitational-Wave Treasure Map</p>
                </div>

                <p>Hi {safe_username},</p>

                <p>{paragraph}</p>

                <div style="text-align: center;">
                    <a href="{url}" class="button" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">{button_text}</a>
                </div>

                {notes_html}

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
    {title}

    Hi {username},

    {paragraph}

    {button_text}:
    {url}

    {notes_text}

    ---
    GWTM Team
    Gravitational-Wave Treasure Map Platform
    """

    logger.info("Sending '%s' email to %s", subject, recipient)

    # Preferred transport: Resend. The SDK is blocking, so run it in a worker
    # thread to avoid stalling the event loop. Exceptions propagate to the caller.
    if RESEND_API_KEY:
        await asyncio.to_thread(
            _send_resend, recipient, subject, html_content, text_content
        )
        return True

    if SMTP_SERVER:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = recipient
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        # smtplib is blocking; run the send in a worker thread so we don't stall
        # the event loop while we wait on the network.
        await asyncio.to_thread(_send_smtp, recipient, message.as_string())
        return True

    # No transport configured.
    if settings.DEVELOPMENT_MODE:
        # Dev fallback only: log the full URL so developers can follow the link manually.
        logger.warning("Email not configured, link for %s: %s", recipient, url)
    else:
        logger.warning(
            "Email not configured, skipping '%s' email to %s", subject, recipient
        )
    return True


async def send_verification_email(
    email: str, username: str, verification_token: str
) -> bool:
    """Send a verification email to a newly registered user."""
    return await _send_email(
        recipient=email,
        subject="Verify your GWTM account",
        title="Welcome to GWTM!",
        username=username,
        paragraph=(
            "Thank you for registering with the Gravitational-Wave Treasure Map. "
            "To complete your registration and start coordinating telescope "
            "observations, please verify your email address."
        ),
        button_text="Verify Email Address",
        url=f"{BASE_URL}/verify-email?token={verification_token}",
        notes=[
            "This verification link will expire in 24 hours for security reasons.",
            "If you didn't create a GWTM account, you can safely ignore this email.",
        ],
    )


async def send_password_reset_email(email: str, username: str, reset_token: str) -> bool:
    """Send a password reset link to an existing user."""
    return await _send_email(
        recipient=email,
        subject="Reset your GWTM password",
        title="Reset your password",
        username=username,
        paragraph=(
            "We received a request to reset the password for your "
            "Gravitational-Wave Treasure Map account. Use the button below to "
            "choose a new one."
        ),
        button_text="Reset Password",
        url=f"{BASE_URL}/reset-password?token={reset_token}",
        notes=[
            f"This link will expire in {RESET_TOKEN_EXPIRY_TEXT} and can only be used once.",
            "If you didn't ask to reset your password, you can safely ignore this "
            "email. Your password will not change.",
        ],
    )
