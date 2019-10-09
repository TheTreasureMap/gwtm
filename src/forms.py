from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, widgets, DateTimeField, IntegerField, DecimalField, TextAreaField, HiddenField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from . import models

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
    graceids = SelectField('Grace ID', validators=[DataRequired()])

    bands = [('all', 'All')]
    for m in models.bandpass:
        bands.append((m.name, m.name))
    #band_choices = SelectMultipleField('Bandpasses', choices=bands, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    band_choices = SelectMultipleField('Bandpasses', choices=bands)

    statuses = [('all', 'All')]
    for m in models.pointing_status:
        statuses.append((m.name, m.name))
    status_choices = SelectField('Status', choices=statuses)

    submit = SubmitField('Search')

    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        alerts = sorted(list(set([a.graceid for a in alerts])))
        self.graceids.choices = [(a, a) for a in alerts]


class SearchInstrumentsForm(FlaskForm):
    type_choices = [('all', 'All')]
    for m in models.instrument_type:
        type_choices.append((m.name, m.name))
    types = SelectField('Instrument Types', choices=type_choices, default='all')
    name = StringField('Instrument Name')
    submit = SubmitField('Search')


class SubmitInstrumentForm(FlaskForm):
    type_choices = [('choose', 'Choose Type')]
    for m in models.instrument_type:
        type_choices.append((m.name, m.name))
    instrument_type = SelectField('Instrument Types', choices=type_choices, default='choose')
    instrument_name = StringField('Name', validators=[DataRequired()])
    instrument_nickname = StringField('Short Name')
    unit = SelectField('Unit', choices=[('choose', 'Choose'), ('deg', 'Degrees'), ('arcmin', 'Arc Minutes'), ('arcsec', 'Arc Seconds')], validators=[DataRequired()])
    footprint_type = SelectField('Footprint Shape', choices=[('choose', 'Choose'), ('Rectangular', 'Rectangular') ,('Circular', 'Circular'), ('Polygon', 'Polygon')], default='choose', validators=[DataRequired()])
    height = DecimalField('Height')
    width = DecimalField('Width')
    radius = DecimalField('Radius')
    polygon = TextAreaField('Polygon', render_kw={"rows": 20, "cols": 11})
    submit =  SubmitField('Submit')


class SubmitPointingForm(FlaskForm):
    graceids = SelectField('Grace ID', validators=[DataRequired()])
    instruments = SelectField('Instrument', validators=[DataRequired()])

    loadid = IntegerField("Planned ID")

    statuses = [(None, 'Select')]
    for a in models.pointing_status:
        if 'cancelled' not in a.name:
            statuses.append((a.name, a.name))
    obs_status = SelectField('Observation Status', choices=statuses, validators=[DataRequired()])
    completed_obs_time = DateTimeField('Completed Time', format='%Y-%m-%dT%H:%M:%S')
    planned_obs_time = DateTimeField('Planned Time', format='%Y-%m-%dT%H:%M:%S')
    bands = [(None, 'Select')]
    for a in models.bandpass:
        bands.append((a.name, a.name))
    obs_bandpass = SelectField('Bandpass', choices=bands, validators=[DataRequired()])
    ra = DecimalField("RA", validators=[DataRequired()])
    dec = DecimalField("DEC", validators=[DataRequired()])

    depth = DecimalField("Depth")
    depth_err = DecimalField("Depth Error")

    dus = [(None, 'Select')]
    for a in models.depth_unit:
        dus.append((str(a.name), str(a.name)))
    depth_unit = SelectField('Depth Unit', choices=dus, validators=[DataRequired()])
    #galaxy_catalogid = IntegerField("Galaxy Catalog")
    #galaxy_id = IntegerField("Galaxy ID")
    pos_angle = DecimalField("Position Angle")

    submit = SubmitField('Submit')

    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        alerts = sorted(list(set([a.graceid for a in alerts])))
        self.graceids.choices = [(None, 'Select')]
        for a in alerts:
            self.graceids.choices.append((a, a))

    def populate_instruments(self):
        query = models.instrument.query.all()
        self.instruments.choices = [(None, 'Select')]
        for a in query:
            self.instruments.choices.append((str(a.id)+"_"+a.instrument_type.name, a.instrument_name))

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
    avgra, avgdec = '', ''