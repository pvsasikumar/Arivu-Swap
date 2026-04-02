from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import ExchangeRequest, Skill
from utils import create_notification

exchange_bp = Blueprint('exchange', __name__)

@exchange_bp.route('/request/<int:skill_id>', methods=['GET', 'POST'])
@login_required
def request_exchange(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    my_skills = Skill.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        er = ExchangeRequest(
            sender_id=current_user.id,
            receiver_id=skill.user_id,
            skill_offered_id=request.form.get('skill_offered'),
            skill_wanted_id=skill_id,
            message=request.form.get('message')
        )
        db.session.add(er)
        db.session.commit()
        create_notification(skill.user_id, f'{current_user.name} wants to exchange skills with you!',
                            url_for('exchange.manage'))
        flash('Exchange request sent!', 'success')
        return redirect(url_for('skills.browse'))
    return render_template('exchange/request.html', skill=skill, my_skills=my_skills)

@exchange_bp.route('/manage')
@login_required
def manage():
    received = ExchangeRequest.query.filter_by(receiver_id=current_user.id).order_by(ExchangeRequest.created_at.desc()).all()
    sent = ExchangeRequest.query.filter_by(sender_id=current_user.id).order_by(ExchangeRequest.created_at.desc()).all()
    return render_template('exchange/manage.html', received=received, sent=sent)

@exchange_bp.route('/respond/<int:req_id>/<action>', methods=['POST'])
@login_required
def respond(req_id, action):
    er = ExchangeRequest.query.get_or_404(req_id)
    if er.receiver_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('exchange.manage'))
    if action in ('accept', 'reject'):
        er.status = 'accepted' if action == 'accept' else 'rejected'
        db.session.commit()
        create_notification(er.sender_id, f'Your exchange request was {er.status}!',
                            url_for('exchange.manage'))
        flash(f'Request {er.status}.', 'success')
    return redirect(url_for('exchange.manage'))
