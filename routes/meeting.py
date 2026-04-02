from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Meeting, User
from utils import create_notification
from datetime import datetime

meeting_bp = Blueprint('meeting', __name__)

@meeting_bp.route('/schedule/<int:user_id>', methods=['GET', 'POST'])
@login_required
def schedule(user_id):
    participant = User.query.get_or_404(user_id)
    if request.method == 'POST':
        scheduled_at = datetime.strptime(request.form['scheduled_at'], '%Y-%m-%dT%H:%M')
        meeting = Meeting(
            organizer_id=current_user.id,
            participant_id=user_id,
            title=request.form['title'],
            scheduled_at=scheduled_at,
            duration_minutes=request.form.get('duration', 60),
            meet_link=request.form.get('meet_link'),
            notes=request.form.get('notes')
        )
        db.session.add(meeting)
        db.session.commit()
        create_notification(user_id, f'{current_user.name} scheduled a meeting with you!',
                            url_for('meeting.my_sessions'))
        flash('Meeting scheduled!', 'success')
        return redirect(url_for('meeting.my_sessions'))
    return render_template('meeting/schedule.html', participant=participant)

@meeting_bp.route('/detail/<int:meeting_id>')
@login_required
def detail(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    return render_template('meeting/detail.html', meeting=meeting)

@meeting_bp.route('/my-sessions')
@login_required
def my_sessions():
    meetings = Meeting.query.filter(
        (Meeting.organizer_id == current_user.id) | (Meeting.participant_id == current_user.id)
    ).order_by(Meeting.scheduled_at.desc()).all()
    return render_template('meeting/my_sessions.html', meetings=meetings)
