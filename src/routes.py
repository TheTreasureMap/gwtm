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
import numpy as np
import healpy as hp
import astropy
from astropy import coordinates
from astropy.time import Time
from mocpy import MOC, WCS
from astropy.coordinates import Angle, SkyCoord
import astropy.units as u
import time
import plotly
import plotly.graph_objects as go
import ephem
import io
import requests

from . import function
from . import models
from . import forms

from src import app
from src import mail

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
@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500

@app.route("/index", methods=["GET"])
@app.route("/", methods=["GET"])
def home():
	#get latest alert. Construct the form alertsform

	#fix this by ingesting LAT pointings in the pointings DB
	if os.path.exists('/var/www/gwtm/src/static'):
		fermi_events = len([x for x in os.listdir('/var/www/gwtm/src/static') if 'Fermi' in x])
	else:
		fermi_events = 0

	inst_info = db.session.query(
		models.pointing,
		models.instrument
	).group_by(
		models.pointing.instrumentid,
		models.instrument
	).filter(
		models.pointing.status == models.pointing_status.completed,	
		models.instrument.id == models.pointing.instrumentid,
		models.pointing_event.pointingid == models.pointing.id,
		models.pointing_event.graceid != 'TEST_EVENT'
	).order_by(
		func.count(models.pointing.id).desc()
	).values(
		func.count(models.pointing.id).label('count'),
		models.instrument.instrument_name,
		models.instrument.id
	)

	inst_info = [list(inst_info), fermi_events]

	graceids = db.session.query(
		models.gw_alert.graceid,
		models.gw_alert.alert_type,
	).order_by(
		models.gw_alert.time_of_signal.desc()
	).filter(
		models.gw_alert.graceid != 'TEST_EVENT'
	).all()

	gids = list(sorted(set([x.graceid for x in graceids]), reverse=True))
	rets = []
	for g in gids:
		gw_alerts = [x.alert_type for x in graceids if x.graceid == g]
		if 'Retraction' in gw_alerts:
			rets.append(g)

	gids = [x for x in gids if x not in rets]
	graceid = gids[0]

	status = request.args.get('pointing_status')
	status = status if status is not None else 'completed'

	alerttype = request.args.get('alert_type')
	args = {'graceid':graceid, 'pointing_status':status, 'alert_type':alerttype} 
	form = forms.AlertsForm
	form, detection_overlays, inst_overlays, GRBoverlays, galaxy_cats = construct_alertform(form, args)
	form.page = 'index'
	return render_template("index.html", form=form, inst_table=inst_info, detection_overlays=detection_overlays, inst_overlays=inst_overlays, GRBoverlays=GRBoverlays, galaxy_cats=galaxy_cats)

class overlay():
	def __init__(self, name, color, contours):
		self.name = name
		self.color = color
		self.contours = contours

@app.route("/alert_select", methods=['GET'])
def alert_select():

	allerts = db.session.query(
		models.gw_alert
	).filter(
		models.gw_alert.graceid != 'TEST_EVENT',
		models.gw_alert.graceid != 'GW170817'
	).all()

	p_event_counts = db.session.query(
		models.pointing_event
	).group_by(
		models.pointing_event.graceid
	).filter(
		models.pointing.id == models.pointing_event.pointingid,
		models.pointing.status == models.pointing_status.completed
	).values(
		func.count(models.pointing_event.graceid).label('pcount'),
		models.pointing_event.graceid
	)

	p_event_counts = list(p_event_counts)
	
	gids = list(sorted(set([x.graceid for x in allerts]), reverse=True))
	
	non_retracted_alerts = []
	all_alerts = {}

	for g in gids:
		alert_types = [x.alert_type for x in allerts if x.graceid == g]
		most_recent_date = list(sorted([x.datecreated for x in allerts if x.graceid == g], reverse=True))[0]
		most_recent_alert = [x for x in allerts if x.graceid == g and x.datecreated == most_recent_date][0]
		pcounts = [x.pcount for x in p_event_counts if g == x.graceid]

		pointing_counts = 0
		if len(pcounts):
			pointing_counts = pcounts[0]

		if 'Retraction' in alert_types:
			all_alerts[g] = {
				'class':'Retracted',
				'distance':'',
				'pcounts':pointing_counts 
			}

		else:
			classification = most_recent_alert.getClassification()
			all_alerts[g] = {
				'class':classification,
				'distance':str(round(most_recent_alert.distance, 2)) + ' +/- ' + str(round(most_recent_alert.distance_error, 2)),
				'pcounts':pointing_counts
			}

	all_alerts['TEST_EVENT'] = {
		'class':'Test',
		'distance':'',
		'pcounts':''
	}

	return render_template("alert_select.html", alerts=all_alerts)

@app.route("/alerts", methods=['GET', 'POST'])
#@login_required
def alerts():
	graceid = request.args.get('graceids')
	status = request.args.get('pointing_status')
	status = status if status is not None else 'completed'
	alerttype = request.args.get('alert_type')
	args = {'graceid':graceid, 'pointing_status':status, 'alert_type': alerttype}
	form = forms.AlertsForm
	form.page = 'alerts'
	form, detection_overlays, inst_overlays, GRBoverlays, galaxy_cats = construct_alertform(form, args)
	if graceid != 'None' and graceid is not None:
		return render_template("alerts.html", form=form, detection_overlays= detection_overlays, inst_overlays=inst_overlays, GRBoverlays=GRBoverlays, galaxy_cats=galaxy_cats)
		
	form.graceid = 'None'
	return render_template("alerts.html", form=form)


@app.route("/fairuse", methods=['GET'])
def fairuse():
	return render_template('fairuse.html')

@app.route("/status", methods=['GET'])
def status():
	return render_template('status.html')


@app.route("/documentation", methods=['GET'])
def documentation():
	return render_template('documentation.html')


@app.route("/jupyter_tutorial", methods=['GET'])
def jupyter():
	return render_template('jupyter_tutorial.html')


@app.route("/development_blog", methods=['GET'])
def devblog():
	return render_template('development_blog.html')


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

	if current_user.is_authenticated:
		logout_user()

	if verification_key and not form.validate_on_submit():
		flash('Please login with your email and password to verify account')
		user = models.users.query.filter_by(verification_key=verification_key).first()
		form.username.data = user.username
		form.verification_key = verification_key

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


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
	token = request.args.get('token')
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	user = models.users.verify_reset_password_token(token)
	if not user:
		return redirect(url_for('index'))
	form = forms.ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Your password has been reset.')
		return redirect(url_for('login'))
	return render_template('reset_password.html', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = forms.ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = models.users.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html',
						   title='Reset Password', form=form)


