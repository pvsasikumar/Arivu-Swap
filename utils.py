import random, string
from flask_mail import Message as MailMessage
from extensions import mail, db
from models import OTP, Notification
from datetime import datetime, timedelta
from config import Config

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp_code):
    msg = MailMessage(
        subject='Your SkillSwap OTP',
        recipients=[email],
        html=f"""
        <div style="font-family:sans-serif;max-width:480px;margin:auto">
          <h2 style="color:#6c47ff">SkillSwap Verification</h2>
          <p>Your OTP code is:</p>
          <h1 style="letter-spacing:8px;color:#222">{otp_code}</h1>
          <p>Expires in {Config.OTP_EXPIRY_MINUTES} minutes.</p>
        </div>"""
    )
    mail.send(msg)

def save_otp(email, code):
    otp = OTP(email=email, code=code)
    db.session.add(otp)
    db.session.commit()

def verify_otp(email, code):
    expiry = datetime.utcnow() - timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
    otp = OTP.query.filter_by(email=email, code=code, used=False)\
                   .filter(OTP.created_at >= expiry)\
                   .order_by(OTP.created_at.desc()).first()
    if otp:
        otp.used = True
        db.session.commit()
        return True
    return False

def create_notification(user_id, message, link='#'):
    notif = Notification(user_id=user_id, message=message, link=link)
    db.session.add(notif)
    db.session.commit()
