# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from enum import Enum
import os,function, json, datetime

import models
from __init__ import app

db = models.db

#API Endpoints

#Post Pointing/s
#Parameters: List of Pointing JSON objects
#Returns: List of assigned IDs
#Comments: Check if instrument configuration already exists to avoid duplication. 
#Check if pointing is centered at a galaxy in one of the catalogs and if so, associate it.

@app.route("/pointings", methods=["POST"])
def add_pointings():
	rd = request.get_json()
	points = []
	if "pointing" in rd:
		p = rd['pointing']
		mp = models.pointing()
		mp.from_json(p)
		if mp.validate():
			points.append(mp)
			db.session.add(mp)

	elif "pointings" in rd:
		pointings = rd['pointings']
		for p in pointings:
			mp = models.pointing()
			mp.from_json(p)
			if mp.validate():
				points.append(mp)
				db.session.add(mp)

	elif isinstance(rd, (list,)):
		for p in rd:
			mp = models.pointing()
			mp.from_json(p)
			if mp.validate():
				points.append(mp)
				db.session.add(mp)

	else: 
		try:
			mp = models.pointing()
			mp.from_json(rd)
			if mp.validate():
				points.append(mp)
				db.session.add(mp)
		except:
			return jsonify("Whoa slow down, something went wrong")

	db.session.flush()
	db.session.commit()

	return jsonify([x.id for x in points])

#Get Pointing/s
#Parameters: List of ID/s, type/s, group/s, user/s, and/or time/s constraints (to be AND’ed). 
#Returns: List of PlannedPointing JSON objects

@app.route("/pointings", methods=["GET"])
def get_pointings():

	args = request.args

	filter=[]

	if "graceid" in args:
		#validate
		graceid = args.get('graceid')
		filter.append(models.pointing_event.graceid == graceid)
		filter.append(models.pointing_event.pointingid == models.pointing.id)

	if "id" in args:
		#validate
		_id = args.get('id')
		filter.append(models.pointing.id == int(_id))
	elif "ids" in args:
		#validate
		ids = json.loads(args.get('ids'))
		filter.append(models.pointing.id.in_(ids))

	if "status" in args:
		#validate
		status = args.get('status')
		filter.append(models.pointing.status == status)
	elif "statuses" in args:
		#validate
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
			for g in groups:
				filter.append(models.group.name.contains(g))
		filter.append(models.usergroups.userid == models.users.id)
		filter.append(models.users.id == models.pointing.submitterid)

	if "user" in args:
		user = args.get('user')
		if user.isdigit():
			filter.append(models.pointing.submitterid == int(user))
		else:
			filter.append(or_(models.users.username.contains(user),
							  models.users.firstname.contains(user),
							  models.users.lastname.contains(user)))
			filter.append(models.users.id == models.pointing.submitterid)

	elif "users" in args:
		try:
			users = json.loads(args.get('users'))
			filter.append(models.pointing.submitterid.in_(user))
		except:
			users = args.get('users')
			users = users.split('[')[1].split(']')[0].split(',') 
			for u in users:
				filter.append(or_(models.users.username.contains(u.strip()),
							  models.users.firstname.contains(u.strip()),
							  models.users.lastname.contains(u.strip())))
				filter.append(models.users.id == models.pointing.submitterid)
		
	pointings = db.session.query(models.pointing).filter(*filter).all()
	pointings = [x.json for x in pointings]

	return jsonify(pointings)


#Cancel PlannedPointing
#Parameters: List of IDs of planned pointings for which it is known that they aren’t going to happen

@app.route("/pointings", methods=["DELETE"])
def del_pointings():
	args = request.args

	filter = []
	if "id" in args:
		filter.append(models.pointing.id == int(args.get('id')))
	if "ids" in args:
		filter.append(models.pointing.id.in_(json.loads(args.get('ids'))))

	if len(filter) > 0:
		pointings = db.session.query(models.pointing).filter(*filter)
		pointings.delete(synchronize_session=False)
		db.session.commit()

		return jsonify("Deleted Pointings successfully")
	else:
		return jsonify("Please Don't delete the ENTIRE table")


@app.route("/instruments", methods=["POST"])
def post_instruments():
	rd = request.get_json()

	#validate inputs

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

	return inst.id


#Get Instrument/s
#Parameters: List of ID/s, type/s (to be AND’ed).
#Returns: List of Instrument JSON objects

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
		_type = args.get('type')
		filter.append(models.instrument.instrument_type == _type)

	insts = db.session.query(models.instrument).filter(*filter).all()
	insts = [x.json for x in insts]

	return jsonify(insts)

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
