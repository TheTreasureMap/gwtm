# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, redirect, flash, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Message
from werkzeug.urls import url_parse
from sqlalchemy import func
from geoalchemy2 import Geometry
from enum import Enum
import geoalchemy2
import flask_sqlalchemy as fsq
import os, json, datetime
import random, math
import pandas as pd

from . import function
from . import models
from . import forms

from src import app
from src import mail

import plotly
import plotly.graph_objs as go
from plotly.tools import FigureFactory as FF

db = models.db
global colors
colors = [
	"#000000", "#FFFF00", "#1CE6FF", "#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059",
	"#FFDBE5", "#7A4900", "#0000A6", "#63FFAC", "#B79762", "#004D43", "#8FB0FF", "#997D87",
	"#5A0007", "#809693", "#FEFFE6", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", "#FF2F80",
	"#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
	"#DDEFFF", "#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F",
	"#372101", "#FFB500", "#C2FFED", "#A079BF", "#CC0744", "#C0B9B2", "#C2FF99", "#001E09",
	"#00489C", "#6F0062", "#0CBD66", "#EEC3FF", "#456D75", "#B77B68", "#7A87A1", "#788D66",
	"#885578", "#FAD09F", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
	"#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81",
	"#575329", "#00FECF", "#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00",
	"#7900D7", "#A77500", "#6367A9", "#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700",
	"#549E79", "#FFF69F", "#201625", "#72418F", "#BC23FF", "#99ADC0", "#3A2465", "#922329",
	"#5B4534", "#FDE8DC", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
	"#83AB58", "#001C1E", "#D1F7CE", "#004B28", "#C8D0F6", "#A3A489", "#806C66", "#222800",
	"#BF5650", "#E83000", "#66796D", "#DA007C", "#FF1A59", "#8ADBB4", "#1E0200", "#5B4E51",
	"#C895C5", "#320033", "#FF6832", "#66E1D3", "#CFCDAC", "#D0AC94", "#7ED379", "#012C58"
	]
#WEBSITE ROUTES
@app.route("/index", methods=["GET"])
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


class overlay():
	def __init__(self, name, color, contours):
		self.name = name
		self.color = color
		self.contours = contours

@app.route("/alerts", methods=['GET', 'POST'])
@login_required
def alerts():
	form = forms.AlertsForm()
	form.populate_graceids()
	if request.method == 'POST':
		
		graceid = form.graceids.data
		
		#filter and query for the relevant pointings
		pointing_info = db.session.query(
			models.pointing.instrumentid,
			models.pointing.pos_angle,
			func.ST_AsText(models.pointing.position).label('position'),
		).filter(
			models.pointing_event.graceid == graceid,
			models.pointing_event.pointingid == models.pointing.id
		).all()

		#grab the pointings instrument ids
		instrumentids = [x.instrumentid for x in pointing_info]

		#filter and query for the relevant instruments
		instrumentinfo = db.session.query(
			models.instrument.instrument_name,
			models.instrument.id
		).filter(
			models.instrument.id.in_(instrumentids)
		).all()

		#filter and query the relevant instrument footprints
		footprintinfo = db.session.query(
			func.ST_AsText(models.footprint_ccd.footprint).label('footprint'), 
			models.footprint_ccd.instrumentid
		).filter(
			models.footprint_ccd.instrumentid.in_(instrumentids)
		).all()
		
		overlays = []

		#grab the precomputed localization contour region
		contourpath = '/var/www/gwtm/src/static/'+graceid+'-contours-smooth.json'
		print(contourpath)
		#contourpath = os.getcwd()+'/viz-example/contours-smooth.json'

		#if it exists, add it to the overlay list
		if os.path.exists(contourpath):
			contours_data=pd.read_json(contourpath)
			contour_geometry = []
			for contour in contours_data['features']:
				contour_geometry.extend(contour['geometry']['coordinates'])

			overlays.append({
				"name":"GW Contour",
				"color": '#e6194B',
				"contours":function.polygons2footprints(contour_geometry)
			})
		
		#iterate over each instrument and grab their pointings
		#rotate and project the footprint and then add it to the overlay list
		for inst in instrumentinfo:
			name = inst.instrument_name
			color = colors[inst.id]
			footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == inst.id]
			sanatized_ccds = function.sanatize_footprint_ccds(footprint_ccds)
			inst_pointings = [x for x in pointing_info if x.instrumentid == inst.id]
			pointing_geometries = []

			for p in inst_pointings:
				ra, dec = function.sanatize_pointing(p.position)
				for ccd in sanatized_ccds:
					rotated = function.rotate(ccd, p.pos_angle)
					pointing_footprint = function.project(rotated, ra, dec)
					pointing_geometries.append({"polygon":pointing_footprint})

			overlays.append({
				"name":name,
				"color":color,
				"contours":pointing_geometries
			})

		return render_template("alerts.html", form=form, viz=True, graceid=graceid, overlays=overlays)

	return render_template("alerts.html", form=form)


