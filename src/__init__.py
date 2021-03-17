
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'

configPath = os.environ.get('CONFIGPATH')
if configPath is None:
    configPath = '/var/www/gwtm'

from . import gwtmconfig
gcfig = gwtmconfig.Config(configPath, '/config')
config = gcfig.run()

app.config["DEBUG"] = bool(config['DEBUG'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+config['user']+':'+config['pwd']+'@'+config['host']+':'+str(config['port'])+'/'+config['db']+'?sslmode=verify-full&sslrootcert='+configPath+'/rds-ca-2019-root.pem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 300
app.config['CSRF_ENABLED'] = True

#Mail Settings
#Load from config later
app.config['MAIL_USERNAME'] = config['MAIL_USERNAME']
app.config['MAIL_DEFAULT_SENDER'] = config['MAIL_DEFAULT_SENDER']
app.config['ADMINS'] = [config['ADMINS']]
app.config['MAIL_PASSWORD'] = config['MAIL_PASSWORD']
app.config['MAIL_SERVER'] = config['MAIL_SERVER']
app.config['MAIL_PORT'] = int(config['MAIL_PORT']) 
app.config['MAIL_USE_TLS'] = bool(config['MAIL_USE_TLS'])

#RECAPTCHA
app.config['RECAPTCHA_PUBLIC_KEY'] = config['RECAPTCHA_PUBLIC_KEY']
app.config['RECAPTCHA_PRIVATE_KEY'] = config['RECAPTCHA_PRIVATE_KEY']
app.config['ZENODO_ACCESS_KEY'] = config['ZENODO_ACCESS_KEY']

mail = Mail(app)

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='GWTM Error',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    try:
        if not os.path.exists('/var/www/gwtm/logs'):
            os.mkdir('/var/www/gwtm/logs',mode=0o777)
        file_handler = RotatingFileHandler('/var/www/gwtm/logs/gwtm.log', maxBytes=10240,backupCount=10)
        file_handler.setFormatter(logging.Formatter( '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Gravitational Wave Treasure Map')
    except:
        print('Permissions have been reset. Type: sudo chmod a+rw /var/www/gwtm/logs/gwtm.log')

from . import routes
from . import ajaxrequests
from . import api