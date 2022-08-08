
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from werkzeug.utils import import_string
from . import app_mail

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'

configModule = os.environ.get('CONFIGMODULE', 'src.gwtmconfig.Config')
cfg = import_string(configModule)()
app.config.from_object(cfg)

#mail = Mail(app)
mail = app_mail.SESMail(app.config)
cache = Cache(app)


#if not app.debug:
#    if app.config['MAIL_SERVER']:
#        auth = None
#        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
#            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
#        secure = None
#        if app.config['MAIL_USE_TLS']:
#            secure = ()
#        mail_handler = SMTPHandler(
#            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
#            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
#            toaddrs=app.config['ADMINS'], subject='GWTM Error',
#            credentials=auth, secure=secure)
#        mail_handler.setLevel(logging.ERROR)
#        app.logger.addHandler(mail_handler)

    #try:
    #    if not os.path.exists('/var/www/gwtm/logs'):
    #        os.mkdir('/var/www/gwtm/logs',mode=0o777)
    #    file_handler = RotatingFileHandler('/var/www/gwtm/logs/gwtm.log', maxBytes=10240,backupCount=10)
    #    file_handler.setFormatter(logging.Formatter( '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    #    file_handler.setLevel(logging.INFO)
    #    app.logger.addHandler(file_handler)

    #    app.logger.setLevel(logging.INFO)
    #    app.logger.info('Gravitational Wave Treasure Map')
    #except:
    #    print('Permissions have been reset. Type: sudo chmod a+rw /var/www/gwtm/logs/gwtm.log')

from . import routes
from . import ajaxrequests
from . import api
