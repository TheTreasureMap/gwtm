# -*- coding: utf-8 -*-
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from time import time
import jwt
import flask_sqlalchemy as fsq
from geoalchemy2 import Geometry, Geography
import geoalchemy2
from enum import Enum,IntEnum
import os, json
import datetime
from flask_login import UserMixin
from src.function import isInt, isFloat
from src import app
from src import login
import secrets
from . import routes
import math

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
        elif "instrument_type" in str(v):
            d[c.name] = v.name
        elif "pointing_status" in str(v):
            d[c.name] = v.name
        elif "bandpass" in str(v):
            d[c.name] = v.name
        elif "depth_unit" in str(v):
            d[c.name] = v.name
        elif "geography" in str(c.type):
            #try:
            d[c.name] = str(geoalchemy2.shape.to_shape(v))
            #except:
            #   d[c.name] = v
        elif isinstance(v, (datetime.date, datetime.datetime)):
            d[c.name] = v.isoformat()
        else:
            d[c.name] = v
    return json.dumps(d)


class depth_unit(IntEnum):
    ab_mag = 1
    vega_mag = 2
    flux_erg = 3
    flux_jy = 4

    def __str__(self):
        split_name = str(self.name).split('_')
        return str.upper(split_name[0]) + ' ' + split_name[1]


class pointing_status(IntEnum):
    planned = 1
    completed = 2
    cancelled = 3


class instrument_type(IntEnum):
    photometric = 1
    spectroscopic = 2


class bandpass(IntEnum):
    U = 1
    B = 2
    V = 3
    R = 4
    I = 5
    J = 6
    H = 7
    K = 8
    u = 9
    g = 10
    r = 11
    i = 12
    z = 13
    UVW1 = 14
    UVW2 = 15
    UVM2 = 16
    XRT = 17
    clear = 18
    open = 19
    UHF = 20
    VHF = 21
    L = 22
    S = 23
    C = 24
    X = 25
    other = 26


class gw_galaxy_score_type(IntEnum):
    default = 1


class valid_mapping():
    def __init__(self):
        self.valid = False
        self.errors = []
        self.warnings = []


@login.user_loader
def load_user(id):
    return users.query.get(int(id))


#API Models

class users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), index=True, unique=True)
    firstname = db.Column(db.String(25))
    lastname = db.Column(db.String(25))
    password_hash = db.Column(db.String(128))
    datecreated = db.Column(db.Date)
    email = db.Column(db.String(100))
    api_token = db.Column(db.String(128))
    verification_key = db.Column(db.String(128))
    verified =  db.Column(db.Boolean)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_apitoken(self):
        self.api_token = secrets.token_urlsafe(28)

    def check_apitoken(self, token):
        return token == self.api_token

    def set_verification_key(self):
        self.verification_key = secrets.token_urlsafe(28)
    
    def check_verification_key(self, verification_key):
        return verification_key == self.verification_key

    def get_reset_password_token(self, expires_in=600):
        print(self.id, app.config['SECRET_KEY'])
        token = jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
        print(token)
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return users.query.get(id)


class usergroups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    groupid  = db.Column(db.Integer)
    role = db.Column(db.String(25))


class groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    datecreated = db.Column(db.Date)


