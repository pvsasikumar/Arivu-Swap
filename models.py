from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import secrets

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    google_id = db.Column(db.String(100), unique=True)
    avatar = db.Column(db.String(200), default='default.png')
    bio = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    skills = db.relationship('Skill', backref='owner', lazy=True)
    sent_requests = db.relationship('ExchangeRequest', foreign_keys='ExchangeRequest.sender_id', backref='sender', lazy=True)
    received_requests = db.relationship('ExchangeRequest', foreign_keys='ExchangeRequest.receiver_id', backref='receiver', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    desired_skills = db.relationship('DesiredSkill', backref='user', lazy=True)
    matches_as_a = db.relationship('SkillMatch', foreign_keys='SkillMatch.user_a_id', backref='user_a', lazy=True)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    level = db.Column(db.String(20))  # beginner, intermediate, expert
    wants = db.Column(db.String(200))  # what they want in exchange
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExchangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_offered_id = db.Column(db.Integer, db.ForeignKey('skill.id'))
    skill_wanted_id = db.Column(db.Integer, db.ForeignKey('skill.id'))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100))
    scheduled_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=60)
    meet_link = db.Column(db.String(200))
    status = db.Column(db.String(20), default='upcoming')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), default='text')  # text, file, code, image
    file_url = db.Column(db.String(300))
    file_name = db.Column(db.String(200))
    file_size = db.Column(db.Integer)
    code_lang = db.Column(db.String(30))
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(300))
    link = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

class DesiredSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    level_wanted = db.Column(db.String(20))  # beginner, intermediate, expert
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SkillMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_a_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_b_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_a_id', 'user_b_id'),)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    goals = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    meet_link = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed, cancelled
    reminder_sent = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booker = db.relationship('User', foreign_keys=[booker_id], backref='sessions_booked')
    host = db.relationship('User', foreign_keys=[host_id], backref='sessions_hosted')
    skill = db.relationship('Skill', backref='sessions')

class SessionFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1–5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('Session', backref='feedbacks')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='feedback_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], backref='feedback_received')
