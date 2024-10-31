from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import db
from app.models import Experiment, CultivationMedium, ExperimentEntry, CultureVessel, Image
from app.forms import ExperimentForm, ExperimentEntryForm

experiments = Blueprint('experiments', __name__)

@experiments.route('/experiments')
@login_required
def list_experiments():
    experiments = Experiment.query.filter_by(user_id=current_user.id).all()
    return render_template('experiments/list.html', experiments=experiments)

@experiments.route('/experiments/manage/', defaults={'id': None}, methods=['GET', 'POST'])
@experiments.route('/experiments/manage/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_experiment(id):
    experiment = Experiment.query.get_or_404(id) if id else None
    form = ExperimentForm(obj=experiment)
    
    # Get available clean media for the dropdown
    form.medium_id.choices = [(m.id, f"{m.type} - {m.status}") 
                            for m in CultivationMedium.query.filter_by(status='clean').all()]
    
    # Get available culture vessels for the dropdown
    available_vessels = CultureVessel.query\
        .outerjoin(Experiment, CultureVessel.id == Experiment.vessel_id)\
        .filter(
            (CultureVessel.status == 'OK') &  # Only vessels with OK status
            ((Experiment.vessel_id.is_(None)) |  # That are not assigned to any experiment
             (Experiment.id == id))  # Or assigned to this experiment if editing
        ).all()
    form.vessel_id.choices = [(0, 'None')] + [(v.id, f"{v.medium_type.type} - {v.label}") 
                                for v in available_vessels]
    
    if form.validate_on_submit():
        if form.vessel_id.data != 0:
            existing_experiment = Experiment.query.filter(
                Experiment.vessel_id == form.vessel_id.data,
                Experiment.id != (id if id else None)
            ).first()
            if existing_experiment:
                flash('This vessel is already assigned to another experiment.', 'danger')
                return render_template('experiments/manage.html', form=form, experiment=experiment)

        if experiment is None:
            experiment = Experiment(user_id=current_user.id)
            db.session.add(experiment)
            flash_message = 'Experiment created successfully!'
        else:
            flash_message = 'Experiment updated successfully!'

        # Update experiment attributes
        experiment.title = form.title.data
        experiment.medium_id = form.medium_id.data
        experiment.vessel_id = form.vessel_id.data if form.vessel_id.data != 0 else None
        experiment.substrate_composition = form.substrate_composition.data
        experiment.inoculation_method = form.inoculation_method.data
        experiment.inoculation_source_type = form.inoculation_source_type.data
        experiment.inoculation_date = form.inoculation_date.data
        experiment.geographic_origin = form.geographic_origin.data
        experiment.supplier_info = form.supplier_info.data
        experiment.strain_info = form.strain_info.data
        experiment.temperature = form.temperature.data
        experiment.humidity = form.humidity.data
        experiment.light_exposure = form.light_exposure.data

        # Update vessel status if assigned
        if form.vessel_id.data != 0:
            vessel = CultureVessel.query.get(form.vessel_id.data)
            vessel.status = 'In Use'

        try:
            db.session.commit()
            flash(flash_message, 'success')
            return redirect(url_for('experiments.view_experiment', id=experiment.id))
        except Exception as e:
            db.session.rollback()
            flash('Error saving experiment. Please try again.', 'danger')
    
    return render_template('experiments/manage.html', form=form, experiment=experiment)

@experiments.route('/experiments/<int:id>', methods=['GET', 'POST'])
@login_required
def view_experiment(id):
    experiment = Experiment.query.get_or_404(id)
    entries = ExperimentEntry.query.filter_by(experiment_id=id).order_by(ExperimentEntry.entry_date.desc()).all()
    if request.method == 'POST':
        if 'end_experiment' in request.form:
            experiment.status = 'completed'
            experiment.end_date = datetime.utcnow()
            if experiment.vessel_id:
                vessel = CultureVessel.query.get(experiment.vessel_id)
                vessel.status = 'Unevacuated'  # Mark vessel as needing evacuation
                experiment.vessel_id = None  # De-allocate the vessel
            db.session.commit()
            flash('Experiment marked as completed', 'success')
            return redirect(url_for('experiments.list_experiments'))
        elif 'update_vessel_status' in request.form:
            if experiment.vessel_id:
                vessel = CultureVessel.query.get(experiment.vessel_id)
                new_status = request.form.get('vessel_status')
                if new_status in ['OK', 'Compromised', 'Contaminated', 'Breached', 'Non-viable', 'Decommissioned', 'Defunct']:
                    vessel.status = new_status
                    db.session.commit()
                    flash(f'Vessel status updated to {new_status}', 'success')
            return redirect(url_for('experiments.view_experiment', id=id))
    form = ExperimentForm()  # Create an empty form for CSRF token
    return render_template('experiments/view.html', experiment=experiment, entries=entries, form=form)

@experiments.route('/experiments/<int:id>/entry/new', methods=['GET', 'POST'])
@login_required
def add_entry(id):
    experiment = Experiment.query.get_or_404(id)
    form = ExperimentEntryForm()
    
    if form.validate_on_submit():
        entry = ExperimentEntry(
            experiment_id=id,
            content=form.content.data,
            entry_type=form.entry_type.data
        )
        db.session.add(entry)
        db.session.commit()

        if form.photo.data:
            photo = form.photo.data
            filename = secure_filename(f"entry_{entry.id}_{photo.filename}")
            photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
            image = Image(filename=filename, entry_id=entry.id)
            db.session.add(image)
            db.session.commit()
        flash('Entry added successfully!', 'success')
        return redirect(url_for('experiments.view_experiment', id=id))
    
    return render_template('experiments/add_entry.html', form=form, experiment=experiment)

@experiments.route('/experiments/<int:id>/delete', methods=['POST'])
@login_required
def delete_experiment(id):
    experiment = Experiment.query.get_or_404(id)
    if experiment.user_id != current_user.id:
        flash('You do not have permission to delete this experiment.', 'danger')
        return redirect(url_for('experiments.list_experiments'))
    
    if experiment.status != 'completed':
        flash('Only completed experiments can be deleted.', 'danger')
        return redirect(url_for('experiments.list_experiments'))
    
    # Delete associated entries and images first
    for entry in experiment.entries:
        for image in entry.images:
            # Delete image file
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
            except OSError:
                pass
            db.session.delete(image)
        db.session.delete(entry)
    
    db.session.delete(experiment)
    db.session.commit()
    flash('Experiment deleted successfully.', 'success')
    return redirect(url_for('experiments.list_experiments'))