@app.route('/manage_user', methods=['GET', 'POST'])
@login_required
def manage_user():
	userid = current_user.id
	user = models.users.query.filter_by(id=userid).first()
	groupfilter = []
	groupfilter.append(models.usergroups.groupid == models.groups.id)
	groupfilter.append(models.usergroups.userid == userid)
	groups = db.session.query(models.groups.name, models.usergroups.role).filter(*groupfilter).all()

	doi_groups = db.session.query(models.doi_author_group).filter(models.doi_author_group.userid == userid)
	#form = froms.ManageUserForm():
	#if form.validate_on_submit():

	if userid == 2 or userid == 5:
		all_users = models.users.query.order_by(models.users.datecreated.asc()).all()
		return render_template('manage_user.html', user=user, doi_groups=doi_groups, users=all_users)
	else:
		return render_template('manage_user.html', user=user, doi_groups=doi_groups)


@app.route('/search_pointings', methods=['GET', 'POST'])
#@login_required
def search_pointings():
	form = forms.SearchPointingsForm()
	form.populate_graceids()
	form.populate_creator_groups(current_user.get_id())
	print(form.doi_creator_groups.choices)


	if form.validate_on_submit():
		filter = []
		filter.append(models.pointing_event.graceid.contains(form.graceids.data))
		filter.append(models.pointing_event.pointingid == models.pointing.id)

		if form.status_choices.data != '' and form.status_choices.data != 'all':
			filter.append(models.pointing.status == form.status_choices.data)

		if len(form.band_choices.data):
			if "all" not in form.band_choices.data:
				filter.append(models.pointing.band.in_(form.band_choices.data))

		if form.my_points.data:
			filter.append(models.pointing.submitterid == current_user.get_id())

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
								   models.pointing.doi_url,
								   models.pointing.doi_id,
								   models.instrument.instrument_name,
								   models.users.username,
								   models.pointing.submitterid
								   ).filter(*filter).all()

		return render_template('search_pointings.html', form=form, search_result=results)
	return render_template('search_pointings.html', form=form)



@app.route('/search_instruments', methods=['GET', 'POST'])
#@login_required
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
	form.populate_creator_groups(current_user.get_id())
	print(form.doi_creator_groups.choices)
	
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
			print(completed_time)
			if completed_time is None:
				flash('Completed time is required')
				flash('Completed time must be in the format of \'%Y-%m-%dT%H:%M:%S.%f\'')
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
				flash('Planned time must be in the format of \'%Y-%m-%dT%H:%M:%S.%f\'')
				return render_template('submit_pointings.html', form=form)
		
			#inserting
			pointing.time = planned_time


		otherpointings = db.session.query(models.pointing).filter(
			models.pointing.id == models.pointing_event.pointingid,
			models.pointing_event.graceid == graceid
		).all()

		if pointing_crossmatch(pointing, otherpointings):
			flash("Pointing already submitted")
			return render_template('submit_pointings.html', form=form)

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

		if form.request_doi.data:
			user = models.users.query.filter_by(id=pointing.submitterid).first()
			if form.doi_creator_groups.data != 'None':
				valid, creators = construct_creators(form.doi_creator_groups.data, user.id)
				print(creators)
				if not valid:
					creators = [{"name":str(user.firstname) + " " + str(user.lastname), "affiliation":""}]
			else:
				creators = [{"name":str(user.firstname) + " " + str(user.lastname), "affiliation":""}]

			points = [pointing]

			insts = db.session.query(models.instrument).filter(models.instrument.id.in_([x.instrumentid for x in points]))
			inst_set = list(set([x.instrument_name for x in insts]))

			pointing.doi_id, pointing.doi_url = create_doi(points, graceid, creators, inst_set)
			db.session.commit()
			flash("Your DOI url is: "+pointing.doi_url)

		return redirect("/index")

	return render_template('submit_pointings.html', form=form)


@app.route('/submit_instrument', methods=['GET', 'POST'])
@login_required
def submit_instrument():
	form = forms.SubmitInstrumentForm()

	insts = db.session.query(
		models.instrument
	).all()

	args = request.args

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

	return render_template('submit_instrument.html', form=form, plot=None, insts=insts)

@app.route('/instrument_info')
def instrument_info():
	instid = request.args.get('id')

	instrument = db.session.query(
		models.instrument,
		models.users.username,
		func.ST_AsText(models.footprint_ccd.footprint).label('footprint')
	).filter(
		models.instrument.id == instid,
		models.instrument.id == models.footprint_ccd.instrumentid,
		models.instrument.submitterid == models.users.id
	).all()

	events_contributed = db.session.query(
		models.pointing,
		models.gw_alert.graceid
	).filter(
		models.pointing.instrumentid == instid,
		models.pointing_event.pointingid == models.pointing.id,
		models.gw_alert.graceid == models.pointing_event.graceid,
	).all()

	gids = sorted(list(set([x.graceid for x in events_contributed])), reverse=True)
	events = []
	for g in gids:
		numevents = len([x for x in events_contributed if x.graceid == g])
		events.append({'event':g, 'count':str(numevents)})

	if len(instrument) > 0:
		inst = instrument[0].instrument
		username = instrument[0].username
		sanatized_ccds = function.sanatize_footprint_ccds([x.footprint for x in instrument])
		trace = []
		vertices = sanatized_ccds
		for vert in vertices:
			xs = [v[0] for v in vert]
			ys =[v[1] for v in vert]
			trace1 = go.Scatter(
				x=xs,
				y=ys,
				line_color='blue',
				fill='tozeroy',
				fillcolor='violet'
			)
			trace.append(trace1)
		fig = go.Figure(data=trace)
		fig.update_layout(
			showlegend=False,
			xaxis_title = 'degrees',
			yaxis_title = 'degrees',
			width=500,
			height=500,
			yaxis=dict(
				matches='x',
				scaleanchor="x",
				scaleratio=1,
				constrain='domain',
			)
		)
		data = fig
		graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

	return render_template('instrument_info.html', inst=inst, graph=graphJSON, events=events, username=username)

