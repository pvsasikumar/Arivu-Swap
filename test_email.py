"""
Run this standalone to test your email config.
Usage: python test_email.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Print what we loaded
print("=== CONFIG CHECK ===")
print(f"MAIL_USERNAME : {os.environ.get('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD : {'SET ✓' if os.environ.get('MAIL_PASSWORD') else 'MISSING ✗'}")
print(f"Password length: {len(os.environ.get('MAIL_PASSWORD',''))} chars (should be 16)")
print()

app.config.update(
    MAIL_SERVER   = 'smtp.gmail.com',
    MAIL_PORT     = 587,
    MAIL_USE_TLS  = True,
    MAIL_USE_SSL  = False,
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME'),
)

mail = Mail(app)

with app.app_context():
    try:
        print("=== SENDING TEST EMAIL ===")
        msg = Message(
            subject="SkillSwap Test Email",
            recipients=[os.environ.get('MAIL_USERNAME')],  # send to yourself
            body="If you see this, your email config works!"
        )
        mail.send(msg)
        print("✅ SUCCESS! Check your inbox.")
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        print()
        print("=== COMMON FIXES ===")
        if "Username and Password not accepted" in str(e):
            print("→ App Password is wrong. Re-generate at myaccount.google.com/apppasswords")
            print("→ Make sure you copied all 16 chars with NO spaces in .env")
        elif "534" in str(e):
            print("→ 2FA not enabled. Go to myaccount.google.com/security and enable 2-Step Verification first")
        elif "Connection refused" in str(e) or "timeout" in str(e).lower():
            print("→ Port 587 is blocked. Try changing MAIL_PORT=465 and MAIL_USE_SSL=True, MAIL_USE_TLS=False")
        elif "CERTIFICATE" in str(e).upper():
            print("→ SSL error. Add: MAIL_SSL_CONTEXT='adhoc' or try port 465")
        else:
            print("→ Check your internet connection and firewall settings")
