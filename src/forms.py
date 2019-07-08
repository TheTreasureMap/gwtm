from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, widgets
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from . import models

db = models.db

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
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

    bands = [(m.name, m.name) for m in models.bandpass]
    bands.append(('all', 'All'))
    #band_choices = SelectMultipleField('Bandpasses', choices=bands, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    band_choices = SelectMultipleField('Bandpasses', choices=bands)

    statuses = [(m.name, m.name) for m in models.pointing_status]
    statuses.append(('all', 'All'))
    status_choices = SelectField('Status', choices=statuses)


    submit = SubmitField('Search')

    def populate_graceids(self):
        alerts = models.gw_alert.query.filter_by(role='observation').all()
        alerts = list(set([a.graceid for a in alerts]))
        self.graceids.choices = [(a, a) for a in alerts]


class SearchInstrumentsForm(FlaskForm):
    type_choices = [(m.name, m.name) for m in models.instrument_type]
    type_choices.append(('all', 'All'))
    types = SelectField('Instrument Types', choices=type_choices, default='all')
    name = StringField('Instrument Name')
    submit = SubmitField('Search')