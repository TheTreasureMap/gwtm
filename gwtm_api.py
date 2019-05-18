from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from enum import Enum
import os,function


app = Flask(__name__)
cwd = os.getcwd()

config = function.readconfig(cwd, '/config')

app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+config['mysqluser']+':'+config['mysqlpwd']+'@localhost/'+config['mysqldb']+''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#API Models

class pointing_status(Enum):
    planned = 1
    completed = 2
    cancelled = 3

class instrument_type(Enum):
    photometric = 1
    spectroscopic = 2

class Users(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True)
    firstname = db.Column(db.String(25))
    lastname = db.Column(db.String(25))
    datecreated = db.Column(db.Date)

class UserGroups(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer)
    groupID = db.Column(db.Integer)
    role = db.Column(db.String(25))

class Groups(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    datecreated = db.Column(db.Date)

class UserActyions(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    modified_table = db.Column(db.String(25))
    modified_id = db.Column(db.Integer)
    modified_column = db.Column(db.String(25))
    prev_value = db.Column(db.String)
    new_value = db.Column(db.String)
    type = db.Column(db.String(25))
    time = db.Column(db.Date)

class Instrument(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    instrument_name = db.Column(db.String(25))
    instrument_type = db.Column(db.Enum(instrument_type))
    footprint = db.Column(Geometry('GEOMETRY'))
    datecreated = db.Column(db.Date)
    submitterID = db.Column(db.Integer)

class Pointing(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(pointing_status))
    position = db.Column(Geometry('POINT'))
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogID = db.Column(db.Integer)
    instrumentID = db.Column(db.Integer)
    depth = db.Column(db.Float)
    time = db.Column(db.Date)
    datecreated = db.Column(db.Date)
    submitterID = db.Column(db.Integer)

class Pointing_Event(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    pointingID = db.Column(db.Integer)
    GraceID = db.Column(db.String)

class Glade_2p3(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    position = db.Column(Geometry('POINT'))
    gwgc_name = db.Column(db.String)
    hyperleda_name = db.Column(db.String)
    _2mass_name = db.Column(db.String)
    distance = db.Column(db.Float)
    distance_err = db.Column(db.Float)
    redshift = db.Column(db.Float)
    bmag = db.Column(db.Float)
    bmag_err = db.Column(db.Float)
    bmag_abs = db.Column(db.Float)
    jmag = db.Column(db.Float)
    jmag_err = db.Column(db.Float)
    hmag = db.Column(db.Float)
    hmag_err = db.Column(db.Float)
    kmag = db.Column(db.Float)
    kmag_err = db.Column(db.Float)
    flag1 = db.Column(db.String(1))
    flag2 = db.Column(db.Integer)
    flag3 = db.Column(db.Integer)

class GW_Alert(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    GraceID = db.Column(db.String)
    role = db.Column(db.String)
    timesent = db.Column(db.Date)
    time_of_signal = db.Column(db.Date)
    packet_type = db.Column(db.Integer)
    alert_type = db.Column(db.String)
    detectors = db.Column(db.String)
    description = db.Column(db.String)
    far = db.Column(db.Float)
    skymap_fits_url = db.Column(db.String)
    distance = db.Column(db.Float)
    distance_err = db.Column(db.Float)
    prob_bns = db.Column(db.Float)
    prob_nsbh = db.Column(db.Float)
    prob_gap = db.Column(db.Float)
    prob_bbh = db.Column(db.Float)
    prob_terrestrial = db.Column(db.Float)
    prob_hasns = db.Column(db.Float)
    prob_hasremenant = db.Column(db.Float)
    datecreated = db.Column(db.Date)

#API Endpoints


#Post Pointing/s
#Parameters: List of Pointing JSON objects
#Returns: List of assigned IDs
#Comments: Check if instrument configuration already exists to avoid duplication. Check if pointing is centered at a galaxy in one of the catalogs and if so, associate it.

@app.route("/pointings", methods=["POST"])
def add_pointings():
    return jsonify([])
    #username = request.json['username']
    #email = request.json['email']

    #new_user = User(username, email)

    #db.session.add(new_user)
    #db.session.commit()

    #return jsonify(new_user)



#Get Pointing/s
#Parameters: List of ID/s, type/s, group/s, user/s, and/or time/s constraints (to be AND’ed). 
#Returns: List of PlannedPointing JSON objects

@app.route("/pointings", methods=["GET"])
def get_pointings():
    return jsonify([])


#Cancel PlannedPointing
#Parameters: List of IDs of planned pointings for which it is known that they aren’t going to happen

@app.route("/pointings", methods=["DELETE"])
def del_pointings():
    return jsonify([])



#Get Instrument/s
#Parameters: List of ID/s, type/s (to be AND’ed).
#Returns: List of Instrument JSON objects

@app.route("/instruments", methods=["POST"])
def post_instruments():
    rd = request.get_json()
    inst = Instrument(
            instrument_name = rd['instrument_name'],
            instrument_type = rd['instrument_type'],
            footprint = rd['footprint'],
            datecreated = rd['datecreated'],
            submitterID = rd['submitterID']
            )

    db.session.add(inst)
    db.session.commit()

    
    return jsonify(inst)

@app.route("/instruments", methods=["GET"])
def get_instruments():
    print(request.args.get('insts'))
    return jsonify(['GET Instrument'])


app.run()
#Post Candidate/s
#Parameters: List of Candidate JSON objects
#Returns: List of assigned IDs
#Notes: Check if a candidate already exists at these coordinates (with a 2” tolerance) and if so, just add the name to the names table (if new).

#Get Candidate/s
#Parameters: List of ID/s, name/s, group/s, user/s, time/s, RA, Dec (to be AND’ed).
#Returns: List of Candidate JSON objects

#Post Photometry
#Parameters: List of Photometry JSON objects
#Returns: List of assigned IDs

#Get Photometry
#Parameters: List of candidate ID/s, time/s, magnitude/s, filter/s (to be AND’ed).
#Returns: List of Photometry JSON objects

#Post Spectroscopy
#Parameters: List of Spectroscopy JSON objects
#Returns: List of assigned IDs

#Get Spectroscopy
#Parameters: List of candidate ID/s, time/s (to be AND’ed).
#Returns: List of Spectroscopy JSON objects
