from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Session, SessionFeedback, User, Skill
from utils import create_notification
from datetime import datetime, timedelta

session_bp = Blueprint('session', __name__)


# ─── LIST: my sessions ───────────────────────────────────────────────────────

@session_bp.route('/')
@login_required
def my_sessions():
    booked = Session.query.filter_by(booker_id=current_user.id)\
                .order_by(Session.scheduled_at.desc()).all()
    hosted = Session.query.filter_by(host_id=current_user.id)\
                .order_by(Session.scheduled_at.desc()).all()
    return render_template('session/my_sessions.html', booked=booked, hosted=hosted)


# ─── BOOK: create new session ────────────────────────────────────────────────

@session_bp.route('/book/<int:host_id>', methods=['GET', 'POST'])
@login_required
def book(host_id):
    if host_id == current_user.id:
        flash('You cannot book a session with yourself.', 'danger')
        return redirect(url_for('session.my_sessions'))

    host = User.query.get_or_404(host_id)
    host_skills = Skill.query.filter_by(user_id=host_id).all()

    if request.method == 'POST':
        try:
            scheduled_at = datetime.strptime(
                request.form['scheduled_at'], '%Y-%m-%dT%H:%M'
            )
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(request.url)

        if scheduled_at < datetime.utcnow():
            flash('Cannot book a session in the past.', 'danger')
            return redirect(request.url)

        session = Session(
            booker_id=current_user.id,
            host_id=host_id,
            skill_id=request.form.get('skill_id') or None,
            title=request.form['title'],
            goals=request.form.get('goals'),
            scheduled_at=scheduled_at,
            duration_minutes=int(request.form.get('duration', 60)),
            meet_link=request.form.get('meet_link'),
            notes=request.form.get('notes'),
        )
        db.session.add(session)
        db.session.commit()

        create_notification(
            host_id,
            f'{current_user.name} wants to book a session with you: "{session.title}"',
            url_for('session.detail', session_id=session.id)
        )
        flash('Session request sent!', 'success')
        return redirect(url_for('session.my_sessions'))

    return render_template('session/book.html', host=host, host_skills=host_skills)


# ─── DETAIL: view one session ────────────────────────────────────────────────

@session_bp.route('/<int:session_id>')
@login_required
def detail(session_id):
    s = Session.query.get_or_404(session_id)
    if current_user.id not in (s.booker_id, s.host_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('session.my_sessions'))

    already_reviewed = SessionFeedback.query.filter_by(
        session_id=session_id,
        reviewer_id=current_user.id
    ).first()

    return render_template('session/detail.html',
                           s=s,
                           already_reviewed=already_reviewed)


# ─── ACCEPT ──────────────────────────────────────────────────────────────────

@session_bp.route('/<int:session_id>/accept', methods=['POST'])
@login_required
def accept(session_id):
    s = Session.query.get_or_404(session_id)
    if s.host_id != current_user.id:
        flash('Not authorized.', 'danger')
        return redirect(url_for('session.my_sessions'))

    s.status = 'accepted'
    db.session.commit()

    create_notification(
        s.booker_id,
        f'{current_user.name} accepted your session: "{s.title}"',
        url_for('session.detail', session_id=s.id)
    )
    flash('Session accepted!', 'success')
    return redirect(url_for('session.detail', session_id=s.id))


# ─── CANCEL ──────────────────────────────────────────────────────────────────

@session_bp.route('/<int:session_id>/cancel', methods=['POST'])
@login_required
def cancel(session_id):
    s = Session.query.get_or_404(session_id)
    if current_user.id not in (s.booker_id, s.host_id):
        flash('Not authorized.', 'danger')
        return redirect(url_for('session.my_sessions'))

    if s.status == 'completed':
        flash('Cannot cancel a completed session.', 'danger')
        return redirect(url_for('session.detail', session_id=s.id))

    s.status = 'cancelled'
    db.session.commit()

    notify_id = s.host_id if current_user.id == s.booker_id else s.booker_id
    create_notification(
        notify_id,
        f'{current_user.name} cancelled the session: "{s.title}"',
        url_for('session.my_sessions')
    )
    flash('Session cancelled.', 'warning')
    return redirect(url_for('session.my_sessions'))


