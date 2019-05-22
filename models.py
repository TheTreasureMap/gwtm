# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry, Geography
import geoalchemy2
from enum import Enum,IntEnum
from __init__ import app
import os,function, json, geojson
import datetime

db = SQLAlchemy(app)

def to_json(inst, cls):
    """
    Jsonify the sql alchemy query result.
    """
    convert = dict()
    # add your coversions for things like datetime's 
    # and what-not that aren't serializable.
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        elif "geography" in str(c.type):
            d[c.name] = str(geoalchemy2.shape.to_shape(v))
        elif isinstance(v, (datetime.date, datetime.datetime)):
            d[c.name] = v.isoformat()
        else:
            d[c.name] = v
    return json.dumps(d)

class pointing_status(IntEnum):
    planned = 1
    completed = 2
    cancelled = 3

class instrument_type(IntEnum):
    photometric = 1
    spectroscopic = 2

#API Models

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True)
    firstname = db.Column(db.String(25))
    lastname = db.Column(db.String(25))
    datecreated = db.Column(db.Date)

class userGroups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer)
    groupID = db.Column(db.Integer)
    role = db.Column(db.String(25))

class groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    datecreated = db.Column(db.Date)

class useractions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modified_table = db.Column(db.String(25))
    modified_id = db.Column(db.Integer)
    modified_column = db.Column(db.String(25))
    prev_value = db.Column(db.String)
    new_value = db.Column(db.String)
    type = db.Column(db.String(25))
    time = db.Column(db.Date)

class instrument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instrument_name = db.Column(db.String(25))
    instrument_type = db.Column(db.Enum(instrument_type))
    footprint = db.Column(Geography('POLYGON', srid=4326))
    datecreated = db.Column(db.Date)
    submitterid = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)

class pointing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(pointing_status))
    position = db.Column(Geography('POINT', srid=4326))
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogid = db.Column(db.Integer)
    instrumentID = db.Column(db.Integer)
    depth = db.Column(db.Float)
    time = db.Column(db.Date)
    datecreated = db.Column(db.Date)
    submitterID = db.Column(db.Integer)

class pointing_event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pointingID = db.Column(db.Integer)
    graceid = db.Column(db.String)

class glade_2p3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(Geography('POINT', srid=4326))
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

class gw_alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graceid = db.Column(db.String)
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
