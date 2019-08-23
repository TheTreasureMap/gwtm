
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'


configPath = os.environ.get('CONFIGPATH')
if configPath is None:
    configPath = '/var/www/gwtm'

from . import function
config = function.readconfig(configPath, '/config')

app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+config['user']+':'+config['pwd']+'@'+config['host']+':'+str(config['port'])+'/'+config['db']+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

db = SQLAlchemy(app)
mail = Mail(app)

from . import routes
