from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import CultivationMedium
from flask_login import login_required
from app import db
from app.models import CultureVessel
from app.forms import CultureVesselForm

vessels = Blueprint('vessels', __name__)

@vessels.route('/vessels', methods=['GET'])
@login_required
def list_vessels():
        
    vessels = CultureVessel.query.all()
    return render_template('vessel/list.html', dishes=vessels)

@vessels.route('/vessels/manage/', defaults={'id': None}, methods=['GET', 'POST'])
@vessels.route('/vessels/manage/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_vessel(id):
    vessel = CultureVessel.query.get_or_404(id) if id else None
    form = CultureVesselForm(obj=vessel)
    form.medium_id.choices = [(m.id, m.type) for m in CultivationMedium.query.all()]
    
    if form.validate_on_submit():
        if vessel is None:
            vessel = CultureVessel(
                label=form.label.data,
                medium_id=form.medium_id.data,
                notes=form.notes.data
            )
            db.session.add(vessel)
            flash('Culture vessel created successfully!', 'success')
        else:
            vessel.label = form.label.data
            vessel.medium_id = form.medium_id.data
            vessel.notes = form.notes.data
            vessel.status = request.form.get('status')
            flash('Culture vessel updated successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('vessels.list_vessels'))
    
    return render_template('vessel/manage.html', form=form, vessel=vessel)

@vessels.route('/vessels/<int:id>/delete', methods=['POST'])
@login_required
def delete_vessel(id):
    vessel = CultureVessel.query.get_or_404(id)
    
    # Check if vessel is assigned to any active experiments
    if any(exp.status == 'active' for exp in vessel.experiments):
        flash('Cannot delete vessel that is assigned to active experiments.', 'danger')
        return redirect(url_for('vessels.list_vessels'))
    
    db.session.delete(vessel)
    db.session.commit()
    flash('Culture vessel deleted successfully!', 'success')
    return redirect(url_for('vessels.list_vessels'))
