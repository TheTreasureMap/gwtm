# -*- coding: utf-8 -*-

import os
from flask import Flask
import function


cwd = os.getcwd()
config = function.readconfig(cwd, '/config')

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+config['user']+':'+config['pwd']+'@localhost/'+config['db']+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
