from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Experiment

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    active_experiments = Experiment.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    return render_template('main/index.html', active_experiments=active_experiments)