# ─── COMPLETE ────────────────────────────────────────────────────────────────

@session_bp.route('/<int:session_id>/complete', methods=['POST'])
@login_required
def complete(session_id):
    s = Session.query.get_or_404(session_id)
    if s.host_id != current_user.id:
        flash('Only the host can mark a session complete.', 'danger')
        return redirect(url_for('session.detail', session_id=s.id))

    s.status = 'completed'
    db.session.commit()

    create_notification(
        s.booker_id,
        f'Your session "{s.title}" has been marked complete. Leave feedback!',
        url_for('session.feedback', session_id=s.id)
    )
    flash('Session marked as completed!', 'success')
    return redirect(url_for('session.feedback', session_id=s.id))


# ─── FEEDBACK ────────────────────────────────────────────────────────────────

@session_bp.route('/<int:session_id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(session_id):
    s = Session.query.get_or_404(session_id)
    if current_user.id not in (s.booker_id, s.host_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('session.my_sessions'))

    if s.status != 'completed':
        flash('Feedback is only available after the session is completed.', 'warning')
        return redirect(url_for('session.detail', session_id=s.id))

    already = SessionFeedback.query.filter_by(
        session_id=session_id,
        reviewer_id=current_user.id
    ).first()
    if already:
        flash('You have already submitted feedback.', 'info')
        return redirect(url_for('session.detail', session_id=s.id))

    if request.method == 'POST':
        reviewee_id = s.host_id if current_user.id == s.booker_id else s.booker_id
        fb = SessionFeedback(
            session_id=session_id,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            rating=int(request.form['rating']),
            comment=request.form.get('comment')
        )
        db.session.add(fb)
        db.session.commit()
        flash('Feedback submitted, thanks!', 'success')
        return redirect(url_for('session.detail', session_id=s.id))

    return render_template('session/feedback.html', s=s)


# ─── REMINDER LOGIC (call via cron or APScheduler) ───────────────────────────

def send_reminders(app):
    with app.app_context():
        now = datetime.utcnow()
        soon = now + timedelta(hours=1)
        upcoming = Session.query.filter(
            Session.status == 'accepted',
            Session.reminder_sent == False,
            Session.scheduled_at >= now,
            Session.scheduled_at <= soon
        ).all()

        for s in upcoming:
            create_notification(
                s.booker_id,
                f'Reminder: your session "{s.title}" starts in less than 1 hour!',
                url_for('session.detail', session_id=s.id)
            )
            create_notification(
                s.host_id,
                f'Reminder: your session "{s.title}" starts in less than 1 hour!',
                url_for('session.detail', session_id=s.id)
            )
            s.reminder_sent = True

        db.session.commit()


# ─── API ─────────────────────────────────────────────────────────────────────

@session_bp.route('/api/my')
@login_required
def api_my_sessions():
    sessions = Session.query.filter(
        (Session.booker_id == current_user.id) |
        (Session.host_id == current_user.id)
    ).order_by(Session.scheduled_at).all()

    return jsonify([{
        'id':           s.id,
        'title':        s.title,
        'status':       s.status,
        'scheduled_at': s.scheduled_at.isoformat(),
        'duration':     s.duration_minutes,
        'booker':       s.booker.name,
        'host':         s.host.name,
        'meet_link':    s.meet_link,
    } for s in sessions])

def google_calendar_link(session):
    from urllib.parse import urlencode
    from datetime import timedelta
    params = {
        'action': 'TEMPLATE',
        'text': session.title,
        'dates': session.scheduled_at.strftime('%Y%m%dT%H%M%S') + '/' +
                 (session.scheduled_at + timedelta(minutes=session.duration_minutes)).strftime('%Y%m%dT%H%M%S'),
        'details': session.goals or '',
        'location': session.meet_link or '',
    }
    return 'https://calendar.google.com/calendar/render?' + urlencode(params)