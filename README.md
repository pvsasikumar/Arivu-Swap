# SkillSwap 🔄

A peer-to-peer skill exchange platform built with Flask.

## Features
- OTP-based email verification
- Skill listing & browsing with search/filter
- Exchange requests (accept/decline)
- Real-time chat with Socket.IO
- Meeting scheduler with video link support
- User profiles with reviews & ratings
- Notification system
- Dashboard with stats

## Setup

```bash
# 1. Clone / extract the project
cd skillswap

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your SMTP credentials and secret key

# 5. Run the app
python app.py
```

Open http://localhost:5000 in your browser.

## Project Structure
```
skillswap/
├── app.py              # App factory & entry point
├── config.py           # Configuration
├── extensions.py       # Flask extensions
├── models.py           # Database models
├── utils.py            # OTP, email, notification helpers
├── routes/             # Blueprints
│   ├── auth.py         # Login, register, OTP, password reset
│   ├── dashboard.py
│   ├── skills.py
│   ├── exchange.py
│   ├── meeting.py
│   ├── chat.py         # Real-time chat via Socket.IO
│   ├── review.py
│   ├── profile.py
│   ├── notifications.py
│   └── session.py
├── templates/          # Jinja2 HTML templates
└── static/             # CSS, JS, images
```
