
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
app = Flask(__name__)

login = LoginManager(app)
login.login_view = 'login'
from . import routes
from . import function

configPath = '/var/www/gwtm'
try:
    configPath = os.environ.get('CONFIGPATH')
except:
    pass

config = function.readconfig(configPath, '/config')
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+config['user']+':'+config['pwd']+'@'+config['host']+':'+str(config['port'])+'/'+config['db']+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
