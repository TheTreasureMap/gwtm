import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from server.config import settings

# Email configuration from central settings
EMAIL_TOKEN_EXPIRE_HOURS = 24
EMAIL_SECRET_KEY = settings.JWT_SECRET_KEY
EMAIL_ALGORITHM = settings.JWT_ALGORITHM
SMTP_SERVER = settings.MAIL_SERVER
SMTP_PORT = settings.MAIL_PORT
SMTP_USERNAME = settings.MAIL_USERNAME
SMTP_PASSWORD = settings.MAIL_PASSWORD
SENDER_EMAIL = settings.MAIL_DEFAULT_SENDER
BASE_URL = "http://localhost:8000"  # This should be configured in settings as well


def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with optional expiration
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, EMAIL_SECRET_KEY, algorithm=EMAIL_ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify a JWT token and return the payload
    """
    try:
        payload = jwt.decode(token, EMAIL_SECRET_KEY, algorithms=[EMAIL_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


def send_account_validation_email(user, db: Session) -> None:
    """
    Send an account validation email to a user
    """
    # Generate token
    token = create_token(
        data={"sub": user.email, "id": user.id},
        expires_delta=timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
    )

    # Create verification URL
    verification_url = f"{BASE_URL}/verify-account?token={token}"

    # Email subject and content
    subject = "Verify your GWTM account"

    # Email content - HTML
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ padding: 20px; }}
            .button {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to GWTM!</h1>
            <p>Thank you for registering with the Gravitational-Wave Treasure Map.</p>
            <p>Please click the button below to verify your account:</p>
            <a href="{verification_url}" class="button">Verify Account</a>
            <p>This link will expire in {EMAIL_TOKEN_EXPIRE_HOURS} hours.</p>
            <p>If you did not register for a GWTM account, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    # Email content - Plain text
    text_content = f"""
    Welcome to GWTM!
    
    Thank you for registering with the Gravitational-Wave Treasure Map.
    
    Please click the link below to verify your account:
    {verification_url}
    
    This link will expire in {EMAIL_TOKEN_EXPIRE_HOURS} hours.
    
    If you did not register for a GWTM account, please ignore this email.
    """

    # In a development environment, we might just log the verification URL
    print(f"Verification URL for {user.email}: {verification_url}")

    # In a production environment, we would send the actual email
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = user.email

        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Connect to server and send
        # In a real environment, use a proper production setup
        # This is commented out to avoid actual email sending
        """
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, user.email, message.as_string())
        """

        # For development, we could save the email to a file
        # email_path = Path(f"./emails/{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
        # email_path.parent.mkdir(exist_ok=True)
        # email_path.write_text(html_content)

        # Update the user's token
        user.token = token
        db.commit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(user, db: Session) -> None:
    """
    Send a password reset email to a user
    """
    # Generate token
    token = create_token(
        data={"sub": user.email, "id": user.id, "type": "password_reset"},
        expires_delta=timedelta(hours=1),  # Shorter expiry for password resets
    )

    # Create reset URL
    reset_url = f"{BASE_URL}/reset-password?token={token}"

    # Email subject and content
    subject = "Reset your GWTM password"

    # Email content - HTML
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ padding: 20px; }}
            .button {{ 
                background-color: #4CAF50; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Password Reset Request</h1>
            <p>We received a request to reset your GWTM password.</p>
            <p>Please click the button below to reset your password:</p>
            <a href="{reset_url}" class="button">Reset Password</a>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    # Email content - Plain text
    text_content = f"""
    Password Reset Request
    
    We received a request to reset your GWTM password.
    
    Please click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you did not request a password reset, please ignore this email.
    """

    # In a development environment, we might just log the reset URL
    print(f"Password reset URL for {user.email}: {reset_url}")

    # Store the token in the user record
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
