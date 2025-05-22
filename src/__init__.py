
from flask import Flask
from flask_login import LoginManager
from . import app_mail
from .gwtmconfig import config
from flask_profiler import Profiler

profiler = Profiler()

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'

app.config.from_object(config)

mail = app_mail.AppMail(config)

app.config["DEBUG"] = True

# You need to declare necessary configuration to initialize
# flask-profiler as follows:
app.config["flask_profiler"] = {
    "enabled": app.config["DEBUG"],
    "storage": {
        "engine": "sqlalchemy",
        "db_url": config.SQLALCHEMY_DATABASE_URI
    },
    "basicAuth":{
        "enabled": True,
        "username": config.PROFILER_USERNAME,
        "password": config.PROFILER_PASSWORD
    },
    "endpointRoot": config.PROFILER_ENDPOINT,
    "ignore": [
	    "^/static/.*",
	    "^/ajax_renormalize_skymap.*",
            "^/ajax_coverage_calculator.*"
	]
}
profiler.init_app(app)

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
from . import api_v0
from . import api_v1
