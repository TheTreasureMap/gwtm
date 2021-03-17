# -*- coding: utf-8 -*-

from flask import request, jsonify
from sqlalchemy import func
import flask_sqlalchemy as fsq
import os, json, datetime
import random, math
import numpy as np
import time

from src import app
from . import function
from . import models
from . import forms
from . import enums

db = models.db

#API Endpoints

#Get instrument footprints
@app.route("/api/v0/footprints", methods=['GET'])
def get_footprints():
	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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
	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")
	
	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

	if "listid" in args:
		listid = args['listid']
		if function.isInt(listid):
			gallist = db.session.query(models.gw_galaxy_list).filter(models.gw_galaxy_list.id==listid).first()
			if gallist is not None:
				if user.id == gallist.submitterid:
					gallist_entries = db.session.query(models.gw_galaxy_entry).filter(models.gw_galaxy_entry.listid == listid)
					db.session.delete(gallist)
					for ge in gallist_entries:
						db.session.delete(ge)
					db.session.commit()
					return(jsonify("Successfully deleted your galaxy list"))
				else:
					return jsonify('you can only delete information related to your api_token! shame shame')
			else:
				return(jsonify('No galaxies with that listid'))
		else:
			return jsonify('Invalid listid')
	else:
		return jsonify('Event galaxy listid is required')


