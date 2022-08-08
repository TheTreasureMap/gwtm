import emails

class SESMail():
    def __init__(self, app_config, fromaddr=('GWTM Admin (Do Not Reply)', 'gwtreasuremap@gmail.com')):
        self.SMTP_USERNAME = app_config['SMTP_USERNAME']
        self.SMTP_PASSWORD = app_config['SMTP_PASSWORD']
        self.smtp={
            "host": "email-smtp.us-east-2.amazonaws.com", 
            "port": 587, 
            "timeout": 5,
            "user": self.SMTP_USERNAME,
            "password": self.SMTP_PASSWORD,
            "tls": True,
        }
        self.fromaddr=fromaddr

    def send_message(self, recipients, subject, body_html, attachments=[]):
        message = emails.html(
            html=body_html,
            subject=subject,
            mail_from=self.fromaddr,
        )
        
        if attachments:
            for a in attachments:
                message.attach(data=open(a, 'rb'), filename=a)

        r = message.send(
            to=recipients,
            smtp=self.smtp
        )
        
        return r.status_code == 250

if __name__ == '__main__':

    test_config = {
        'SMTP_USERNAME':"-------------",
        'SMTP_PASSWORD':"-------------"
    }
    mail = SESMail(app_config=test_config)
    valid = mail.send_message(["righteousloaf@gmail.com", "swyatt@email.arizona.edu"], "This is a subject", 
            "app_mail working", ['test.xml'])
    assert valid