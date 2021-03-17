import astropy
import pandas as pd
import os
import json
import time

from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, widgets, DateTimeField, IntegerField, DecimalField, TextAreaField, HiddenField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from sqlalchemy import func

from . import function
from . import models
from . import enums

db = models.db

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    verification_key = HiddenField('verification_key')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    fairuse = BooleanField('Fair Use', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = models.users.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = models.users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class ManageUserForm(FlaskForm):
    submit = SubmitField('Search')


class SearchPointingsForm(FlaskForm):
    doi_creator_groups = SelectField('DOI Author Groups')
    graceids = SelectField('Grace ID', validators=[DataRequired()])

    bands = [('all', 'All')]
    for m in enums.bandpass:
        bands.append((m.name, m.name))
    #band_choices = SelectMultipleField('Bandpasses', choices=bands, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    band_choices = SelectMultipleField('Bandpasses', choices=bands)

    statuses = [('all', 'All')]
    for m in enums.pointing_status:
        statuses.append((m.name, m.name))
    status_choices = SelectField('Status', choices=statuses)
    my_points = BooleanField('Show Only My Pointings')
    doi_url = StringField('DOI URL')
    
    submit = SubmitField('Search')

    def populate_creator_groups(self, current_userid):
        dag = models.doi_author_group.query.filter_by(userid=current_userid).all()
        self.doi_creator_groups.choices = [('None', 'None')]
        for a in dag:
            self.doi_creator_groups.choices.append((a.id, a.name))
            
    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        sortalerts = sorted(list(set([a.graceid for a in alerts if "TEST" not in a.graceid])), reverse=True)
        listalerts = []
        for a in sortalerts:
            alternateid = [aid.alternateid for aid in alerts if aid.graceid == a and aid.alternateid is not None]
            if len(alternateid):
                a = alternateid[0]
                listalerts.append((a, a))
            else:
                listalerts.append((a, a))
        listalerts.append(('TEST_EVENT', 'TEST_EVENT'))
        self.graceids.choices = listalerts


class SearchInstrumentsForm(FlaskForm):
    type_choices = [('all', 'All')]
    for m in enums.instrument_type:
        type_choices.append((m.name, m.name))
    types = SelectField('Instrument Types', choices=type_choices, default='all')
    name = StringField('Instrument Name')
    submit = SubmitField('Search')


class SubmitInstrumentForm(FlaskForm):
    type_choices = [('choose', 'Choose Type')]
    for m in enums.instrument_type:
        type_choices.append((m.name, m.name))
    instrument_type = SelectField('Instrument Types', choices=type_choices, default='choose')
    instrument_name = StringField('Name', validators=[DataRequired()])
    instrument_nickname = StringField('Short Name')
    unit = SelectField('Unit', choices=[('choose', 'Choose'), ('deg', 'Degrees'), ('arcmin', 'Arc Minutes'), ('arcsec', 'Arc Seconds')], validators=[DataRequired()])
    footprint_type = SelectField('Footprint Shape', choices=[('choose', 'Choose'), ('Rectangular', 'Rectangular') ,('Circular', 'Circular'), ('Polygon', 'Polygon')], default='choose', validators=[DataRequired()])
    height = DecimalField('Height')
    width = DecimalField('Width')
    radius = DecimalField('Radius')
    polygon = TextAreaField('Polygon', render_kw={"rows": 20, "cols": 20})
    submit =  SubmitField('Submit')


class SubmitPointingForm(FlaskForm):
    graceids = SelectField('Grace ID', validators=[DataRequired()])
    instruments = SelectField('Instrument', validators=[DataRequired()])

    loadid = IntegerField("Planned ID")

    statuses = [(None, 'Select')]
    for a in enums.pointing_status:
        if 'cancelled' not in a.name:
            statuses.append((a.name, a.name))
    obs_status = SelectField('Observation Status', choices=statuses, validators=[DataRequired()])
    completed_obs_time = DateTimeField('Completed Time', format='%Y-%m-%dT%H:%M:%S.%f')
    planned_obs_time = DateTimeField('Planned Time', format='%Y-%m-%dT%H:%M:%S.%f')
    bands = [(None, 'Select')]
    for a in enums.bandpass:
        bands.append((a.name, a.name))
    obs_bandpass = SelectField('Bandpass', choices=bands, validators=[DataRequired()])
    ra = DecimalField("RA", validators=[DataRequired()])
    dec = DecimalField("DEC", validators=[DataRequired()])

    depth = DecimalField("Depth")
    depth_err = DecimalField("Depth Error")

    dus = [(None, 'Select')]
    for a in enums.depth_unit:
        dus.append((str(a.name), str(a.name)))
    depth_unit = SelectField('Depth Unit', choices=dus, validators=[DataRequired()])
    pos_angle = DecimalField("Position Angle")
    request_doi = BooleanField('Request DOI')

    doi_creator_groups = SelectField('DOI Author Groups')
    doi_url = StringField('DOI URL')
    submit = SubmitField('Submit')

    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        sortalerts = sorted(list(set([a.graceid for a in alerts if "TEST" not in a.graceid])), reverse=True)
        listalerts = []
        for a in sortalerts:
            alternateid = [aid.alternateid for aid in alerts if aid.graceid == a and aid.alternateid is not None]
            if len(alternateid):
                a = alternateid[0]
                listalerts.append((a, a))
            else:
                listalerts.append((a, a))
        listalerts.append(('TEST_EVENT', 'TEST_EVENT'))
        self.graceids.choices = [(None, 'Select')]
        for a in listalerts:
            self.graceids.choices.append(a)

    def populate_instruments(self):
        query = models.instrument.query.all()
        self.instruments.choices = [(None, 'Select')]
        for a in query:
            self.instruments.choices.append((str(a.id)+"_"+a.instrument_type.name, a.instrument_name))
        
    def populate_creator_groups(self, current_userid):
        dag = models.doi_author_group.query.filter_by(userid=current_userid).all()
        self.doi_creator_groups.choices = [('None', 'None')]
        for a in dag:
            self.doi_creator_groups.choices.append((a.id, a.name))

class AlertsForm(FlaskForm):
    page = ''
    pointing_status = []
    status =''
    graceids = []
    graceid = ''
    viz = False
    contours = []
    alert_type = None
    alert_types = []
    selected_alert = None
    distance = None
    distance_error = None
    avgra, avgdec = '', ''

    def construct_alertform(self, args):

        graceid = args['graceid']

        detection_overlays = None
        inst_overlays = None
        GRBoverlays = None
        galaxy_cats = None
        self.viz = False

        statuses = [
            {'name':'All', 'value':'all'},
            {'name':'Planned+Completed', 'value':'pandc'}
        ]
        for m in enums.pointing_status:
            statuses.append({'name':m.name, 'value':m.name})
        self.pointing_status = statuses
        self.status = 'all'

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
                alternateid = [gw.alternateid for gw in gwalerts if gw.graceid == g and (gw.alternateid != '' and gw.alternateid is not None)]
                if len(alternateid):
                    g = alternateid[0]
                if 'Retraction' in g_types:
                    graceids.append({'name':g + ' -retracted-', 'value':g})
                else:
                    graceids.append({'name':g, 'value':g})

        graceids.append({'name':'TEST_EVENT', 'value':'TEST_EVENT'})
        self.graceids = graceids

        #if there is a selected graceid
        if graceid != 'None' and graceid is not None:

            t_start = time.time()
            #preserve the forms graceid
            self.graceid = graceid

            #if there has been an updated event's name: confirmed GW event
            alertsfromalternate = [gwa for gwa in gwalerts if gwa.alternateid == graceid]
            if len(alertsfromalternate):
                graceid = alertsfromalternate[0].graceid

            #Here we get the relevant alert type information

            alert_info = db.session.query(
                models.gw_alert
            ).filter(
                models.gw_alert.graceid == graceid
            ).order_by(
                models.gw_alert.datecreated.asc()
            ).all()
            #if there is a specificly selected usertype

            #Getting the alert types do display as tabs
            #Also involves logic to handle multiple alert types that are the same
            #Update, Update 1, Update 2...
            alert_types = [x.alert_type for x in alert_info]
            self.alert_type_tabs = []
            for at in alert_info:
                typetabs = [x['type'] for x in self.alert_type_tabs]
                if at.alert_type in typetabs:
                    num = len([x for x in typetabs if at.alert_type in x])
                    self.alert_type_tabs.append({
                        'type': at.alert_type + ' ' + str(num),
                        'timesent':at.timesent,
                        'urlid':'{}_{}_{}'.format(at.id, at.alert_type, str(num))
                    })
                else:
                    self.alert_type_tabs.append({
                        'type': at.alert_type,
                        'timesent':at.timesent,
                        'urlid':'{}_{}'.format(at.id, at.alert_type)
                    })

            cleaned_alert_info = [alert for alert in alert_info if alert.alert_type != 'Retraction']
            if len(cleaned_alert_info):
                pre_alert = cleaned_alert_info[len(cleaned_alert_info)-1]
            else:
                pre_alert = alert_info[0]
            num = len([x for x in alert_types if x == pre_alert.alert_type])-1
            self.selected_alert_info = pre_alert

            #make sure to get the correct alert attribute even if it has a number appended to it.. Update, vs Update 1, Update 2...
            self.alert_type = pre_alert.alert_type if num < 1 else pre_alert.alert_type + ' ' + str(num)

            if self.selected_alert_info.far != 0:
                farrate = 1/self.selected_alert_info.far
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
                self.selected_alert_info.human_far=round(farrate,2)
                self.selected_alert_info.human_far_unit = farunit

            if self.selected_alert_info.distance is not None:
                self.distance = round(self.selected_alert_info.distance,3)
            if self.selected_alert_info.distance_error is not None:
                self.distance_error = round(self.selected_alert_info.distance_error, 3)

            if self.selected_alert_info.time_of_signal is not None:
                t=astropy.time.Time(self.selected_alert_info.time_of_signal,format='datetime',scale='utc')
                self.selected_alert_info.sun_ra =  astropy.coordinates.get_sun(t).ra.deg
                self.selected_alert_info.sun_dec =  astropy.coordinates.get_sun(t).dec.deg
                self.selected_alert_info.moon_ra =  astropy.coordinates.get_moon(t).ra.deg
                self.selected_alert_info.moon_dec =  astropy.coordinates.get_moon(t).dec.deg

            self.viz = True

            #filter and query for the relevant pointings
            pointing_filter = []
            pointing_filter.append(models.pointing_event.graceid == graceid)
            pointing_filter.append(models.pointing_event.pointingid == models.pointing.id)
            pointing_filter.append(models.pointing.status == enums.pointing_status.completed)

            pointing_info = db.session.query(
                models.pointing.instrumentid,
                #models.pointing.pos_angle,
                models.pointing.time,
                #func.ST_AsText(models.pointing.position).label('position'),
                models.pointing.band,
                models.pointing.depth,
                models.pointing.depth_unit,
                models.pointing.status
            ).filter(*pointing_filter).all()

            self.band_cov = []
            for band in list(set([x.band.name for x in pointing_info if x.status == enums.pointing_status.completed and x.instrumentid != 49])):
                self.band_cov.append({'name':band, 'value':band})

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

            self.inst_cov = []
            for inst in [x for x in instrumentinfo if x.id != 49]:
                self.inst_cov.append({'name':inst.nickname if inst.nickname != None else inst.instrument_name, 'value':inst.id})

            self.depth_unit=[]
            for dp in list(set([x.depth_unit for x in pointing_info if x.status == enums.pointing_status.completed and x.instrumentid != 49 and x.depth_unit != None])):
                self.depth_unit.append({'name':str(dp), 'value':dp.name})

            detection_overlays = []
            GRBoverlays = []

            if self.selected_alert_info.time_of_signal:
                tos = self.selected_alert_info.time_of_signal
                t = astropy.time.Time([tos])
                self.tos_mjd = round(t.mjd[0], 3)
            else:
                self.tos_mjd = 0

            if len(pointing_info):
                times = []
                for p in pointing_info:
                    t = astropy.time.Time([p.time])
                    times.append(round(t.mjd[0]-self.tos_mjd, 3))

                self.mintime = min(times)
                self.maxtime = max(times)
                self.step = (self.maxtime*100 - self.mintime*100)/100000

            #iterate over each instrument and grab their pointings
            #rotate and project the footprint and then add it to the overlay list
            
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
            if self.selected_alert_info.time_of_signal and graceid != 'TEST_EVENT' and graceid != 'GW170817':
                #earth_ra, earth_dec, earth_rad = getearthsatpos(form.selected_alert_info.time_of_signal)
                #if earth_ra != False:
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
                else:
                    GRBoverlays.append({
                        'name': 'Fermi in South Atlantic Anomaly'
                        })
                #Do LAT stuff
                LATpathinfo = '/var/www/gwtm/src/static/'+graceid+ '-LAT.json'
                if os.path.exists(LATpathinfo):
                    with open(LATpathinfo) as json_data:
                        contours_data = json.load(json_data)
                    GRBoverlays.append({
                        'name':'Fermi/LAT',
                        'color':'red',
                        'json':contours_data
                    })

            #grab the precomputed localization contour region
            if len(self.alert_type.split()) > 1:
                path_info = graceid + '-' + self.alert_type.split()[0] + self.alert_type.split()[1]
                mappath = graceid + '-' + self.alert_type.split()[0] + self.alert_type.split()[1]
            else:
                path_info = graceid + '-' + self.alert_type.split()[0]
                mappath = graceid + '-' + self.alert_type.split()[0]

            mappathinfo = '/var/www/gwtm/src/static/'+mappath+'.fits.gz'
            self.avgra = self.selected_alert_info.avgra
            self.avgdec = self.selected_alert_info.avgdec

            contourpath = '/var/www/gwtm/src/static/'+path_info+'-contours-smooth.json'
            self.mappathinfo = mappathinfo
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


            #galLists = db.session.query(models.gw_galaxy_list).filter(
            #    models.gw_galaxy_list.graceid == graceid,
            #    models.gw_galaxy_list.alertid == self.selected_alert_info.id,
            #).all()
            #galList_ids = list(set([x.id for x in galLists]))

            #galEntries = db.session.query(
            #    models.gw_galaxy_entry.name,
            #    func.ST_AsText(models.gw_galaxy_entry.position).label('position'),
            #    models.gw_galaxy_entry.score,
            #    models.gw_galaxy_entry.info,
            #    models.gw_galaxy_entry.listid,
            #    models.gw_galaxy_entry.rank,
            #).filter(
            #    models.gw_galaxy_entry.listid.in_(galList_ids)
            #).all()

            #for glist in galLists:
            #    markers = []
            #    entries = [x for x in galEntries if x.listid == glist.id]
            #    for e in entries:
            #        ra, dec = function.sanatize_pointing(e.position)
            #        markers.append({
            #            "name":e.name,
            #            "ra": ra,
            #            "dec": dec,
            #            "info":function.sanatize_gal_info(e, glist)
            #        })
            #    galaxy_cats.append({
            #        "name":glist.groupname,
            #        "markers":markers
            #    })
            t_stop = time.time()
            print("Time loading page: ", t_stop-t_start) 
        return self, detection_overlays, inst_overlays, GRBoverlays, galaxy_cats