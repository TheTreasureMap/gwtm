# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import flask_sqlalchemy as fsq
from geoalchemy2 import Geometry
import geoalchemy2
from enum import Enum

import os, json, datetime
import random, math

from . import function
from . import models
from . import forms
from src import app
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

db = models.db

@app.route("/index", methods=["GET"])
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/alerts", methods=['GET'])
@login_required
def alerts():
	alerts = models.gw_alert.query.filter_by(role="observation").all()
	alerts = list(set([a.graceid for a in alerts]))
	return render_template("alerts.html", alerts=alerts)


@app.route("/gw_event", methods=['GET'])
@login_required
def ligo_alert():
	#get graceID and display visulization.
	return render_template('gw_event.html', graceid=graceid)


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
			datecreated=datetime.datetime.now()
			)
        user.set_password(form.password.data)
        user.set_apitoken()
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = models.users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            #print("Invalid username or password")
            return redirect('login')
        login_user(user, remember=form.remember_me.data)
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
		filter = []
		if form.name.data != '':
			filter.append(models.instrument.instrument_name.contains(form.name.data))
		if form.types.data != '' and form.types.data != 'all':
			filter.append(models.instrument.instrument_type == form.types.data)
		results = db.session.query(models.instrument).filter(*filter).all()
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
	if request.method == 'POST':
		submitterid = current_user.get_id()
		instrument_type = form.instrument_type.data
		instrument_name = form.instrument_name.data
		footprint = None

		u = form.unit.data
		if u is None or u == "choose":
			flash('Unit is required')
			return render_template('submit_instrument.html', form=form, again='/submit_instrument')

		if instrument_type == "choose":
			flash('Instrument Type is required')
			return render_template('submit_instrument.html', form=form, again='/submit_instrument')

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
				flash('Height and Width are required for Rectangular shape')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")
			if not function.isFloat(h) or not function.isFloat(w):
				flash('Height and Width must be decimal')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")
			vertices = []
			half_h = round(0.5*float(h)*scale, 4)
			half_w = round(0.5*float(w)*scale, 4)
			vertices.append([-half_w, half_h])
			vertices.append([half_w, half_h])
			vertices.append([half_w, -half_h])
			vertices.append([-half_w, -half_h])
			vertices.append([-half_w, half_h])

			geom = "POLYGON(("
			for v in vertices:
				geom += str(v[0])+" "+str(v[1])+", "
			geom = geom[0:len(geom)-2]
			geom += "))"
			footprint = geom

		if form.footprint_type.data == 'Circular':
			r = form.radius.data

			if r is None:
				flash('Radius is required for Circular shape')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")
			if not function.isFloat(r):
				flash('Radius must be decimal')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")

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

			geom = "POLYGON(("
			for v in vertices:
				geom += str(v[0])+" "+str(v[1])+", "
			geom = geom[0:len(geom)-2]
			geom += "))"
			footprint = geom

		if form.footprint_type.data == 'Polygon':
			p = form.polygon.data
			if p is None:
				flash('Polygon is required for Polygon shape')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")

			vertices = []

			try:
				for itera,line in enumerate(p.split('\r\n')):
					if line.strip() != "":
						splitlineconfusion = line.split('(')[1].split(')')[0].split(',')
						x = round(float(splitlineconfusion[0])*scale, 5)
						y = round(float(splitlineconfusion[1])*scale, 5)
						vertices.append([x, y])

			except Exception as e:
				flash("Error: " + str(e))
				flash("For line "+str(itera+1)+": "+line)
				flash("Please check the example for correct format")
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")
			
			if len(vertices) < 3:
				flash('Invalid Polygon. Must have more than 2 vertices')
				return render_template('submit_instrument.html', form=form, again="/submit_instrument")

			if vertices[0] != vertices[len(vertices)-1]:
				vertices.append(vertices[0])

			geom = "POLYGON(("
			for v in vertices:
				geom += str(v[0])+" "+str(v[1])+", "
			geom = geom[0:len(geom)-2]
			geom += "))"
			footprint = geom

		if footprint is None:
			flash('Footprint required')	
			return render_template('submit_instrument.html', form=form, again='/submit_instrument')

		instrument = models.instrument(
			instrument_name = instrument_name,
			instrument_type = instrument_type,
			submitterid = submitterid,
			footprint = footprint,
			datecreated = datetime.datetime.now()
		)
		db.session.add(instrument)
		db.session.flush()
		db.session.commit()

		flash("Successful submission of Instrument. Your instrument ID is "+str(instrument.id))
		return redirect("/index")

	return render_template('submit_instrument.html', form=form, again="/submit_instrument")


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/index')

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
		print(position)
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


#API Endpoints
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