def authors_from_page(form):
	authors = []
	for aid, an, aff, orc, gnd in zip(
			form.getlist('author_id'),
			form.getlist('author_name'),
			form.getlist('affiliation'),
			form.getlist('orcid'),
			form.getlist('gnd')
		):
		print(aid, an, aff, orc, gnd)
		if  str(aid) == "" or str(aid) == "None":
			authors.append(
				models.doi_author(
					name=an,
					affiliation=aff,
					orcid=orc,
					gnd=gnd
				)
			)
		else:
			authors.append(
				models.doi_author(
					id=int(aid),
					name=an,
					affiliation=aff,
					orcid=orc,
					gnd=gnd
				)
			)	
	return authors

def validate_authors(authors):
	if len(authors) == 0:
		return False, "At least one author is required"
	for a in authors:
		if a.name is None or a.name == "":
			return False, "Author Name is required"
		if a.affiliation is None or a.affiliation == "":
			return False, "Affiliation is required"
	return True, ''

@app.route('/doi_author_group', methods=['GET','POST'])
def doi_author_group():
	#I want to be able to edit/and create on the same page
	#test for the id, if there is one, then load it
	form = request.form
	groupid = request.args.get('doi_group_id')

	#test to load page
	if groupid and request.method != 'POST':
		doi_author_group = db.session.query(models.doi_author_group).filter(models.doi_author_group.id == groupid).first()

		if doi_author_group.userid != int(current_user.get_id()):
			flash("Invalid Author Group. You may only view your own")
			return redirect('/manage_user')

		authors = db.session.query(models.doi_author).filter(models.doi_author.author_groupid == groupid).order_by(models.doi_author.id).all()
		return render_template('doi_author_group.html', group_info=doi_author_group, authors=authors)
	
	#test to save
	if groupid and request.method == 'POST':
		authors = authors_from_page(form)
		group_name = form.get('group_name')

		group_info = db.session.query(models.doi_author_group).filter(models.doi_author_group.id == groupid).first()
		group_info.name = group_name

		valid, message = validate_authors(authors)
		if not valid:
			flash(message)
			return render_template('doi_author_group.html', group_info=group_info, authors=authors, create=False)
		if group_name is None or group_name == "":
			flash("Group Name is required")
			return render_template('doi_author_group.html', group_info=group_info, authors=authors, create=False)
		
		prev_authors = db.session.query(models.doi_author).filter(models.doi_author.author_groupid == groupid)
		
		curr_ids = [x.id for x in authors]
		for pre_auth in prev_authors:
			if pre_auth.id not in curr_ids:
				db.session.delete(pre_auth)

		for a in authors:
			a.author_groupid = int(groupid)
			if a.id is None:
				db.session.add(a)
			prev = prev_authors.filter(models.doi_author.id == a.id).first()
			if prev:
				prev.name = a.name
				prev.affiliation = a.affiliation
				prev.orcid = a.orcid
				prev.gnd = a.gnd
				prev.pos_order = a.pos_order
				
		db.session.flush()
		db.session.commit()

		return redirect('/manage_user')
		
	#test if new save
	if groupid is None and request.method == 'POST':
		authors = authors_from_page(form)
		group_name = form.get('group_name')
		group_info = models.doi_author_group(
			name=group_name,
			userid=current_user.get_id()
		)
		valid, message = validate_authors(authors)
		if not valid:
			flash(message)
			return render_template('doi_author_group.html', group_info=group_info, authors=authors, create=True)
		if group_name is None or group_name == "":
			flash("Group Name is required")
			return render_template('doi_author_group.html', group_info=group_info, authors=authors, create=True)

		db.session.add(group_info)
		db.session.flush()
		
		for a in authors:
			a.author_groupid = group_info.id
			db.session.add(a)

		db.session.commit()

		return redirect('/manage_user')
		
	return render_template('doi_author_group.html', create=True)

@app.route('/logout')
def logout():
	logout_user()
	return redirect('/index')


#AJAX FUNCTIONS

@app.route('/ajax_request_doi')
def ajax_request_doi():
	args = request.args
	graceid = args['graceid']
	if args['ids'] != '':
		ids = [int(x) for x in args['ids'].split(',')]

		points = db.session.query(
			models.pointing
		).filter(
			models.pointing_event.pointingid == models.pointing.id,
			models.pointing.id.in_(ids),
			models.pointing_event.graceid == graceid
		).all()
		
		user = db.session.query(models.users).filter(models.users.id == current_user.get_id()).first()

		if 'doi_group_id' in args:
			valid, creators = construct_creators(args['doi_group_id'], current_user.get_id())
			if not valid:
				creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]
		else:
			creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]


		insts = db.session.query(models.instrument).filter(models.instrument.id.in_([x.instrumentid for x in points]))
		inst_set = list(set([x.instrument_name for x in insts]))

		doi_id, doi_url = create_doi(points, graceid, creators, inst_set)

		for p in points:
			p.doi_url = doi_url
			p.doi_id = doi_id
		
		db.session.commit()

		return jsonify(doi_url)
	
	return jsonify('')

