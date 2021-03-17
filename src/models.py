# -*- coding: utf-8 -*-
import jwt
import flask_sqlalchemy as fsq
import geoalchemy2
import os, json
import datetime
import secrets
import math

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry, Geography
from time import time
from sqlalchemy import func
from flask_login import UserMixin

from src.function import isInt, isFloat
from src import app
from src import login

from . import function
from . import enums

db = SQLAlchemy(app)

def to_json(inst, cls):
    """
    Jsonify the sql alchemy query result.
    """
    convert = dict()
    json_cols = [gw_galaxy_entry.info]
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
        elif c in json_cols:
            d[c.name] = v
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
    instrument_type = db.Column(db.Enum(enums.instrument_type))
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
            geom = function.create_geography(vertices)
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
            geom = function.create_geography(vertices)
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
                        result = function.extract_polygon(poly, scale)
                        if len(result[1]) > 0:
                            for e in result[1]:
                                v.errors.append(e)
                            return [v]
                        else:
                            vertices = result[0]

                        multi_vertices.append(vertices)
                        geom = function.create_geography(vertices)
                        footprint.append(geom)
                    except Exception as e:
                        v.errors.append("Invalid Polygon. If error persists, contact administrator")
                        return [v]

            else:
                result = function.extract_polygon(p, scale)
                if len(result[1]) > 0:
                    for e in result[1]:
                        v.errors.append(e)
                    return [v]
                else:
                    vertices = result[0]

                multi_vertices.append(vertices)
                geom = function.create_geography(vertices)
                footprint.append(geom)

        if len(footprint) == 0:
            v.errors.append('Footprint required')
            return [v]

        self.nickname = nickname
        self.instrument_name = instrument_name
        self.instrument_type = enums.instrument_type.photometric
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
    status = db.Column(db.Enum(enums.pointing_status))
    position = db.Column(Geography('POINT', srid=4326))
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogid = db.Column(db.Integer)
    instrumentid = db.Column(db.Integer)
    depth = db.Column(db.Float)
    depth_err = db.Column(db.Float)
    depth_unit = db.Column(db.Enum(enums.depth_unit))
    time = db.Column(db.Date)
    datecreated = db.Column(db.Date)
    dateupdated = db.Column(db.Date)
    submitterid = db.Column(db.Integer)
    pos_angle = db.Column(db.Float)
    band = db.Column(db.Enum(enums.bandpass))
    doi_url = db.Column(db.String(100))
    doi_id = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)

    @staticmethod
    def pointings_from_IDS(ids, filter=[]):

        filter.append(instrument.id == pointing.instrumentid)
        filter.append(pointing_event.pointingid.in_(ids))
        filter.append(pointing.id.in_(ids))

        pointings = db.session.query(
            pointing.id,
            func.ST_AsText(pointing.position).label('position'),
            pointing.instrumentid,
            pointing.band,
            pointing.pos_angle,
            pointing.depth,
            pointing.depth_err,
            pointing.depth_unit,
            pointing.time,
            pointing.status,
            instrument.instrument_name,
            instrument.instrument_type,
            pointing_event.graceid
        ).filter(*filter).all()

        pointing_returns = {}
        for p in pointings:
            pointing_returns[str(p.id)] = p

        return pointing_returns


    def from_json(self, p, dbinsts, userid, planned_pointings, otherpointings): #dbusers):
        v = valid_mapping()

        PLANNED = False
        if 'id' in p:
            PLANNED = True
            pointingid = p['id']
            planned_pointing = planned_pointings[str(pointingid)]

            if planned_pointing.status == enums.pointing_status.completed or planned_pointing.status == enums.pointing_status.cancelled:
                v.errors.append('This pointing has already been '+planned_pointing.status.name)

            self.position = planned_pointing.position
            self.depth = planned_pointing.depth
            self.depth_err = planned_pointing.depth_err
            self.depth_unit = planned_pointing.depth_unit
            self.status = enums.pointing_status.completed
            self.band = planned_pointing.band
            self.instrumentid = planned_pointing.instrumentid

        if 'status' in p:
            userstatus = p['status']
            validstatusints = [int(b) for b in enums.pointing_status if b.name != 'cancelled']
            validstatusstr = [str(b.name) for b in enums.pointing_status if b.name != 'cancelled']
            if userstatus in validstatusints or userstatus in validstatusstr:
                self.status = userstatus
        elif not PLANNED:
            self.status = enums.pointing_status.completed
        else:
            v.warnings.append("No status given, or unrecognized status. Setting the status to planned")
            self.status = enums.pointing_status.planned

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
        elif self.status == enums.pointing_status.completed and not PLANNED:
            v.errors.append('depth is required for completed observations')

        if 'depth_unit' in p:
            du = p['depth_unit']
            validdepthunit = [int(b) for b in enums.depth_unit]
            validdepthunitstr = [str(b.name) for b in enums.depth_unit]
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
        elif self.status == enums.pointing_status.completed:
            v.errors.append('pos_angle is required for completed observations')

        if 'time' in p:
            try:
                self.time = datetime.datetime.strptime(p['time'], "%Y-%m-%dT%H:%M:%S.%f")
            except:
                v.errors.append("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
        elif self.status == enums.pointing_status.planned:
            v.errors.append("Field \"time\" is required for when the pointing is planned to be observed")
        elif self.status == enums.pointing_status.completed:
            v.errors.append('Field \"time\" is required for the observed pointing')

        self.submitterid = userid
        self.datecreated = datetime.datetime.now()

        if "band" in p and not PLANNED:
            validbandints = [int(b) for b in enums.bandpass]
            validbandstr = [str(b.name) for b in enums.bandpass]
            userband = p['band']
            if userband in validbandints or userband in validbandstr:
                self.band = userband
            else:
                v.errors.append("Field \"band\" is invalid")
        elif not PLANNED:
            v.errors.append("Field \"band\" is required")

        if function.pointing_crossmatch(self, otherpointings):
           v.errors.append("Pointing already submitted")

        v.valid = len(v.errors) == 0
        return v


class pointing_event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pointingid = db.Column(db.Integer)
    graceid = db.Column(db.String)

    @property
    def json(self):
        return to_json(self, self.__class__)


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
    alternateid = db.Column(db.String)
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
    avgra = db.Column(db.Float)
    avgdec = db.Column(db.Float)

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
    
    @property
    def json(self):
        return to_json(self, self.__class__)

    @staticmethod
    def graceidfromalternate(graceid):
        #if there is an input alternate id for this event, it will find the original graceid
        #else it will return the input graceid

        alternateids = db.session.query(gw_alert).filter(
            gw_alert.alternateid == graceid
        ).all()

        if len(alternateids):
            graceid = alternateids[0].graceid
            
        return graceid
    
    @staticmethod
    def alternatefromgraceid(graceid):

        alternateids = db.session.query(gw_alert).filter(
            gw_alert.graceid == graceid
        ).all()
        if len(alternateids):
            if alternateids[0].alternateid is not None:
                graceid = alternateids[0].alternateid
            
        return graceid


class gw_galaxy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graceid = db.Column(db.String)
    galaxy_catalog = db.Column(db.Integer)
    galaxy_catalogID = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)


