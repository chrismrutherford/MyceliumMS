from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    experiments = db.relationship('Experiment', backref='researcher', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class CultivationMedium(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # petri, grow_bag, liquid_culture
    status = db.Column(db.String(50), nullable=False)  # clean, in_use, contaminated, decontaminating, sterilizing
    status_changed = db.Column(db.DateTime, default=datetime.utcnow)
    experiments = db.relationship('Experiment', backref='medium', lazy=True)
    vessels = db.relationship('CultureVessel', backref='medium_type', lazy=True)

class CultureVessel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)
    medium_id = db.Column(db.Integer, db.ForeignKey('cultivation_medium.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='OK')  # OK, In Use, Compromised, Contaminated, Breached, Non-viable, Decommissioned, Defunct, Unevacuated
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    experiments = db.relationship('Experiment', backref='culture_vessel', lazy=True)

class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), nullable=False, default='active')  # active, completed, terminated
    
    # Medium details
    medium_id = db.Column(db.Integer, db.ForeignKey('cultivation_medium.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('culture_vessel.id'), unique=True, info={'unique_name': 'uix_experiment_vessel_id'})
    substrate_composition = db.Column(db.Text)
    
    # Inoculation details
    inoculation_method = db.Column(db.String(100))
    inoculation_source_type = db.Column(db.String(50))  # wild_specimen, commercial_culture, previous_experiment
    inoculation_date = db.Column(db.DateTime)
    geographic_origin = db.Column(db.String(200))
    supplier_info = db.Column(db.String(200))
    strain_info = db.Column(db.String(200))
    
    # Environmental conditions
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light_exposure = db.Column(db.String(100))
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    entries = db.relationship('ExperimentEntry', backref='experiment', lazy=True)
    children = db.relationship('Experiment', backref=db.backref('parent', remote_side=[id]))
    spawn_prints = db.relationship('SpawnPrint', backref='source_experiment', lazy=True)

class ExperimentEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    entry_type = db.Column(db.String(50), nullable=False)  # observation, analysis, transfer, flushing, spawn_print_collection
    images = db.relationship('Image', backref='entry', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('experiment_entry.id'), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class SpawnPrint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(100), nullable=False)
    collection_date = db.Column(db.DateTime, nullable=False)
    source_experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    storage_location = db.Column(db.String(200))
    status = db.Column(db.String(50), nullable=False)  # viable, used, contaminated
