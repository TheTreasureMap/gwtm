from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, widgets, DateTimeField, IntegerField, DecimalField, TextAreaField
from wtforms_components import TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from . import models

db = models.db

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = models.users.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = models.users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


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
        alerts = list(set([a.graceid for a in alerts]))
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
    statuses = [(m.name, m.name) for m in models.pointing_status if 'cancelled' not in m.name]
    obs_status = SelectField('Observation Status', choices=statuses, validators=[DataRequired])
    obs_time = TimeField('Time of Observation', format='%Y-%m-%dT%H:%M:%S')
    bands = [(m.name, m.name) for m in models.bandpass]
    obs_bandpass = SelectField('Bandpass', choices=bands, validators=[DataRequired()])
    depth = DecimalField("Depth", validators=[DataRequired])
    ra = DecimalField("RA", validators=[DataRequired])
    dec = DecimalField("DEC", validators=[DataRequired])
    galaxy_catalogid = IntegerField("Galaxy Catalog")
    galaxy_id = IntegerField("Galaxy ID")
    pos_angle = DecimalField("Position Angle")
    submit = SubmitField('Submit')

    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        alerts = list(set([a.graceid for a in alerts]))
        self.graceids.choices = [(a, a) for a in alerts]

    def populate_instruments(self):
        query = models.instrument.query.all()
        query = list(set([a.instrument_name for a in query]))
        self.instruments.choices = [(a, a) for a in query]