class useractions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
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
    nickname = db.Column(db.String(25))
    instrument_type = db.Column(db.Enum(instrument_type))
    datecreated = db.Column(db.Date)
    #footprint = db.Column(Geography('POLYGON', srid=4326))
    submitterid = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)

    def from_json(self, form, userid, preview=False):
        v = valid_mapping()
        
        nickname = form.instrument_nickname.data
        submitterid = userid
        instrument_name = form.instrument_name.data
        footprint = []
        multi_vertices = []

        u = form.unit.data
        if (u is None or u == "choose") and not preview:
            v.errors.append('Unit is required')
            return [v]

        scale = 1
        if u == "deg":
            scale = 1
        if u == "arcmin":
            scale = 1/60.0
        if u == "arcsec":
            scale = 1/(60.0*60.0)

        if form.footprint_type.data == 'Rectangular':
            h,w = form.height.data, form.width.data
            if h is None or w is None:
                v.errors.append('Height and Width are required for Rectangular shape')
                return [v]
            if not isFloat(h) or not isFloat(w):
                v.errors.append('Height and Width must be decimal')
                return [v]
                
            vertices = []
            half_h = round(0.5*float(h)*scale, 4)
            half_w = round(0.5*float(w)*scale, 4)
            vertices.append([-half_w, half_h])
            vertices.append([half_w, half_h])
            vertices.append([half_w, -half_h])
            vertices.append([-half_w, -half_h])
            vertices.append([-half_w, half_h])

            multi_vertices.append(vertices)
            geom = routes.create_geography(vertices)
            footprint.append(geom)

        if form.footprint_type.data == 'Circular':
            r = form.radius.data

            if r is None:
                v.errors.append('Radius is required for Circular shape')
                return [v]
            if not isFloat(r):
                v.errors.append('Radius must be decimal')
                return [v]

            r = float(r)*float(scale)
            vertices = []
            steps = len(range(0,360, int(360/20)))
            ang = float(360/(steps))

            for a in range(0,steps):
                a = float(a)
                x = r*math.cos(math.radians(90-a*ang))
                y = r*math.sin(math.radians(90-a*ang))
                if abs(x) < 1e-10:
                    x = 0.0
                if abs(y) < 1e-10:
                    y = 0.0
                x = round(x, 4)
                y = round(y, 4)
                vertices.append([x, y])
            vertices.append(vertices[0])

            multi_vertices.append(vertices)
            geom = routes.create_geography(vertices)
            footprint.append(geom)

        if form.footprint_type.data == 'Polygon':
            p = form.polygon.data
            if p is None:
                v.errors.append('Polygon is required for Polygon shape')
                return [v]

            vertices = []

            if "[" in p and "]" in p:
                polygons = p.split("#")
                for poly in polygons:
                    try:
                        poly = poly.split('[')[1].split(']')[0]
                        result = routes.extract_polygon(poly, scale)
                        if len(result[1]) > 0:
                            for e in result[1]:
                                v.errors.append(e)
                            return [v]
                        else:
                            vertices = result[0]

                        multi_vertices.append(vertices)
                        geom = routes.create_geography(vertices)
                        footprint.append(geom)
                    except Exception as e:
                        v.errors.append("Invalid Polygon. If error persists, contact administrator")
                        return [v]

            else:
                result = routes.extract_polygon(p, scale)
                if len(result[1]) > 0:
                    for e in result[1]:
                        v.errors.append(e)
                    return [v]
                else:
                    vertices = result[0]

                multi_vertices.append(vertices)
                geom = routes.create_geography(vertices)
                footprint.append(geom)

        if len(footprint) == 0:
            v.errors.append('Footprint required')
            return [v]

        self.nickname = nickname
        self.instrument_name = instrument_name
        self.instrument_type = instrument_type.photometric
        self.submitterid = submitterid
        self.datecreated = datetime.datetime.now()
        return [v, footprint, multi_vertices]


class footprint_ccd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instrumentid = db.Column(db.Integer)
    footprint = db.Column(Geography('POLYGON', srid=4326))

    @property
    def json(self):
        return to_json(self, self.__class__)