@app.route("/coverage", methods=['GET','POST'])
def plot_prob_coverage():
	graceid = request.args.get('graceid')
	mappathinfo = request.args.get('mappathinfo')
	inst_cov = request.args.get('inst_cov')
	band_cov = request.args.get('band_cov')
	depth = request.args.get('depth_cov')
	depth_unit = request.args.get('depth_unit')

	if os.path.exists(mappathinfo):
		try:
			GWmap = hp.read_map(mappathinfo)
			#bestpixel = np.argmax(GWmap)
			nside = hp.npix2nside(len(GWmap))
		except:
			return 'Map error, contact administrator.'
	else:
		return 'Map not found.'

	pointing_filter = []
	pointing_filter.append(models.pointing_event.graceid == graceid)
	pointing_filter.append(models.pointing.status == 'completed')
	pointing_filter.append(models.pointing_event.pointingid == models.pointing.id)
	pointing_filter.append(models.pointing.instrumentid != 49)

	if inst_cov != '':
		print(inst_cov)
		insts_cov = [int(x) for x in inst_cov.split(',')]
		pointing_filter.append(models.pointing.instrumentid.in_(insts_cov))
	if band_cov != '':
		bands_cov = [x for x in band_cov.split(',')]
		pointing_filter.append(models.pointing.band.in_(bands_cov))
	if depth_unit != 'None' and depth_unit != '':
		pointing_filter.append(models.pointing.depth_unit == depth_unit)
	if depth != None and function.isFloat(depth):
		if 'mag' in depth_unit:
			pointing_filter.append(models.pointing.depth >= float(depth))
		elif 'flux' in depth_unit:
			pointing_filter.append(models.pointing.depth <= float(depth))
		else:
			return "You must specify a unit if you want to cut on depth."
	
	pointings_sorted = db.session.query(
		models.pointing.instrumentid,
		models.pointing.pos_angle,
		func.ST_AsText(models.pointing.position).label('position'),
		models.pointing.band,
		models.pointing.depth,
		models.pointing.time
	).filter(
		*pointing_filter
	).order_by(
		models.pointing.time.asc()
	).all()

	instrumentids = [x.instrumentid for x in pointings_sorted]
	#filter and query the relevant instrument footprints
	footprintinfo = db.session.query(
		func.ST_AsText(models.footprint_ccd.footprint).label('footprint'), 
		models.footprint_ccd.instrumentid
	).filter(
		models.footprint_ccd.instrumentid.in_(instrumentids)
	).all()

	#get GW T0 time
	time_of_signal = db.session.query(
		models.gw_alert.time_of_signal
	).filter(
		models.gw_alert.graceid == graceid
	).order_by(
		models.gw_alert.datecreated.desc()
	).first()[0]

	qps = []
	times=[]
	probs=[]
	for p in pointings_sorted:
		ra, dec = function.sanatize_pointing(p.position)

		footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == p.instrumentid]
		sanatized_ccds = function.sanatize_footprint_ccds(footprint_ccds)
		for ccd in sanatized_ccds:
			pointing_footprint = function.project_footprint(ccd, ra, dec, p.pos_angle)


			ras_poly = [x[0] for x in pointing_footprint][:-1]
			decs_poly = [x[1] for x in pointing_footprint][:-1]
			xyzpoly = astropy.coordinates.spherical_to_cartesian(1, np.deg2rad(decs_poly), np.deg2rad(ras_poly))
			qp = hp.query_polygon(nside,np.array(xyzpoly).T)

			qps.extend(qp)
			#deduplicate indices, so that pixels already covered are not double counted
			deduped_indices=list(dict.fromkeys(qps))

			prob = 0
			for ind in deduped_indices:
				prob += GWmap[ind]
			elapsed = p.time - time_of_signal
			elapsed = elapsed.total_seconds()/3600
			times.append(elapsed)
			probs.append(prob)

	fig=go.Figure(data=go.Scatter(x=times,y=[prob*100 for prob in probs],mode='lines'))
	fig.update_layout(xaxis_title='Hours since GW T0', yaxis_title='Percent of GW localization covered')
	coverage_div = plotly.offline.plot(fig,output_type='div',include_plotlyjs=False, show_link=False)

	return coverage_div

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
				line_color='blue',
				fill='tozeroy',
				fillcolor='violet'
			)
			trace.append(trace1)
		fig = go.Figure(data=trace)
		fig.update_layout(
			showlegend=False,
			xaxis_title = 'degrees',
			yaxis_title = 'degrees',
			yaxis=dict(
				matches='x',
				scaleanchor="x",
				scaleratio=1,
				constrain='domain',
			)
		)
		data = fig
		graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
		return graphJSON
	print(v[0].errors)
	return jsonify("")


@app.route('/pointingfromid')
def get_pointing_fromID():
	args = request.args
	if 'id' in args and function.isInt(args.get('id')):
		#try:
		id = int(args.get('id'))
		pfilter = []
		pfilter.append(models.pointing.submitterid == current_user.get_id())
		pfilter.append(models.pointing.status == models.pointing_status.planned)

		pointings = pointings_from_IDS([id], pfilter)

		if len(pointings) > 0:
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
	
	return 'success'


#Internal Functions

def pointing_crossmatch(pointing, otherpointings, dist_thresh=None):

	if dist_thresh is None:

		filtered_pointings = [x for x in otherpointings if (
			x.status.name == pointing.status and \
			x.instrumentid == int(pointing.instrumentid) and \
			x.band.name == pointing.band and \
			x.time == pointing.time and \
			x.pos_angle == function.floatNone(pointing.pos_angle)
		)]

		for p in filtered_pointings:
			p_pos = str(geoalchemy2.shape.to_shape(p.position))
			if function.sanatize_pointing(p_pos) == function.sanatize_pointing(pointing.position):
				return True

	else:

		p_ra, p_dec = function.sanatize_pointing(pointing.position)

		filtered_pointings = [x for x in otherpointings if (
			x.status.name == pointing.status and \
			x.instrumentid == int(pointing.instrumentid) and \
			x.band.name == pointing.band
		)]

		for p in filtered_pointings:
			ra, dec == function.sanatize_pointing(str(geoalchemy2.shape.to_shape(p.position)))
			sep = 206264.806*(float(ephem.separation((ra, dec ), (p_ra, p_dec))))
			if sep < dist_thresh:
				return True

	return False


