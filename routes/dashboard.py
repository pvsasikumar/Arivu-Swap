from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Skill, ExchangeRequest, Meeting, Notification

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    skills = Skill.query.filter_by(user_id=current_user.id).all()
    pending = ExchangeRequest.query.filter_by(receiver_id=current_user.id, status='pending').count()
    upcoming = Meeting.query.filter(
        (Meeting.organizer_id == current_user.id) | (Meeting.participant_id == current_user.id),
        Meeting.status == 'upcoming'
    ).count()
    return render_template('dashboard/index.html', skills=skills, pending=pending, upcoming=upcoming)