class pointing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(pointing_status))
    position = db.Column(Geography('POINT', srid=4326))
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogid = db.Column(db.Integer)
    instrumentid = db.Column(db.Integer)
    depth = db.Column(db.Float)
    depth_err = db.Column(db.Float)
    depth_unit = db.Column(db.Enum(depth_unit))
    time = db.Column(db.Date)
    datecreated = db.Column(db.Date)
    dateupdated = db.Column(db.Date)
    submitterid = db.Column(db.Integer)
    pos_angle = db.Column(db.Float)
    band = db.Column(db.Enum(bandpass))
    doi_url = db.Column(db.String(100))
    doi_id = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)

    def from_json(self, p, dbinsts, userid, planned_pointings, otherpointings): #dbusers):
        v = valid_mapping()

        PLANNED = False
        if 'id' in p:
            PLANNED = True
            pointingid = p['id']
            planned_pointing = planned_pointings[str(pointingid)]

            if planned_pointing.status == pointing_status.completed or planned_pointing.status == pointing_status.cancelled:
                v.errors.append('This pointing has already been '+planned_pointing.status.name)

            self.position = planned_pointing.position
            self.depth = planned_pointing.depth
            self.depth_err = planned_pointing.depth_err
            self.depth_unit = planned_pointing.depth_unit
            self.status = pointing_status.completed
            self.band = planned_pointing.band
            self.instrumentid = planned_pointing.instrumentid

        if 'status' in p:
            userstatus = p['status']
            validstatusints = [int(b) for b in pointing_status if b.name != 'cancelled']
            validstatusstr = [str(b.name) for b in pointing_status if b.name != 'cancelled']
            if userstatus in validstatusints or userstatus in validstatusstr:
                self.status = userstatus
        elif not PLANNED:
            self.status = pointing_status.completed
        else:
            v.warnings.append("No status given, or unrecognized status. Setting the status to planned")
            self.status = pointing_status.planned

        if 'position' in p and not PLANNED:
            pos = p['position']
            if "POINT" in pos:
                self.position = p['position']
            else:
                v.errors.append("Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type \"POINT(RA, DEC)\"")
        elif not PLANNED:
            if 'ra' in p or 'RA' in p:
                ra = p['ra'] if 'ra' in p else p['RA']
                if not isFloat(ra):
                    ra = None
            else:
                ra = None

            if 'dec' in p or 'DEC' in p:
                dec = p['dec'] if 'dec' in p else p['DEC']
                if not isFloat(dec):
                    dec = None
            else:
                dec = None

            if ra == None or dec == None:
                v.errors.append("Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type \"POINT(RA, DEC)\"")
            else:
                self.position = "POINT("+str(ra)+" "+str(dec)+")"

        #if 'galaxy_catalog' in p:
        #    if isInt(p['galaxy_catalog']):
        #        self.galaxy_catalog = p['galaxy_catalog']

        #if 'galaxy_catalogid' in p:
        #    if isInt(p['galaxy_catalogid']):    
        #        self.galaxy_catalogid = p['galaxy_catalogid']

        if 'instrumentid' in p and not PLANNED:
            inst = p['instrumentid']
            validinst = False
            if isInt(inst):
                insts = [x for x in dbinsts if x.id == int(inst)]
                if len(insts) > 0:
                    self.instrumentid = inst
                    validinst = True
            else:
                insts = [x for x in dbinsts if x.instrument_name == inst]
                inames = [x.instrument_name for x in insts]
                if inst in inames:
                    instmatch = insts[0].id
                    validinst = True
                    self.instrumentid = instmatch

            if validinst is False:
                v.errors.append("Invalid instrumentid. Can be id or name of instrument")
        elif not PLANNED:
            v.errors.append("Field instrumentid is required")

        if 'depth' in p:
            if isFloat(p['depth']):
                self.depth = p['depth']
            else:        
                v.errors.append('Invalid depth. Must b and not PLANNEDe decimal')
        elif self.status == pointing_status.completed and not PLANNED:
            v.errors.append('depth is required for completed observations')

        if 'depth_unit' in p:
            du = p['depth_unit']
            validdepthunit = [int(b) for b in depth_unit]
            validdepthunitstr = [str(b.name) for b in depth_unit]
            if du in validdepthunit or du in validdepthunitstr:
                self.depth_unit = du
            else:
                v.errors.append('Invalid depth_unit. Must be ab_mag, vega_mag, flux_erg, or flux_jy')
        else:
            v.errors.append('depth_unit is required')

        if 'depth_err' in p:
            if isFloat(p['depth_err']):
                self.depth_err = p['depth_err']
            else:
                v.errors.append('Invalid depth_err. Must be decimal')

        if 'pos_angle' in p:
            if isFloat(p['pos_angle']):
                self.pos_angle = p['pos_angle']
            else:        
                v.errors.append('Invalid pos_angle. Must be decimal')
        elif self.status == pointing_status.completed:
            v.errors.append('pos_angle is required for completed observations')

        if 'time' in p:
            try:
                self.time = datetime.datetime.strptime(p['time'], "%Y-%m-%dT%H:%M:%S.%f")
            except:
                v.errors.append("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
        elif self.status == pointing_status.planned:
            v.errors.append("Field \"time\" is required for when the pointing is planned to be observed")
        elif self.status == pointing_status.completed:
            v.errors.append('Field \"time\" is required for the observed pointing')

        self.submitterid = userid
        self.datecreated = datetime.datetime.now()

        if "band" in p and not PLANNED:
            validbandints = [int(b) for b in bandpass]
            validbandstr = [str(b.name) for b in bandpass]
            userband = p['band']
            if userband in validbandints or userband in validbandstr:
                self.band = userband
            else:
                v.errors.append("Field \"band\" is invalid")
        elif not PLANNED:
            v.errors.append("Field \"band\" is required")

        if routes.pointing_crossmatch(self, otherpointings):
           v.errors.append("Pointing already submitted")

        v.valid = len(v.errors) == 0
        return v

class pointing_event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pointingid = db.Column(db.Integer)
    graceid = db.Column(db.String)

class glade_2p3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pgc_number = db.Column(db.Integer)
    position = db.Column(Geography('POINT', srid=4326))
    gwgc_name = db.Column(db.String)
    hyperleda_name = db.Column(db.String)
    _2mass_name = db.Column(db.String)
    sdssdr12_name = db.Column(db.String)
    distance = db.Column(db.Float)
    distance_error = db.Column(db.Float)
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

    @property
    def json(self):
        return to_json(self, self.__class__)

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
    distance_error = db.Column(db.Float)
    prob_bns = db.Column(db.Float)
    prob_nsbh = db.Column(db.Float)
    prob_gap = db.Column(db.Float)
    prob_bbh = db.Column(db.Float)
    prob_terrestrial = db.Column(db.Float)
    prob_hasns = db.Column(db.Float)
    prob_hasremenant = db.Column(db.Float)
    datecreated = db.Column(db.Date)
    group = db.Column(db.String)
    centralfreq = db.Column(db.Float)
    duration = db.Column(db.Float)

    def getClassification(self):

        if self.group == 'Burst':
            return 'None (detected as burst)'

        probs = [
            {'prob':self.prob_bns, 'class':'BNS'},
            {'prob':self.prob_nsbh, 'class':'NSBH'},
            {'prob':self.prob_bbh, 'class':'BBH'},
            {'prob':self.prob_terrestrial, 'class':'Terrestrial'},
            {'prob':self.prob_gap, 'class':'Mass Gap'}
        ]

        sorted_probs = sorted([x for x in probs if x['prob'] > 0.01], key = lambda i: i['prob'], reverse=True)
        
        classification = ''
        for p in sorted_probs:
            classification += p['class'] + ': ('+str(round(100*p['prob'], 1))+'%) '

        return classification


class gw_galaxy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graceid = db.Column(db.String)
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogID = db.Column(db.Integer)


class gw_galaxy_score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gw_galaxyID = db.Column(db.Integer)
    score_type = db.Column(db.Enum(gw_galaxy_score_type))
    score = db.Column(db.Float)


class doi_author_group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    name = db.Column(db.String)


class doi_author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    affiliation = db.Column(db.String)
    orcid = db.Column(db.String)
    gnd = db.Column(db.String)
    pos_order = db.Column(db.Integer)
    author_groupid = db.Column(db.Integer)