def construct_alertform(form, args):

	graceid = args['graceid']
	status = args['pointing_status']
	alerttype = args['alert_type']

	detection_overlays = None
	inst_overlays = None
	GRBoverlays = None
	form.viz = False

	statuses = [
		{'name':'All', 'value':'all'},
		{'name':'Planned+Completed', 'value':'pandc'}
	]
	for m in models.pointing_status:
		statuses.append({'name':m.name, 'value':m.name})
	form.pointing_status = statuses
	form.status = 'all'
	
	#grab all observation alerts
	gwalerts = models.gw_alert.query.filter_by(role='observation').order_by(models.gw_alert.time_of_signal).all()
	gwalerts_ids = sorted(list(set([a.graceid for a in gwalerts])), reverse=True)

	#link all alert types to its graceid
	#we want to be able to label the retracted ones individual for the custom dropdown
	gid_types = {}
	for g in gwalerts_ids:
		types = [x.alert_type for x in gwalerts if x.graceid == g]
		gid_types[g] = types

	#form the custom dropdown dictionary
	graceids = [{'name':'--Select--', 'value':None}]

	for g in gwalerts_ids:
		if g != 'TEST_EVENT':
		#get the alert types for each graceid to test for retractions
			g_types = gid_types[g]

			if 'Retraction' in g_types:
				graceids.append({'name':g + ' -retracted-', 'value':g})
			else:
				graceids.append({'name':g, 'value':g})

	graceids.append({'name':'TEST_EVENT', 'value':'TEST_EVENT'})
	form.graceids = graceids

	#if there is a selected graceid
	if graceid != 'None' and graceid is not None:

		form.graceid = graceid

		#Here we get the relevant alert type information

		alert_info = db.session.query(models.gw_alert).filter(models.gw_alert.graceid == graceid).order_by(models.gw_alert.datecreated.asc()).all()
		#if there is a specificly selected usertype

		#Getting the alert types do display as tabs
		#Also involves logic to handle multiple alert types that are the same
		#Update, Update 1, Update 2...
		alert_types = [x.alert_type for x in alert_info]
		#print(alert_types)
		form.alert_types = []
		for at in alert_types:
			if at in form.alert_types:
				num = len([x for x in form.alert_types if at in x])
				form.alert_types.append(at + ' ' + str(num))
			else:
				form.alert_types.append(at)


		#user selected an alert type?
		if alerttype is not None and alerttype != 'None':
			at = alerttype.split()[0]
			if len(alerttype.split()) > 1:
				itera = int(alerttype.split()[1])
			else:
				itera = 0
			#print(at,itera)
			form.selected_alert_info = [x for x in alert_info if x.alert_type == at][itera]
			form.alert_type = alerttype
		#user did not select an alert type, so get the most recent one
		else: 
			pre_alert = alert_info[len(alert_info)-1]
			num = len([x for x in alert_types if x == pre_alert.alert_type])-1
			form.selected_alert_info = pre_alert
			#make sure to get the correct alert attribute even if it has a number appended to it.. Update, vs Update 1, Update 2...
			form.alert_type = pre_alert.alert_type if num < 1 else pre_alert.alert_type + ' ' + str(num)

		if form.selected_alert_info.far != 0:
			farrate = 1/form.selected_alert_info.far
			farunit = "s"
			if farrate > 86400:
				farunit = "days"
				farrate /= 86400
				if farrate > 365:
					farrate /= 365.25
					farunit = "years"
				elif farrate > 30:
					farrate /= 30
					farunit = "months"
				elif farrate > 7:
					farrate /= 7
					farunit = "weeks"
			form.selected_alert_info.human_far=round(farrate,2)
			form.selected_alert_info.human_far_unit = farunit

		if form.selected_alert_info.distance is not None:
			form.distance = round(form.selected_alert_info.distance,3)
		if form.selected_alert_info.distance_error is not None:
			 form.distance_error = round(form.selected_alert_info.distance_error, 3)

		if form.selected_alert_info.time_of_signal is not None:
			t=astropy.time.Time(form.selected_alert_info.time_of_signal,format='datetime',scale='utc')
			form.selected_alert_info.sun_ra =  astropy.coordinates.get_sun(t).ra.deg
			form.selected_alert_info.sun_dec =  astropy.coordinates.get_sun(t).dec.deg
			form.selected_alert_info.moon_ra =  astropy.coordinates.get_moon(t).ra.deg
			form.selected_alert_info.moon_dec =  astropy.coordinates.get_moon(t).dec.deg

		form.viz = True

		#filter and query for the relevant pointings
		pointing_filter = []
		pointing_filter.append(models.pointing_event.graceid == graceid)
		pointing_filter.append(models.pointing_event.pointingid == models.pointing.id)

		if status == 'pandc':
			ors = []
			ors.append(models.pointing.status == models.pointing_status.completed)
			ors.append(models.pointing.status == models.pointing_status.planned)
			pointing_filter.append(fsq.sqlalchemy.or_(*ors))
			form.status = 'pandc'
		elif (status is not None and status != 'all' and status != ''):
			pointing_filter.append(models.pointing.status == status)
			form.status = status

		pointing_info = db.session.query(
			models.pointing.instrumentid,
			models.pointing.pos_angle,
			models.pointing.time,
			func.ST_AsText(models.pointing.position).label('position'),
			models.pointing.band,
			models.pointing.depth,
			models.pointing.depth_unit,
			models.pointing.status
		).filter(*pointing_filter).all()

		form.band_cov = []
		for band in list(set([x.band.name for x in pointing_info if x.status == models.pointing_status.completed and x.instrumentid != 49])):
			form.band_cov.append({'name':band, 'value':band})

		#grab the pointings instrument ids
		instrumentids = [x.instrumentid for x in pointing_info]

		#filter and query for the relevant instruments
		instrumentinfo = db.session.query(
			models.instrument.instrument_name,
			models.instrument.nickname,
			models.instrument.id
		).filter(
			models.instrument.id.in_(instrumentids)
		).all()

		form.inst_cov = []
		for inst in [x for x in instrumentinfo if x.id != 49]:
			form.inst_cov.append({'name':inst.nickname if inst.nickname != None else inst.instrument_name, 'value':inst.id})
		
		form.depth_unit=[]
		for dp in list(set([x.depth_unit for x in pointing_info if x.status == models.pointing_status.completed and x.instrumentid != 49 and x.depth_unit != None])):
			form.depth_unit.append({'name':str(dp), 'value':dp.name})

		#filter and query the relevant instrument footprints
		footprintinfo = db.session.query(
			func.ST_AsText(models.footprint_ccd.footprint).label('footprint'), 
			models.footprint_ccd.instrumentid
		).filter(
			models.footprint_ccd.instrumentid.in_(instrumentids)
		).all()

		detection_overlays = []
		inst_overlays = []
		GRBoverlays = []
		galaxy_cats = []

		if form.selected_alert_info.time_of_signal:
			tos = form.selected_alert_info.time_of_signal
			t = Time([tos])
			form.tos_mjd = round(t.mjd[0], 2)
		else:
			form.tos_mjd = 0

		#iterate over each instrument and grab their pointings
		#rotate and project the footprint and then add it to the overlay list
		colorlist=['#ffe119', '#4363d8', '#f58231', '#42d4f4', '#f032e6', '#fabebe', '#469990', '#e6beff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9']

		if 'Retraction' not in form.alert_type:
			for i,inst in enumerate([x for x in instrumentinfo if x.id != 49]):
				name = inst.nickname if inst.nickname and inst.nickname != 'None' else inst.instrument_name
				try:
					color = colorlist[i]
				except:
					color = colors[inst.id]
					pass
				footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == inst.id]
				sanatized_ccds = function.sanatize_footprint_ccds(footprint_ccds)
				inst_pointings = [x for x in pointing_info if x.instrumentid == inst.id]
				pointing_geometries = []

				for p in inst_pointings:
					t = Time([p.time])
					ra, dec = function.sanatize_pointing(p.position)
					for ccd in sanatized_ccds:
						pointing_footprint = function.project_footprint(ccd, ra, dec, p.pos_angle)
						pointing_geometries.append({"polygon":pointing_footprint, "time":round(t.mjd[0]-form.tos_mjd, 2)})
				
				inst_overlays.append({
					"display":True,
					"name":name,
					"color":color,
					"contours":pointing_geometries
				})

			#do BAT stuff
			#BAT instrumentid == 49
			# If there are any pointings with BAT. Find the file
			# that should have been created by the BAT listener
			if len([x for x in pointing_info if x.instrumentid == 49]):
				batpathinfo = '/var/www/gwtm/src/static/'+graceid+'-BAT.json'
				if os.path.exists(batpathinfo):
					with open(batpathinfo) as json_data:
						contours_data = json.load(json_data)
					GRBoverlays.append({
						'name':'Swift/BAT',
						'color':'#3cb44b',
						'json':contours_data
					})

			#do Fermi stuff
			if form.selected_alert_info.time_of_signal and graceid != 'TEST_EVENT' and graceid != 'GW170817':
				earth_ra, earth_dec, earth_rad = function.getearthsatpos(form.selected_alert_info.time_of_signal)
				if earth_ra != False:
					#Do GBM stuff
					GBMpathinfo = '/var/www/gwtm/src/static/'+graceid+ '-Fermi.json'
					if os.path.exists(GBMpathinfo):
						with open(GBMpathinfo) as json_data:
							contours_data = json.load(json_data)
						GRBoverlays.append({
							'name':'Fermi/GBM',
							'color':'magenta',
							'json':contours_data
						})
					#Do LAT stuff
					LATpathinfo = '/var/www/gwtm/src/static/'+graceid+ '-LAT.json'
					print(LATpathinfo)
					if os.path.exists(LATpathinfo):
						with open(LATpathinfo) as json_data:
							contours_data = json.load(json_data)
						GRBoverlays.append({
							'name':'Fermi/LAT',
							'color':'red',
							'json':contours_data
						})
				else:
					GRBoverlays.append({
						'name': 'Fermi in South Atlantic Anomaly'
						})

			#grab the precomputed localization contour region
			if len(form.alert_type.split()) > 1:
				path_info = graceid + '-' + form.alert_type.split()[0] + form.alert_type.split()[1]
				mappath = graceid + '-' + form.alert_type.split()[0] + form.alert_type.split()[1]
			else:
				path_info = graceid + '-' + form.alert_type.split()[0]
				mappath = graceid + '-' + form.alert_type.split()[0]

			mappathinfo = '/var/www/gwtm/src/static/'+mappath+'.fits.gz'

			form.avgra = form.selected_alert_info.avgra
			form.avgdec = form.selected_alert_info.avgdec

			contourpath = '/var/www/gwtm/src/static/'+path_info+'-contours-smooth.json'
			form.mappathinfo = mappathinfo
			#if it exists, add it to the overlay list
			if os.path.exists(contourpath):
				contours_data=pd.read_json(contourpath)
				contour_geometry = []
				for contour in contours_data['features']:
					contour_geometry.extend(contour['geometry']['coordinates'])

				detection_overlays.append({
					"display":True,
					"name":"GW Contour",
					"color": '#e6194B',
					"contours":function.polygons2footprints(contour_geometry, 0)
				})

			if len(inst_overlays):
				times = []
				for o in inst_overlays:
					for c in o['contours']:
						times.append(c['time'])
						
				form.mintime = min(times)
				form.maxtime = max(times)
				form.step = (form.maxtime*100 - form.mintime*100)/100000

			galLists = db.session.query(models.gw_galaxy_list).filter(
				models.gw_galaxy_list.graceid == graceid
			).all()
			galList_ids = list(set([x.id for x in galLists]))

			galEntries = db.session.query(
				models.gw_galaxy_entry.name,
				func.ST_AsText(models.gw_galaxy_entry.position).label('position'),
				models.gw_galaxy_entry.score,
				models.gw_galaxy_entry.info,
				models.gw_galaxy_entry.listid,
			).filter(
				models.gw_galaxy_entry.listid.in_(galList_ids)
			).all()

			for glist in galLists:
				markers = []
				entries = [x for x in galEntries if x.listid == glist.id]
				for e in entries:
					ra, dec = function.sanatize_pointing(e.position)
					markers.append({
						"name":e.name,
						"ra": ra,
						"dec": dec,
						"info":function.sanatize_gal_info(ra, dec, e.score, e.info)
					})
				galaxy_cats.append({
					"name":glist.groupname,
					"markers":markers
				})

	return form, detection_overlays, inst_overlays, GRBoverlays, galaxy_cats

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