class gw_galaxy_score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gw_galaxyID = db.Column(db.Integer)
    score_type = db.Column(db.Enum(enums.gw_galaxy_score_type))
    score = db.Column(db.Float)

    @property
    def json(self):
        return to_json(self, self.__class__)


class doi_author_group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    name = db.Column(db.String)

    @property
    def json(self):
        return to_json(self, self.__class__)


class doi_author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    affiliation = db.Column(db.String)
    orcid = db.Column(db.String)
    gnd = db.Column(db.String)
    pos_order = db.Column(db.Integer)
    author_groupid = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)

    @staticmethod
    def construct_creators(doi_group_id, userid):

        if isInt(doi_group_id):
            authors = db.session.query(doi_author).filter(
                doi_author.author_groupid == int(doi_group_id),
                doi_author.author_groupid == doi_author_group.id,
                doi_author_group.userid == userid
            ).order_by(
                doi_author.id
            ).all()
        else:
            authors = db.session.query(doi_author).filter(
                doi_author.author_groupid == doi_author_group.id,
                doi_author_group.name == doi_group_id,
                doi_author_group.userid == userid
            ).order_by(
                doi_author.id
            ).all()

        if len(authors) == 0:
            return False, []

        creators = []
        for a in authors:
            a_dict = { "name":a.name, "affiliation":a.affiliation }
            if a.orcid:
                a_dict['orcid'] = a.orcid
            if a.gnd:
                a_dict['gnd'] = a.gnd
            creators.append(a_dict)

        return True, creators

    @staticmethod
    def authors_from_page(form):
        authors = []
        for aid, an, aff, orc, gnd in zip(
                form.getlist('author_id'),
                form.getlist('author_name'),
                form.getlist('affiliation'),
                form.getlist('orcid'),
                form.getlist('gnd')
            ):

            if  str(aid) == "" or str(aid) == "None":
                authors.append(
                    doi_author(
                        name=an,
                        affiliation=aff,
                        orcid=orc,
                        gnd=gnd
                    )
                )
            else:
                authors.append(
                    doi_author(
                        id=int(aid),
                        name=an,
                        affiliation=aff,
                        orcid=orc,
                        gnd=gnd
                    )
                )
        return authors


class gw_galaxy_list(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graceid = db.Column(db.String)
    groupname = db.Column(db.String)
    submitterid = db.Column(db.Integer)
    reference = db.Column(db.String)
    alertid = db.Column(db.String)
    doi_url = db.Column(db.String(100))
    doi_id = db.Column(db.Integer)

    @property
    def json(self):
        return to_json(self, self.__class__)


class gw_galaxy_entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listid = db.Column(db.Integer)
    name = db.Column(db.String)
    score = db.Column(db.Float)
    position = db.Column(Geography('POINT', srid=4326))
    rank = db.Column(db.Integer)
    info = db.Column(db.JSON)

    @property
    def json(self):
        return to_json(self, self.__class__)

    def from_json(self, p): #dbusers):
        v = valid_mapping()

        if 'position' in p:
            pos = p['position']
            if "POINT" in pos:
                self.position = p['position']
            else:
                v.errors.append("Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type \"POINT(RA DEC)\"")
        else:
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

        if 'score' in p:
            if isFloat(p['score']):
                self.score = p['score']
            else:
                v.errors.append('Invalid score. Must be decimal')
        else:
            v.errors.append("\'score\' is required")

        if 'name' in p:
            self.name = p['name']
        else:
            v.errors.append("\'name\' is required for each galaxy in list")

        if 'rank' in p:
            if isInt(p['rank']):
                self.rank = p['rank']
            else:
                v.errors.append('Invalid rank. Must be Integer')
        else:
            v.errors.append("\'rank\' is required for each galaxy in list")

        if 'info' in p:
            self.info = p['info']
            
        v.valid = len(v.errors) == 0
        return v