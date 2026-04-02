from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from extensions import db
from models import User, OTP
from utils import generate_otp, send_otp_email, save_otp, verify_otp

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash('Please verify your email first.', 'warning')
                return redirect(url_for('auth.verify_otp_page', email=email))
            login_user(user, remember=True)
            return redirect(url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        otp = generate_otp()
        save_otp(email, otp)
        try:
            send_otp_email(email, otp)
            print(f"✅ OTP email sent to {email}")
        except Exception as e:
            print(f"❌ MAIL ERROR (register): {e}")
        return redirect(url_for('auth.verify_otp_page', email=email))
    return render_template('auth/register.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_page():
    email = request.args.get('email') or request.form.get('email')
    if request.method == 'POST':
        code = request.form.get('otp')
        if verify_otp(email, code):
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                login_user(user)
                return redirect(url_for('dashboard.index'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('auth/verify_otp.html', email=email)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            otp = generate_otp()
            save_otp(email, otp)
            try:
                send_otp_email(email, otp)
                print(f"✅ OTP email sent to {email}")
            except Exception as e:
                print(f"❌ MAIL ERROR (forgot-password): {e}")
            session['reset_email'] = email
            return redirect(url_for('auth.reset_password'))
        flash('Email not found.', 'danger')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        otp = request.form.get('otp')
        password = request.form.get('password')
        if verify_otp(email, otp):
            user = User.query.filter_by(email=email).first()
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            session.pop('reset_email', None)
            flash('Password reset successful.', 'success')
            return redirect(url_for('auth.login'))
        flash('Invalid or expired OTP.', 'danger')
    return render_template('auth/reset_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))