def construct_creators(doi_group_id, userid):

	if function.isInt(doi_group_id):
		authors = db.session.query(models.doi_author).filter(
			models.doi_author.author_groupid == int(doi_group_id),
			models.doi_author.author_groupid == models.doi_author_group.id,
			models.doi_author_group.userid == userid
		).order_by(
			models.doi_author.id
		).all()
	else:
		authors = db.session.query(models.doi_author).filter(
			models.doi_author.author_groupid == models.doi_author_group.id,
			models.doi_author_group.name == doi_group_id,
			models.doi_author_group.userid == userid
		).order_by(
			models.doi_author.id
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
	
	print(pointings)
	pointing_returns = {}
	for p in pointings:
		pointing_returns[str(p.id)] = p

	return pointing_returns


def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body = text_body
	msg.html = html_body
	with app.app_context():
		mail.send(msg)


def send_account_validation_email(user):
	send_email(
		"Treasure Map Account Verification",
		"gwtreasuremap@gmail.com",
		[user.email],
		"",
		"<p>Hello "+user.firstname+",<br><br> \
		Thank you for registering for The Gravitational Wave Treasure Map Project! Please follow this <a href=\"http://treasuremap.space/login?verification_key="+user.verification_key+"\">address</a> to verify your account. <br>\
		Please do not reply to this email<br><br> \
		Cheers from the Treasure Map team </p>",
	)
	send_email(
		"Treasure Map Account Verification",
		"gwtreasuremap@gmail.com",
		['swyatt@email.arizona.edu'],
		"",
		"<p>Hey Sam,<br><br> \
		 New GWTM account registration: <br> \
		"+user.firstname+" "+user.lastname+" <br> \
		email: "+user.email+" <br> \
		username: "+user.username+" <br><br> \
		Cheers you beautiful bastard</p>",
	)

def send_password_reset_email(user):
	token = user.get_reset_password_token()
	print(token, user.firstname)
	send_email('GWTM Reset Your Password',
			   "gwtreasuremap@gmail.com",
			   [user.email],
			   "",
			   "<p>Dear "+user.username+",</p> \
				<p>\
				To reset your password \
				<a href=\"http://treasuremap.space/reset_password?token="+token+"&_external=True\"> \
				click here \
				</a>.\
				</p>\
				<p>Alternatively, you can paste the following link in your browser's address bar:</p>\
				<p>http://treasuremap.space/reset_password?token="+token+"&_external=True</p>\
				<p>If you have not requested a password reset simply ignore this message.</p>\
				<p>Sincerely,</p>\
				<p>The Treasure Map Team</p>"
	)

def create_doi(points, graceid, creators, insts):
	
	ACCESS_TOKEN = app.config['ZENODO_ACCESS_KEY']
	points_json = []


	for p in points:
		if p.status == models.pointing_status.completed:
			#p.doi_id = d_id
			points_json.append(p.json)

	if len(insts) > 1:
		inst_str = "These observations were taken on the"
		for i in insts:
			if i == insts[len(insts)-1]:
				inst_str +=  " and " + i
			else:
				inst_str += " " + i + ","
			
		inst_str += " instruments."
	else:
		inst_str = "These observations were taken on the " + insts[0] + " instrument."

	if len(points_json):
		data = {
			"metadata": {
				"title":"Submitted Completed pointings to the Gravitational Wave Treasure Map for event " + graceid,
				"upload_type":"dataset",
				"creators":creators,
				"description":"Attached in a .json file is the completed pointing information for "+str(len(points_json))+" observation(s) for the EM counterpart search associated with the gravitational wave event " + graceid +". " + inst_str
			}
		}

		data_file = { 'name':'completed_pointings_'+graceid+'.json' }
		files = { 'file':io.StringIO(json.dumps(points_json)) }
		headers = { "Content-Type": "application/json" }
		
		r = requests.post('https://zenodo.org/api/deposit/depositions', params={'access_token': ACCESS_TOKEN}, json={}, headers=headers)
		d_id = r.json()['id']
		r = requests.post('https://zenodo.org/api/deposit/depositions/%s/files' % d_id, params={'access_token': ACCESS_TOKEN}, data=data_file, files=files)
		r = requests.put('https://zenodo.org/api/deposit/depositions/%s' % d_id, data=json.dumps(data), params={'access_token': ACCESS_TOKEN}, headers=headers)
		r = requests.post('https://zenodo.org/api/deposit/depositions/%s/actions/publish' % d_id, params={'access_token': ACCESS_TOKEN})
		return_json = r.json()
		return int(d_id), return_json['doi_url']
	
	return None, None

#API Endpoints

#Get instrument footprints
@app.route("/api/v0/footprints", methods=['GET'])
def get_footprints():
	args = request.args

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

	filter = []
	if "id" in args:
		if function.isInt(args['id']):
			inst_id = int(args['id'])
			filter.append(models.footprint_ccd.instrumentid == inst_id)
	if "name" in args:
		filter.append(models.footprint_ccd.instrumentid == models.instrument.id)
		name = args.get('name')
		ors = []
		ors.append(models.instrument.instrument_name.contains(name.strip()))
		ors.append(models.instrument.nickname.contains(name.strip()))
		filter.append(fsq.sqlalchemy.or_(*ors))

	footprints= db.session.query(models.footprint_ccd).filter(*filter).all()
	footprints = [x.json for x in footprints]

	return jsonify(footprints)

@app.route('/api/v0/remove_event_galaxies', methods=['Post'])
def remove_event_galaxies():
	pass

@app.route('/api/v0/event_galaxies', methods=['GET'])
def get_event_galaxies():
	pass

@app.route('/api/v0/event_galaxies', methods=['POST'])
def post_event_galaxies():

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	#How do we want to really do this.
	#I think having separate galaxy catalogs ingested isn't the best idea
	#Why don't we just ingest:
	#	EventGalaxyList
	#		Name,RA,DEC,KWARGS (10000 characters long)


	warnings = []
	errors = []

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

	if "graceid" in args:
		graceid = args['graceid']
	else:
		return jsonify('graceid is required')

	if "groupname" in args:
		groupname = args['groupname']
	else:
		groupname = user.username
		warnings.append("no groupname given. Defaulting to api_token username")
	
	#maybe include the possibility for a different delimiter for alert types as well. Not only graceids
	gw_galist = models.gw_galaxy_list(
		submitterid = user.id,
		graceid = graceid,
		groupname = groupname
	)
	db.session.add(gw_galist)
	db.session.flush()

	valid_galaxies = []

	if "galaxies" in args:
		galaxies = args['galaxies']
		for g in galaxies:
			gw_galentry = models.gw_galaxy_entry()
			v = gw_galentry.from_json(g)
			if v.valid:
				gw_galentry.listid = gw_galist.id
				db.session.add(gw_galentry)
				valid_galaxies.append(gw_galentry)
				if len(v.warnings) > 0:
					warnings.append(["Object: " + json.dumps(g), v.warnings])
			
			else:
				errors.append(["Object: "+json.dumps(g), v.errors])

	else:
		return jsonify("a list of galaxies is required")
	
	db.session.flush()
	db.session.commit()

	return jsonify({"Successful adding of "+str(len(valid_galaxies))+" galaxies for event "+graceid+". List ID":str(gw_galist.id), "ERRORS":errors, "WARNINGS":warnings})
	
#Get Galaxies From glade_2p3
@app.route("/api/v0/glade", methods=['GET'])
def get_galaxies():
	args = request.args

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

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
	post_doi = False

	points = []
	errors = []
	warnings = []

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

	if 'request_doi' in rd:
		post_doi = bool(rd['request_doi'])
		if 'creators' in rd:
			creators = rd['creators']
			for c in creators:
				if 'name' not in c.keys() or 'affiliation' not in c.keys():
					return jsonify('name and affiliation are required for DOI creators json list')
		elif 'doi_group_id' in rd:
				valid, creators = construct_creators(rd['doi_group_id'], userid)
				if not valid:
					return jsonify("Invalid doi_group_id. Make sure you are the User associated with the DOI group")
		else:
			creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]

	dbinsts = db.session.query(models.instrument.instrument_name,
							   models.instrument.id).all()


	filter = [models.pointing.submitterid == userid]

	otherpointings = db.session.query(models.pointing).filter(
		models.pointing.id == models.pointing_event.pointingid,
		models.pointing_event.graceid == gid
	).all()

	if "pointing" in rd:
		p = rd['pointing']
		mp = models.pointing()
		if 'id' in p:
			if function.isInt(p['id']):
				planned_pointings = pointings_from_IDS([p['id']], filter)
		v = mp.from_json(p, dbinsts, userid, planned_pointings, otherpointings)
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
			v = mp.from_json(p, dbinsts, userid, planned_pointings, otherpointings)
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

	if post_doi:
		insts = db.session.query(models.instrument).filter(models.instrument.id.in_([x.instrumentid for x in points]))
		inst_set = list(set([x.instrument_name for x in insts]))
		doi_id, doi_url = create_doi(points, gid, creators, inst_set)
		if doi_id is not None:
			for p in points:
				p.doi_url = doi_url
				p.doi_id = doi_id

			db.session.flush()
			db.session.commit()

			return jsonify({"pointing_ids":[x.id for x in points], "ERRORS":errors, "WARNINGS":warnings, "DOI":doi_url})
			

	return jsonify({"pointing_ids":[x.id for x in points], "ERRORS":errors, "WARNINGS":warnings})


