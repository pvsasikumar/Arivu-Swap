from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/')
@login_required
def index():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications/index.html', notifs=notifs)
