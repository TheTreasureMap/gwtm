import os

class Config(object):
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    CSRF_ENABLED = True
    DB_USER = os.environ.get('DB_USER', 'treasuremap')
    DB_PWD = os.environ.get('DB_PWD', '')
    DB_NAME = os.environ.get('DB_NAME', 'treasuremap_dev')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_TIMEOUT = 300
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'gwtreasuremap@gmail.com')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'gwtreasuremap@gmail.com')
    ADMINS = os.environ.get('ADMINS', 'gwtreasuremap@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = os.environ.get('MAIL_PORT', '587')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')
    ZENODO_ACCESS_KEY = os.environ.get('ZENODO_ACCESS_KEY', '')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY= os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-2')
    AWS_BUCKET = os.environ.get('AWS_BUCKET', 'gwtreasuremap')
    SECRET_KEY = os.urandom(16)


    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f'postgresql://{self.DB_USER}:{self.DB_PWD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

config = Config()