#Get Pointing/s
#Parameters: List of ID/s, type/s, group/s, user/s, and/or time/s constraints (to be AND’ed). 
#Returns: List of PlannedPointing JSON objects
@app.route("/api/v0/pointings", methods=["GET"])
def get_pointings():

	args = request.args

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

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
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == models.pointing_status.completed)
		filter.append(models.pointing.time >= time)

	if "completed_before" in args:
		time = args.get('completed_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == models.pointing_status.completed)
		filter.append(models.pointing.time <= time)

	if "planned_after" in args:
		time = args.get('planned_after')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == models.pointing_status.planned)
		filter.append(models.pointing.time >= time)

	if "planned_before" in args:
		time = args.get('planned_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
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

@app.route("/api/v0/request_doi", methods=['POST'])
def api_request_doi():
	
	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
		else:
			userid = user.id
	else:
		return jsonify("api_token is required")
	
	if 'creators' in args:
		creators = args['creators']
		for c in creators:
			if 'name' not in c.keys() or 'affiliation' not in c.keys():
				return jsonify('name and affiliation are required for DOI creators json list')
	elif 'doi_group_id' in rd:
		valid, creators = construct_creators(rd['doi_group_id'], userid)
		if not valid:
			return jsonify("Invalid doi_group_id. Make sure you are the User associated with the DOI group")
	else:
		creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]

	filter=[]

	if "graceid" in args:
		graceid = args.get('graceid')
		filter.append(models.pointing_event.graceid == graceid)
		filter.append(models.pointing_event.pointingid == models.pointing.id)

	if "id" in args:
		_id = args.get('id')
		if function.isInt(_id):
			filter.append(models.pointing.id == int(_id))
		else:
			return jsonify("Invalid ID")
	elif "ids" in args:
		try:
			ids = json.loads(args.get('ids'))
			filter.append(models.pointing.id.in_(ids))
		except:
			return jsonify('Invalid list format of IDs')

	if len(filter) == 0:
		return jsonify("Insufficient filter parameters")

	points = db.session.query(models.pointing).filter(*filter).all()

	gids, doi_points, warnings = [], [], []

	for p in points:
		if p.status == models.pointing_status.completed and p.submitterid == user.id and p.doi_id == None:
			doi_points.append(p)
		else:
			warnings.append("Invalid doi request for pointing: " + str(p.id))

	if len(doi_points) == 0:
		return jsonify("No pointings to give DOI")

	insts = db.session.query(models.instrument).filter(models.instrument.id.in_([x.instrumentid for x in doi_points]))
	inst_set = list(set([x.instrument_name for x in insts]))

	gids = list(set([x.graceid for x in db.session.query(models.pointing_event).filter(models.pointing_event.pointingid.in_([x.id for x in doi_points]))]))
	if len(gids) > 1:
		return jsonify("Pointings must be only for a single GW event")

	gid = gids[0]

	print(len(points), gid, creators)
	doi_id, doi_url = create_doi(points, gid, creators, inst_set)

	if doi_id is not None:
		for p in doi_points:
			p.doi_url = doi_url
			p.doi_id = doi_id

		db.session.flush()
		db.session.commit()
	
	return jsonify({"DOI URL":doi_url, "WARNINGS":warnings})
	