@app.route("/contact", methods=['GET'])
def contact():
    return render_template("contact.html")


@app.route("/about", methods=['GET'])
def about():
    return render_template('about.html')


@app.route("/documentation", methods=['GET'])
def documentation():
	return render_template('documentation.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect('/index')
	form = forms.RegistrationForm()
	if form.validate_on_submit():
		user = models.users(
			username=form.username.data, 
			email=form.email.data,
			firstname=form.firstname.data,
			lastname=form.lastname.data,
			datecreated=datetime.datetime.now(),
			verified = False
			)
		user.set_password(form.password.data)
		user.set_verification_key()
		db.session.add(user)
		db.session.flush()
		db.session.commit()
		send_account_validation_email(user)
		flash("An email has been sent to "+user.email+". Please follow further instructions to activate this account")
		return redirect('/index')
	return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	verification_key = request.args.get("verification_key")
	form = forms.LoginForm()

	if verification_key and not form.validate_on_submit():
		flash('Please login with your email and password to verify account')
		user = models.users.query.filter_by(verification_key=verification_key).first()
		form.username.data = user.username
		form.verification_key = verification_key

	if current_user.is_authenticated:
		return redirect(url_for('index'))

	if form.validate_on_submit():
		user = models.users.query.filter_by(username=form.username.data).first()

		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect('login')

		login_user(user, remember=form.remember_me.data)

		if verification_key == user.verification_key and not user.verified:
			user.verified = True
			user.set_apitoken()
			db.session.commit()
			flash("Your account has been verified, go to manage account to access your api_token")

		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = '/index'

		return redirect(next_page)
	return render_template('login.html', form=form)


@app.route('/manage_user', methods=['GET', 'POST'])
@login_required
def manage_user():

	userid = current_user.id
	user = models.users.query.filter_by(id=userid).first()
	groupfilter = []
	groupfilter.append(models.usergroups.groupid == models.groups.id)
	groupfilter.append(models.usergroups.userid == userid)
	groups = db.session.query(models.groups.name, models.usergroups.role).filter(*groupfilter).all()
	#form = froms.ManageUserForm():
	#if form.validate_on_submit():

	return render_template('manage_user.html', user=user, groups=groups)


@app.route('/search_pointings', methods=['GET', 'POST'])
@login_required
def search_pointings():

	form = forms.SearchPointingsForm()
	form.populate_graceids()

	if form.validate_on_submit():
		filter = []
		filter.append(models.pointing_event.graceid.contains(form.graceids.data))
		filter.append(models.pointing_event.pointingid == models.pointing.id)

		if form.status_choices.data != '' and form.status_choices.data != 'all':
			filter.append(models.pointing.status == form.status_choices.data)

		if len(form.band_choices.data):
			if "all" not in form.band_choices.data:
				print(form.band_choices.data)
				filter.append(models.pointing.band.in_(form.band_choices.data))

		filter.append(models.pointing.submitterid == models.users.id)
		filter.append(models.pointing.instrumentid == models.instrument.id)

		results = db.session.query(models.pointing.id,
								   func.ST_AsText(models.pointing.position).label('position'),
								   models.pointing.instrumentid,
								   models.pointing.band,
								   models.pointing.pos_angle,
								   models.pointing.depth,
								   models.pointing.time,
								   models.pointing.status,
								   models.instrument.instrument_name,
								   models.users.username
								   ).filter(*filter).all()

		#for r in results:
		#	r.position = str(geoalchemy2.shape.to_shape(r.position))

		return render_template('search_pointings.html', form=form, search_result=results)
	return render_template('search_pointings.html', form=form)


@app.route('/search_instruments', methods=['GET', 'POST'])
@login_required
def search_instruments():
	form = forms.SearchInstrumentsForm()
	if request.method == 'POST':
		if form.types.data != '' and form.types.data != 'all':
			results = db.session.query(models.instrument).filter(models.instrument.instrument_name.ilike(form.name.data +'%')).\
			filter(models.instrument.instrument_type == form.types.data).all()
		else:
			results = db.session.query(models.instrument).filter(models.instrument.instrument_name.ilike(form.name.data +'%')).all()
		return render_template('search_instruments.html', form=form, search_result=results)
	return render_template('search_instruments.html', form=form)


@app.route('/submit_pointings', methods=['GET', 'POST'])
@login_required
def submit_pointing():
	form = forms.SubmitPointingForm()
	form.populate_graceids()
	form.populate_instruments()
	
	if request.method == 'POST':

		#pointing object
		pointing = models.pointing()

		#default required fields
		graceid = form.graceids.data
		status = form.obs_status.data
		ra = form.ra.data
		dec = form.dec.data
		instrument = form.instruments.data
		band = form.obs_bandpass.data
		depth_err = form.depth_err.data
		depth = form.depth.data
		depth_unit = form.depth_unit.data

		#validation
		if graceid == 'None':
			flash('GraceID is required')
			return render_template('submit_pointings.html', form=form)

		if status == 'None':
			flash('Status is required')
			return render_template('submit_pointings.html', form=form)

		if not function.isFloat(ra) or not function.isFloat(dec):
			flash("RA and DEC must be decimal")
			return render_template('submit_pointings.html', form=form)
			
		if instrument == 'None':
			flash('Instrument is required')
			return render_template('submit_pointings.html', form=form)

		instrumentid, instrument_type = int(instrument.split('_')[0]), instrument.split('_')[1]

		if band == 'None' and instrument_type == "photometric":
			flash('Bandpass is required for photometric instrument')
			return render_template('submit_pointings.html', form=form)

		if depth is None:
			flash('Depth is required')
			return render_template('submit_pointings.html', form=form)
			
		if depth_unit == 'None':
			flash('Depth Unit is required')
			return render_template('submit_pointings.html', form=form)

		#inserting
		pointing.datecreated = datetime.datetime.now()
		pointing.position="POINT("+str(ra)+" "+str(dec)+")"
		pointing.submitterid = current_user.get_id()
		pointing.status = status
		pointing.instrumentid = instrumentid
		pointing.band = band
		pointing.depth = depth
		pointing.depth_err = depth_err
		pointing.depth_unit = depth_unit

		#conditional status
		if status == models.pointing_status.completed.name:

			#required fields
			completed_time = form.completed_obs_time.data
			pos_angle = form.pos_angle.data

			#validation
			if completed_time is None:
				flash('Completed time is required')
				return render_template('submit_pointings.html', form=form)
			if pos_angle is None:
				flash('Position Angle is required')
				return render_template('submit_pointings.html', form=form)

			#inserting
			pointing.time = completed_time
			pointing.pos_angle = pos_angle

		#conditional status
		if status == models.pointing_status.planned.name:

			#required fields
			planned_time = form.planned_obs_time.data

			#validation
			if planned_time is None:
				flash('Planned time is required')
				return render_template('submit_pointings.html', form=form)
		
			#inserting
			pointing.time = planned_time

		#commiting data
		db.session.add(pointing)
		db.session.flush()

		pointing_e = models.pointing_event(
				graceid=graceid,
				pointingid=pointing.id
		)
		db.session.add(pointing_e)
		db.session.commit()

		flash("Successful submission of Pointing. Your Pointing ID is "+str(pointing.id))
		flash("Please keep track of your pointing ids")
		return redirect("/index")

	return render_template('submit_pointings.html', form=form)


@app.route('/submit_instrument', methods=['GET', 'POST'])
@login_required
def submit_instrument():
	form = forms.SubmitInstrumentForm()

	args = request.args
	print(args)

	if request.method == 'POST' or False:

		instrument = models.instrument()
		valid_map = instrument.from_json(form, current_user.get_id())

		if len(valid_map[0].errors) > 0:
			for e in valid_map[0].errors:
				flash(e)
			return render_template('submit_instrument.html', form=form, plot=None)

		footprint = valid_map[1]

		db.session.add(instrument)
		db.session.flush()

		for f in footprint:
			fccd = models.footprint_ccd(
				instrumentid = instrument.id,
				footprint = f
			)
			db.session.add(fccd)
		
		db.session.commit()

		flash("Successful submission of Instrument. Your instrument ID is "+str(instrument.id))
		return redirect("/index")

	return render_template('submit_instrument.html', form=form, plot=None)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/index')

#AJAX FUNCTIONS
@app.route('/preview_footprint', methods=['GET'])
def preview_footprint():
	args = request.args
	
	form = forms.SubmitInstrumentForm(
		instrument_name = args.get('instrument_name'),
		instrument_type = args.get('instrument_type'),
    	unit = args.get('unit'),
    	footprint_type = args.get('footprint_type'),
    	height = args.get('height'),
    	width = args.get('width'),
    	radius = args.get('radius'),
    	polygon = args.get('polygon')
	)

	instrument = models.instrument()
	v = instrument.from_json(form, 0, True)

	if len(v[0].errors) == 0:
		trace = []
		vertices = v[2]
		print(vertices, 'vertices')
		for vert in vertices:
			xs = [v[0] for v in vert]
			ys =[v[1] for v in vert]
			trace1 = go.Scatter(
				x=xs,
				y=ys,
				mode='markers',
				fill='tozeroy',
			)
			trace.append(trace1)
		fig = go.Figure(data=trace)
		data = fig
		graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
		return graphJSON
	print(v[0].errors)
	return jsonify("")


@app.route('/pointingfromid')
def get_pointing_fromID():
	args = request.args
	if 'id' in args:
		#try:
		id = args.get('id')
		pfilter = []
		pfilter.append(models.pointing.submitterid == current_user.get_id())
		pfilter.append(models.pointing.status == models.pointing_status.planned)

		pointings = pointings_from_IDS([id], pfilter)

		pointing = pointings[str(id)]
		
		pointing_json = {}

		position = pointing.position
		ra = position.split('POINT(')[1].split(' ')[0]
		dec = position.split('POINT(')[1].split(' ')[1].split(')')[0]
		
		pointing_json['ra'] = ra
		pointing_json['dec'] = dec
		pointing_json['graceid'] = pointing.graceid
		pointing_json['instrument'] = str(pointing.instrumentid)+'_'+models.instrument_type(pointing.instrument_type).name
		pointing_json['band'] = pointing.band.name
		pointing_json['depth'] = pointing.depth
		pointing_json['depth_err'] = pointing.depth_err
		
		return jsonify(pointing_json)
		#except Exception as e:
		#	print(e)
		#	pass
	return jsonify('')


#FIX DATA
@app.route('/fixshit', methods=['POST'])
def fixshit():
	#fixshitlogic
	return 'success'


#Internal Functions
def extract_polygon(p, scale):
	vertices = []
	errors = []
	try:
		for itera,line in enumerate(p.split('\r\n')):
			if line.strip() != "":
				splitlineconfusion = line.split('(')[1].split(')')[0].split(',')
				x = round(float(splitlineconfusion[0])*scale, 5)
				y = round(float(splitlineconfusion[1])*scale, 5)
				vertices.append([x, y])

	except Exception as e:
		errors.append("Error: " + str(e))
		errors.append("For line "+str(itera+1)+": "+line)
		errors.append("Please check the example for correct format")
		return [vertices, errors]
	
	if len(vertices) < 3:
		errors.append('Invalid Polygon. Must have more than 2 vertices')
		return [vertices, errors]

	if vertices[0] != vertices[len(vertices)-1]:
		vertices.append(vertices[0])

	return [vertices, errors]


def create_geography(vertices):
	geom = "POLYGON(("
	for v in vertices:
		geom += str(v[0])+" "+str(v[1])+", "
	geom = geom[0:len(geom)-2]
	geom += "))"
	return geom


def pointings_from_IDS(ids, filter=[]):

	filter.append(models.instrument.id == models.pointing.instrumentid)
	filter.append(models.pointing_event.pointingid.in_(ids))
	filter.append(models.pointing.id.in_(ids))

	pointings = db.session.query(models.pointing.id,
								   func.ST_AsText(models.pointing.position).label('position'),
								   models.pointing.instrumentid,
								   models.pointing.band,
								   models.pointing.pos_angle,
								   models.pointing.depth,
								   models.pointing.depth_err,
								   models.pointing.depth_unit,
								   models.pointing.time,
								   models.pointing.status,
								   models.instrument.instrument_name,
								   models.instrument.instrument_type,
								   models.pointing_event.graceid
								   ).filter(*filter).all()
	
	pointing_returns = {}
	for p in pointings:
		pointing_returns[str(p.id)] = p

	return pointing_returns


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_account_validation_email(user):
	send_email(
		"Treasure Map Account Verification",
		"gwtreasuremap@gmail.com",
		[user.email],
		"",
		"<p>Hello "+user.firstname+",<br><br> \
		Thank you for registering for The Gravitational Wave Treasure Map Project! Please follow this <a href=treasuremap.space/login?verification_key="+user.verification_key+">address</a> to verify your account. <br>\
		Please do not reply to this email<br><br> \
		Cheers from the Treasure Map team </p>",
	)


#API Endpoints

#Get instrument footprints
@app.route("/api/v0/footprints", methods=['GET'])
def get_footprints():
	footprints= db.session.query(models.footprint_ccd).all()
	footprints = [x.json for x in footprints]

	return jsonify(footprints)


#Get Galaxies From glade_2p3
@app.route("/api/v0/glade", methods=['GET'])
def get_galaxies():
	args = request.args

	filter = []
	filter1 = []
	#filter1.append(models.glade_2p3.pgc_number != -1)
	#filter1.append(models.glade_2p3.distance > 0)
	#filter1.append(models.glade_2p3.distance < 100)
	trim = db.session.query(models.glade_2p3).filter(*filter1)

	orderby = []
	if 'ra' in args and 'dec' in args:
		ra = args.get('ra')
		dec = args.get('dec')
		if function.isFloat(ra) and function.isFloat(dec):
			geom = "SRID=4326;POINT("+str(ra)+" "+str(dec)+")"
			orderby.append(func.ST_Distance(models.glade_2p3.position, geom))
	if 'name' in args:
		name = args.get('name')
		ors = []
		ors.append(models.glade_2p3._2mass_name.contains(name.strip()))
		ors.append(models.glade_2p3.gwgc_name.contains(name.strip()))
		ors.append(models.glade_2p3.hyperleda_name.contains(name.strip()))
		ors.append(models.glade_2p3.sdssdr12_name.contains(name.strip()))
		filter.append(fsq.sqlalchemy.or_(*ors))
	
	galaxies = trim.filter(*filter).order_by(*orderby).limit(15).all()

	galaxies = [x.json for x in galaxies]

	return jsonify(galaxies)

#Post Pointing/s
#Parameters: List of Pointing JSON objects
#Returns: List of assigned IDs
#Comments: Check if instrument configuration already exists to avoid duplication. 
#Check if pointing is centered at a galaxy in one of the catalogs and if so, associate it.

@app.route("/api/v0/pointings", methods=["POST"])
def add_pointings():

	try:
		rd = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")
		     
	valid_gid = False

	if "graceid" in rd:
		gid = rd['graceid']
		current_gids = db.session.query(models.gw_alert.graceid).filter(models.gw_alert.graceid == gid).all()
		if len(current_gids) > 0:
			valid_gid = True
		else:
			return jsonify("Invalid graceid")
	else:
		return jsonify("graceid is required")

	if "api_token" in rd:
		apitoken = rd['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
		else:
			userid = user.id
	else:
		return jsonify("api_token is required")

	dbinsts = db.session.query(models.instrument.instrument_name,
                               models.instrument.id).all()

	points = []
	errors = []
	warnings = []

	filter = [models.pointing.submitterid == userid]

	if "pointing" in rd:
		p = rd['pointing']
		mp = models.pointing()
		if 'id' in p:
			if function.isInt(p['id']):
				planned_pointings = pointings_from_IDS([p['id']], filter)
		v = mp.from_json(p, dbinsts, userid, planned_pointings)
		if v.valid:
			points.append(mp)
			if len(v.warnings) > 0:
				warnings.append(["Object: " + json.dumps(p), v.warnings])
			db.session.add(mp)
		else:
			errors.append(["Object: "+json.dumps(p), v.errors])
            
	elif "pointings" in rd:
		pointings = rd['pointings']
		planned_ids = []
		for p in pointings:
			if 'id' in p:
				if function.isInt(p['id']):
					planned_ids.append(int(p['id']))
		planned_pointings = pointings_from_IDS(planned_ids, filter)

		for p in pointings:
			mp = models.pointing()
			v = mp.from_json(p, dbinsts, userid, planned_pointings)
			if v.valid:
				points.append(mp)
				db.session.add(mp)
				if len(v.warnings) > 0:
					warnings.append(["Object: " + json.dumps(p), v.warnings])
			else:
				errors.append(["Object: "+json.dumps(p), v.errors])
	else: 
		return jsonify("Invalid request: json pointing or json list of pointings are required\nYou can find API documentation here: treasuremap.space/documentation.com")

	db.session.flush()

	if valid_gid:
		for p in points:
			pe = models.pointing_event(
				pointingid = p.id,
				graceid = gid)
			db.session.add(pe)

	db.session.flush()
	db.session.commit()
	return jsonify({"pointing_ids":[x.id for x in points], "ERRORS":errors, "WARNINGS":warnings})

#Get Pointing/s
#Parameters: List of ID/s, type/s, group/s, user/s, and/or time/s constraints (to be AND’ed). 
#Returns: List of PlannedPointing JSON objects

@app.route("/api/v0/pointings", methods=["GET"])
def get_pointings():

	args = request.args

	filter=[]

	if "graceid" in args:
		graceid = args.get('graceid')
		filter.append(models.pointing_event.graceid == graceid)
		filter.append(models.pointing_event.pointingid == models.pointing.id)

	if "id" in args:
		_id = args.get('id')
		filter.append(models.pointing.id == int(_id))
	elif "ids" in args:
		ids = json.loads(args.get('ids'))
		filter.append(models.pointing.id.in_(ids))

	if "band" in args:
		band = args.get('band')
		filter.append(models.pointing.band == band)
	elif "bands" in args:
		bands_sent = args.get('bands')
		bands = []
		for b in models.bandpass:
			if b.name in bands_sent:
				bands.append(b)
		filter.append(models.pointing.band.in_(bands))

	if "status" in args:
		status = args.get('status')
		filter.append(models.pointing.status == status)
	elif "statuses" in args:
		statuses = []
		statuses_sent = args.get('statuses')
		if "planned" in statuses_sent:
			statuses.append(models.pointing_status.planned)
		if "completed" in statuses_sent:
			statuses.append(models.pointing_status.completed)
		if "cancelled" in statuses_sent:
			statuses.append(models.pointing_status.cancelled)
		filter.append(models.pointing.status.in_(statuses))

	if "completed_after" in args:
		time = args.get('completed_after')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S format. e.g. 2019-05-01T12:00:00")
		filter.append(models.pointing.status == models.pointing_status.completed)
		filter.append(models.pointing.time >= time)

	if "completed_before" in args:
		time = args.get('completed_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S format. e.g. 2019-05-01T12:00:00")
		filter.append(models.pointing.status == models.pointing_status.completed)
		filter.append(models.pointing.time <= time)

	if "planned_after" in args:
		time = args.get('planned_after')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S format. e.g. 2019-05-01T12:00:00")
		filter.append(models.pointing.status == models.pointing_status.planned)
		filter.append(models.pointing.time >= time)

	if "planned_before" in args:
		time = args.get('planned_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S format. e.g. 2019-05-01T12:00:00")
		filter.append(models.pointing.status == models.pointing_status.planned)
		filter.append(models.pointing.time <= time)

	if "group" in args:
		group = args.get('group')
		if group.isdigit():
			filter.append(models.usergroups.groupid == group)
		else:
			filter.append(models.groups.name.contains(group))
			filter.append(models.usergroups.groupid == models.groups.id)

		filter.append(models.usergroups.userid == models.users.id)
		filter.append(models.users.id == models.pointing.submitterid)

	elif "groups" in args:
		try:
			groups = json.loads(args.get('groups'))
			filter.append(models.usergroups.groupid.in_(groups))
		except:
			groups = args.get('groups')
			groups = groups.split('[')[1].split(']')[0].split(',')
			ors = []
			print(groups)
			for g in groups:
				ors.append(models.groups.name.contains(g.strip()))
			filter.append(fsq.sqlalchemy.or_(*ors))
			filter.append(models.usergroups.groupid == models.groups.id)
		filter.append(models.usergroups.userid == models.users.id)
		filter.append(models.users.id == models.pointing.submitterid)

	if "user" in args:
		user = args.get('user')
		if user.isdigit():
			filter.append(models.pointing.submitterid == int(user))
		else:
			filter.append(fsq.sqlalchemy.or_(models.users.username.contains(user),
							  models.users.firstname.contains(user),
							  models.users.lastname.contains(user)))
			filter.append(models.users.id == models.pointing.submitterid)

	if "users" in args:
		try:
			users = json.loads(args.get('users'))
			filter.append(models.pointing.submitterid.in_(users))
		except:
			users = args.get('users')
			users = users.split('[')[1].split(']')[0].split(',') 
			ors = []
			for u in users:
				ors.append(models.users.username.contains(u.strip()))
				ors.append(models.users.firstname.contains(u.strip()))
				ors.append(models.users.lastname.contains(u.strip()))
			filter.append(fsq.sqlalchemy.or_(*ors))
			filter.append(models.users.id == models.pointing.submitterid)
	
	if "instrument" in args:
		inst = args.get('instrument')
		if inst.isdigit():
			filter.append(models.pointing.instrumentid == int(inst))
		else:
			filter.append(models.pointing.instrumentid == models.instrument.id)
			filter.append(models.instrument.instrument_name.contains(inst))

	if "instruments" in args:
		try:
			insts = json.loads(args.get('instruments'))
			filter.append(models.pointing.instrumentid.in_(insts))
		except:
			insts = args.get('instruments')
			insts = insts.split('[')[1].split(']')[0].split(',') 
			ors = []
			for i in insts:
				ors.append(models.instrument.instrument_name.contains(i.strip()))
			filter.append(fsq.sqlalchemy.or_(*ors))
			filter.append(models.instrument.id == models.pointing.instrumentid)

	pointings = db.session.query(models.pointing).filter(*filter).all()
	pointings = [x.json for x in pointings]

	return jsonify(pointings)

#Cancel PlannedPointing
#Parameters: List of IDs of planned pointings for which it is known that they aren’t going to happen

@app.route("/api/v0/update_pointings", methods=["POST"])
def del_pointings():
	args = request.args

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
		else:
			userid = user.id
	else:
		return jsonify("api_token is required")

	if 'status' in args:
		status = args['status']
		if status not in ['cancelled']:
			return jsonify('planned status can only be updated to \'cancelled\'')
	else: 
		status = 'cancelled'

	filter1 = []
	filter1.append(models.pointing.status == models.pointing_status.planned)
	filter1.append(models.pointing.submitterid == userid)
	if "id" in args:
		filter1.append(models.pointing.id == int(args.get('id')))
	elif "ids" in args:
		filter1.append(models.pointing.id.in_(json.loads(args.get('ids'))))
	else:
		return jsonify('id or ids of pointing event is required')

	if len(filter1) > 0:
		pointings = db.session.query(models.pointing).filter(*filter1)
		for p in pointings:
			if status == 'cancelled':
				setattr(p, 'status', models.pointing_status.cancelled)
				setattr(p, 'dateupdated', datetime.datetime.now())
		db.session.commit()
		return jsonify("Updated Pointings successfully")

	else:
		return jsonify("Please Don't update the ENTIRE POINTING table")

#Get Instrument/s
#Parameters: List of ID/s, type/s (to be AND’ed).
#Returns: List of Instrument JSON objects

@app.route("/api/v0/instruments", methods=["GET"])
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
	if "name" in args:
		name = args.get('name')
		filter.append(models.instrument.instrument_name.contains(name))
	if "names" in args:
		insts = args.get('instruments')
		insts = insts.split('[')[1].split(']')[0].split(',') 
		ors = []
		for i in insts:
			ors.append(models.instrument.instrument_name.contains(i.strip()))
		filter.append(fsq.sqlalchemy.or_(*ors))
		filter.append(models.instrument.id == models.pointing.instrumentid)

	if "type" in args:
		#validate
		_type = args.get('type')
		filter.append(models.instrument.instrument_type == _type)

	insts = db.session.query(models.instrument).filter(*filter).all()
	insts = [x.json for x in insts]

	return jsonify(insts)

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
