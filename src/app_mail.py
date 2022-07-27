import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

import boto3
import io
import tempfile
from botocore.exceptions import ClientError

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'gwtreasuremap@gmail.com'

class Mail():
    def __init__(self, app_config, read_aws_s3=False, aws_path_credentials='fit/{}'.format('token.pickle')):
        self.client_config = {
            "installed": {
                "client_id":app_config['GOOGLE_CLIENT_ID'],
                "project_id":app_config['GOOGLE_PROJECT_ID'],
                "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                "token_uri":"https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
                "client_secret":app_config['GOOGLE_CLIENT_SECRET'],
                "redirect_uris":["http://localhost"]
                }
            }
        
        self.app_config = app_config
        self.default_sender = app_config['MAIL_DEFAULT_SENDER']
        self.service=None
        self.read_aws_s3_credentials = read_aws_s3
        self.aws_path_credentials = aws_path_credentials

        self.gmail_authenticate()

    def gmail_authenticate(self):
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        
        if self.read_aws_s3_credentials:
            s3 = boto3.client('s3')
            try:
                s3.head_object(Bucket=self.app_config['AWS_BUCKET'], Key=self.aws_path_credentials )
                with io.BytesIO() as token:
                    s3.download_fileobj(self.app_config['AWS_BUCKET'], self.aws_path_credentials, token)
                    token.seek(0)
                    creds = pickle.load(token)
            except:
                pass
        else:
            if os.path.exists("token.pickle"):
                with open("token.pickle", "rb") as token:
                    creds = pickle.load(token)

        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(self.client_config, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # save the credentials for the next run
            if self.read_aws_s3_credentials:
                s3 = boto3.client('s3')
                with io.BytesIO() as f:
                    pickle.dump(creds, f)
                    f.seek(0)
                    s3.upload_fileobj(f, Bucket=self.app_config['AWS_BUCKET'], Key=self.aws_path_credentials )
            else:
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    # Adds the attachment with the given filename to the given message
    def add_attachment(self, message, filename):
        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(filename, 'rb')
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

    def build_message(self, recipients, obj, body_html, attachments=[]):
        if not attachments: # no attachments given
            message = MIMEMultipart('alternative')
            message['to'] = ", ".join(recipients)
            message['from'] = self.default_sender
            message['subject'] = obj
            message.attach(MIMEText(body_html, 'html'))
            #message.attach(MIMEText(body_text, 'plain'))
        else:
            message = MIMEMultipart('alternative')
            message['to'] = ", ".join(recipients)
            message['from'] = self.default_sender
            message['subject'] = obj
            message.attach(MIMEText(body_html, 'html'))
            #message.attach(MIMEText(body_text, 'plain'))
            for filename in attachments:
                self.add_attachment(message, filename)
        return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, recipients, obj, body_html, attachments=[]):
        if self.service:
            return self.service.users().messages().send(
                userId="me",
                body=self.build_message(recipients, obj, body_html, attachments)
            ).execute()

if __name__ == '__main__':

    test_config = {
        'GOOGLE_CLIENT_ID':"--------------",
        'GOOGLE_PROJECT_ID':"-------------",
        'GOOGLE_CLIENT_SECRET':"------------",
        'AWS_BUCKET':"-------------",
        'MAIL_DEFAULT_SENDER':"-----------"
    }
    mail = appmail(test_config, read_aws_s3=True)
    mail.send_message("swyatt@email.arizona.edu", "This is a subject", 
            "app_mail working", '')