from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import smtplib

from .gwtmconfig import Config


class AppMail:
    def __init__(self, config: Config) -> None:
        self.sender_email_addr = config.MAIL_DEFAULT_SENDER
        self.login_email_user = config.MAIL_USERNAME
        self.login_email_password = config.MAIL_PASSWORD
        self.smtp_host = config.MAIL_SERVER
        self.smtp_port = int(config.MAIL_PORT)

    def send_message(
        self,
        recipients: List[str],
        subject: str,
        # content_body: Optional[str] = None,
        content_html: Optional[str] = None,
        attachments=[],
    ):
        em = MIMEMultipart("alternative")
        em["From"] = self.sender_email_addr
        em["To"] = ",".join(recipients)
        em["Subject"] = subject

        # if content_body:
        #     em.attach(MIMEText(content_body, "plain"))
        if content_html:
            em.attach(MIMEText(content_html, "html"))
        if attachments:
            # TODO: configure attachments, not sure if we will need this yet
            pass

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            host=self.smtp_host, port=self.smtp_port, context=context
        ) as smtp:
            smtp.login(self.login_email_user, self.login_email_password)
            smtp.sendmail(self.sender_email_addr, recipients, em.as_string())
