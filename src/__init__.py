
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

from . import routes
from . import function

config = function.readconfig('/var/www/gwtm', '/config')
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+config['user']+':'+config['pwd']+'@'+config['host']+':'+str(config['port'])+'/'+config['db']+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
