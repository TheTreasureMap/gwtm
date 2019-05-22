# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
import geoalchemy2
from enum import Enum
from models import db
from __init__ import app
import models
import os,function, json
from geoalchemy2.shape import to_shape

#from osgeo import ogr

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

"""
{
	"instrument_name":"SamScope",
	"instrument_type":"photometric",
	"footprint":"POLYGON((0 0,1 0,1 1, 0 1,0 0))",
	"datecreated":"2019-05-19",
	"submitterid":"1"
}
"""
@app.route("/instruments", methods=["POST"])
def post_instruments():
    rd = request.get_json()

    #validate

    inst = models.instrument(
            instrument_name = rd['instrument_name'],
            instrument_type = rd['instrument_type'],
            footprint = rd['footprint'],
            datecreated = rd['datecreated'],
            submitterid = rd['submitterid']
            )

    db.session.add(inst)
    db.session.flush()
    db.session.commit()

    return inst.json

@app.route("/instruments", methods=["GET"])
def get_instruments():

    args = request.args

    filter=[]
    if "id" in args:
    	#validate
    	_id = args.get('id')
    	filter.append(models.instrument.id == int(_id))
    if "ids" in args:
    	#validate
    	ids = json.loads(args.get('ids'))
    	print(ids)
    	filter.append(models.instrument.id.in_(ids))
    if "type" in args:
    	#validate
    	_type = args.get('ids')
    	filter.append(models.instrument.type == _type)

    insts = db.session.query(models.instrument).filter(*filter).all()
    insts = [x.json for x in insts]

    return jsonify(insts)


app.run()


"""
{
	"instrument_name":"SamScope",
	"instrument_type":"photometric",
	"footprint":"POLYGON((0 0,1 0,1 1, 0 1,0 0))",
	"datecreated":"2019-05-19",
	"submitterid":"1"
}
"""

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