@app.route("/api/v0/cancel_all", methods=["POST"])
def cancel_all():
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

	filter1 = []
	filter1.append(models.pointing.status == models.pointing_status.planned)
	filter1.append(models.pointing.submitterid == userid)

	if "graceid" in args:
		graceid = args['graceid']
		filter1.append(models.pointing_event.graceid == graceid)
		filter1.append(models.pointing.id == models.pointing_event.pointingid)
	else:
		return jsonify("graceid is required")
	
	if "instrumentid" in args:
		instid = args['instrumentid']
		if function.isInt(instid):
			filter1.append(models.pointing.instrumentid == instid)
		else:
			return jsonify('invalid instrumentid')
	else:
		return jsonify('instrumentid is required')

	pointings = db.session.query(models.pointing).filter(*filter1)
	for p in pointings:
		setattr(p, 'status', models.pointing_status.cancelled)
		setattr(p, 'dateupdated', datetime.datetime.now())

	db.session.commit()
	return jsonify("Updated "+str(len(pointings.all()))+" Pointings successfully")

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
	try:
		if "id" in args:
			filter1.append(models.pointing.id == int(args.get('id')))
		elif "ids" in args:
			filter1.append(models.pointing.id.in_(json.loads(args.get('ids'))))
		else:
			return jsonify('id or ids of pointing event is required')
	except:
		return jsonify('There was a problem reading your list of ids')

	if len(filter1) > 0:
		pointings = db.session.query(models.pointing).filter(*filter1)
		for p in pointings:
			if status == 'cancelled':
				setattr(p, 'status', models.pointing_status.cancelled)
				setattr(p, 'dateupdated', datetime.datetime.now())
		db.session.commit()

		return jsonify("Updated "+str(len(pointings))+" Pointings successfully")

	else:
		return jsonify("Please Don't update the ENTIRE POINTING table")


#Get Instrument/s
#Parameters: List of ID/s, type/s (to be AND’ed).
#Returns: List of Instrument JSON objects
@app.route("/api/v0/instruments", methods=["GET"])
def get_instruments():

	args = request.args

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

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