@app.route('/api/v0/event_galaxies', methods=['GET'])
def get_event_galaxies():
	try:
		args = request.get_json()
	except:
		return jsonify("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return jsonify("Invalid Arguments.")
	
	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")
	
	filter = [models.gw_galaxy_entry.listid == models.gw_galaxy_list.id]

	if 'graceid' in args:
		graceid = models.gw_alert.graceidfromalternate(args['graceid'])
		filter.append(models.gw_galaxy_list.graceid == graceid)
	else:
		return jsonify("\'graceid\' is required")

	if "timesent_stamp" in args:
		timesent_stamp = args['timesent_stamp']
		try:
			time = datetime.datetime.strptime(timesent_stamp, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")

		alert = db.session.query(models.gw_alert).filter(
			models.gw_alert.timesent < time + datetime.timedelta(seconds=15), 
			models.gw_alert.timesent > time - datetime.timedelta(seconds=15),
			models.gw_alert.graceid == graceid).first()
		if alert is None:
			return jsonify('Invalid \'timesent_stamp\' for event\n Please visit http://treasuremap.space/alerts?graceids={} for valid timesent stamps for this event'.format(graceid))
		else:
			filter.append(models.gw_galaxy_list.alertid == alert.id)

	if 'listid' in args:
		if function.isInt(args['listid']):
			filter.append(models.gw_galaxy_list.id == int(args['listid']))
		else:
			return jsonify('Invalid \'listid\'')

	if 'groupname' in args:
		filter.append(models.gw_galaxy_list.groupname == args['groupname'])

	if 'score_gt' in args:
		if function.isFloat(args['score_gt']):
			sgt = float(args['score_gt'])
			filter.append(models.gw_galaxy_entry.score >= sgt)
	if 'score_lt' in args:
		if function.isFloat(args['score_lt']):
			slt = float(args['score_lt'])
			filter.append(models.gw_galaxy_entry.score <= slt)

	gal_entries = db.session.query(models.gw_galaxy_entry).filter(*filter).all()
	gal_entries = [x.json for x in gal_entries]

	return jsonify(gal_entries)


@app.route('/api/v0/event_galaxies', methods=['POST'])
def post_event_galaxies():

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	post_doi = False
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
		graceid = models.gw_alert.graceidfromalternate(graceid)
	else:
		return jsonify('graceid is required')

	if "timesent_stamp" in args:
		timesent_stamp = args['timesent_stamp']
		try:
			time = datetime.datetime.strptime(timesent_stamp, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")

		alert = db.session.query(models.gw_alert).filter(
			models.gw_alert.timesent < time + datetime.timedelta(seconds=15), 
			models.gw_alert.timesent > time - datetime.timedelta(seconds=15),
			models.gw_alert.graceid == graceid).first()
		if alert is None:
			return jsonify('Invalid \'timesent_stamp\' for event\n Please visit http://treasuremap.space/alerts?graceids={} for valid timesent stamps for this event'.format(graceid))
	else:
		return jsonify('timesent_stamp is required')

	if "groupname" in args:
		groupname = args['groupname']
	else:
		groupname = user.username
		warnings.append("no groupname given. Defaulting to api_token username")

	reference = None
	if "reference" in args:
		reference = args['reference']

	if 'request_doi' in args:
		post_doi = bool(args['request_doi'])
		if 'creators' in args:
			creators = args['creators']
			for c in creators:
				if 'name' not in c.keys() or 'affiliation' not in c.keys():
					return jsonify('name and affiliation are required for DOI creators json list')
		elif 'doi_group_id' in args:
				valid, creators = models.doi_author.construct_creators(args['doi_group_id'], user.id)
				if not valid:
					return jsonify("Invalid doi_group_id. Make sure you are the User associated with the DOI group")
		else:
			creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]

	#maybe include the possibility for a different delimiter for alert types as well. Not only graceids
	gw_galist = models.gw_galaxy_list(
		submitterid = user.id,
		graceid = graceid,
		alertid = alert.id,
		groupname = groupname,
		reference = reference,
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

	doi_string = '. '

	db.session.flush()
	db.session.commit()

	if post_doi:
		doi_id, url = function.create_galaxy_score_doi(valid_galaxies, creators, reference, graceid, alert.alert_type)
		if doi_url is None and doi_id is not None:
			errors.append('There was an error with the DOI request. Please ensure that author group\'s ORIC/GND values are accurate')
		else:
			gw_galist.doi_id = doi_id
			gw_galist.doi_url = url
			doi_string = ". DOI url: {}.".format(url)

			db.session.flush()
			db.session.commit()

	return jsonify({"Successful adding of "+str(len(valid_galaxies))+" galaxies for event "+graceid+doi_string+" List ID" :str(gw_galist.id), 
					"ERRORS":errors, 
					"WARNINGS":warnings})

#Get Galaxies From glade_2p3
@app.route("/api/v0/glade", methods=['GET'])
def get_galaxies():
	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

	if "api_token" in args:
		apitoken = args['api_token']
		user = db.session.query(models.users).filter(models.users.api_token ==  apitoken).first()
		if user is None:
			return jsonify("invalid api_token")
	else:
		return jsonify("api_token is required")

	filter = []
	filter1 = []
	filter1.append(models.glade_2p3.pgc_number != -1)
	filter1.append(models.glade_2p3.distance > 0)
	filter1.append(models.glade_2p3.distance < 100)
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
		gid = models.gw_alert.graceidfromalternate(gid)
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
				valid, creators = models.doi_author.construct_creators(rd['doi_group_id'], userid)
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
				planned_pointings = models.pointing.pointings_from_IDS([p['id']], filter)
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
		planned_pointings = models.pointing.pointings_from_IDS(planned_ids, filter)

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
		print(inst_set)

		if 'doi_url' in rd:
			doi_id, doi_url = 0, rd['doi_url']
		else:
			gid = models.gw_alert.alternatefromgraceid(gid)
			doi_id, doi_url = function.create_pointing_doi(points, gid, creators, inst_set)

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

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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
		graceid = models.gw_alert.graceidfromalternate(graceid)
		filter.append(models.pointing_event.graceid == graceid)
		filter.append(models.pointing_event.pointingid == models.pointing.id)
	elif 'graceids' in args:
		gids_s = args.get('graceids')
		gids = gids_s.split('[')[1].split(']')[0].split(',')
		print(gids, type(gids))
		filter.append(models.pointing_event.graceid.in_(gids))
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
		for b in enums.bandpass:
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
			statuses.append(enums.pointing_status.planned)
		if "completed" in statuses_sent:
			statuses.append(enums.pointing_status.completed)
		if "cancelled" in statuses_sent:
			statuses.append(enums.pointing_status.cancelled)
		filter.append(models.pointing.status.in_(statuses))

	if "completed_after" in args:
		time = args.get('completed_after')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == enums.pointing_status.completed)
		filter.append(models.pointing.time >= time)

	if "completed_before" in args:
		time = args.get('completed_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == enums.pointing_status.completed)
		filter.append(models.pointing.time <= time)

	if "planned_after" in args:
		time = args.get('planned_after')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == enums.pointing_status.planned)
		filter.append(models.pointing.time >= time)

	if "planned_before" in args:
		time = args.get('planned_before')
		try:
			time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
		except:
			return jsonify("Error parsing date. Should be %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00")
		filter.append(models.pointing.status == enums.pointing_status.planned)
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

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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
	elif 'doi_group_id' in args:
		valid, creators = models.doi_author.construct_creators(args['doi_group_id'], userid)
		if not valid:
			return jsonify("Invalid doi_group_id. Make sure you are the User associated with the DOI group")
	else:
		creators = [{ 'name':str(user.firstname) + ' ' + str(user.lastname) }]

	filter=[]

	if "graceid" in args:
		graceid = args.get('graceid')
		graceid = models.gw_alert.graceidfromalternate(graceid)
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
			ids = args.get('ids')
			filter.append(models.pointing.id.in_(ids))
		except:
			return jsonify('Invalid list format of IDs')

	if len(filter) == 0:
		return jsonify("Insufficient filter parameters")

	points = db.session.query(models.pointing).filter(*filter).all()

	gids, doi_points, warnings = [], [], []

	for p in points:
		if p.status == enums.pointing_status.completed and p.submitterid == user.id and p.doi_id == None:
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

	if 'doi_url' in args:
		doi_id, doi_url = 0, args.get('doi_url')
	else:
		gid = models.gw_alert.alternatefromgraceid(gid)
		doi_id, doi_url = function.create_pointing_doi(points, gid, creators, inst_set)

	if doi_id is not None:
		for p in doi_points:
			p.doi_url = doi_url
			p.doi_id = doi_id

		db.session.flush()
		db.session.commit()

	return jsonify({"DOI URL":doi_url, "WARNINGS":warnings})


@app.route("/api/v0/cancel_all", methods=["POST"])
def cancel_all():

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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
	filter1.append(models.pointing.status == enums.pointing_status.planned)
	filter1.append(models.pointing.submitterid == userid)

	if "graceid" in args:
		graceid = args['graceid']
		graceid = models.gw_alert.graceidfromalternate(graceid)
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
		setattr(p, 'status', enums.pointing_status.cancelled)
		setattr(p, 'dateupdated', datetime.datetime.now())

	db.session.commit()
	return jsonify("Updated "+str(len(pointings.all()))+" Pointings successfully")

#Cancel PlannedPointing
#Parameters: List of IDs of planned pointings for which it is known that they aren’t going to happen
@app.route("/api/v0/update_pointings", methods=["POST"])
def del_pointings():

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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
	filter1.append(models.pointing.status == enums.pointing_status.planned)
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
		itera = 0
		for p in pointings:
			if status == 'cancelled':
				itera = itera + 1
				setattr(p, 'status', enums.pointing_status.cancelled)
				setattr(p, 'dateupdated', datetime.datetime.now())
		db.session.commit()

		return jsonify("Updated "+str(itera)+" Pointings successfully")

	else:
		return jsonify("Please Don't update the ENTIRE POINTING table")


#Get Instrument/s
#Parameters: List of ID/s, type/s (to be AND’ed).
#Returns: List of Instrument JSON objects
@app.route("/api/v0/instruments", methods=["GET"])
def get_instruments():

	try:
		args = request.get_json()
	except:
		return("Whoaaaa that JSON is a little wonky")

	if args is None:
		args = request.args
	
	if args is None:
		return("Invalid Arguments.")

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

#FIX DATA
@app.route('/fixdata', methods=['GET'])
def fixdata():

	#ids = [20815,20816,20817]
	#datatochange = db.session.query(models.pointing).filter(models.pointing.id.in_(ids))

	#i = 1
	#for ge in datatochange:
	#	ge.depth = 6.69E-12
		
	#db.session.commit()

	return 'success'

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
