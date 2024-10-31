from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, SelectField, 
                    TextAreaField, FloatField, DateTimeField, FileField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                         validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                           validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                           validators=[DataRequired()])
    submit = SubmitField('Login')

class ExperimentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    medium_id = SelectField('Cultivation Medium', coerce=int, validators=[DataRequired()])
    vessel_id = SelectField('Culture Vessel', coerce=int, validators=[Optional()])
    substrate_composition = TextAreaField('Substrate Composition')
    submit = SubmitField('Create Experiment')

    def __init__(self, *args, **kwargs):
        super(ExperimentForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs and kwargs['obj'] is not None:
            self.submit.label.text = 'Save Experiment'
    
    # Inoculation details
    inoculation_method = StringField('Inoculation Method')
    inoculation_source_type = SelectField('Source Type', 
        choices=[
            ('wild_specimen', 'Wild Specimen'),
            ('commercial_culture', 'Commercial Culture'),
            ('previous_experiment', 'Previous Experiment')
        ])
    inoculation_date = DateTimeField('Inoculation Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    geographic_origin = StringField('Geographic Origin')
    supplier_info = StringField('Supplier Information')
    strain_info = StringField('Strain Information')
    
    # Environmental conditions
    temperature = FloatField('Temperature (°C)', validators=[Optional()])
    humidity = FloatField('Humidity (%)', validators=[Optional()])
    light_exposure = StringField('Light Exposure')
    
    submit = SubmitField('Create Experiment')

class ExperimentEntryForm(FlaskForm):
    content = TextAreaField('Entry Content', validators=[DataRequired()])
    entry_type = SelectField('Entry Type', 
        choices=[
            ('observation', 'Observation'),
            ('analysis', 'Analysis'),
            ('transfer', 'Transfer'),
            ('flushing', 'Flushing'),
            ('spawn_print_collection', 'Spawn Print Collection')
        ],
        validators=[DataRequired()])
    photo = FileField('Photo', validators=[Optional()])
    submit = SubmitField('Add Entry')

class CultureVesselForm(FlaskForm):
    label = StringField('Label', validators=[DataRequired()])
    medium_id = SelectField('Medium Type', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Create Vessel')

    def __init__(self, *args, **kwargs):
        super(CultureVesselForm, self).__init__(*args, **kwargs)
        if 'obj' in kwargs and kwargs['obj'] is not None:
            self.submit.label.text = 'Save Vessel'

class SpawnPrintForm(FlaskForm):
    species = StringField('Species', validators=[DataRequired()])
    storage_location = StringField('Storage Location', validators=[DataRequired()])
    status = SelectField('Status',
        choices=[
            ('viable', 'Viable'),
            ('used', 'Used'),
            ('contaminated', 'Contaminated')
        ],
        validators=[DataRequired()])
    submit = SubmitField('Add Spawn Print')
