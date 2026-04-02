from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config
from extensions import db, login_manager, mail, socketio
from datetime import datetime, timezone, timedelta

app = create_app()
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.skills import skills_bp
    from routes.exchange import exchange_bp
    from routes.meeting import meeting_bp
    from routes.chat import chat_bp
    from routes.review import review_bp
    from routes.profile import profile_bp
    from routes.notifications import notifications_bp
    from routes.session import session_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(skills_bp, url_prefix='/skills')
    app.register_blueprint(exchange_bp, url_prefix='/exchange')
    app.register_blueprint(meeting_bp, url_prefix='/meeting')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(review_bp, url_prefix='/review')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(session_bp, url_prefix='/session')

    from routes.matching import matching_bp
    app.register_blueprint(matching_bp, url_prefix='/matching')
    
    from apscheduler.schedulers.background import BackgroundScheduler
    from routes.session import send_reminders

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=send_reminders, trigger='interval', minutes=30, args=[app])
    scheduler.start()

    from routes import main_bp
    app.register_blueprint(main_bp)

    @app.template_filter('timeago')
    def timeago_filter(dt):
        IST = timedelta(hours=5, minutes=30)
        now = datetime.now(timezone.utc) + IST
        local_dt = dt.replace(tzinfo=timezone.utc) + IST
        diff = now - local_dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            return f'{int(seconds // 60)}m ago'
        elif seconds < 86400:
            return f'{int(seconds // 3600)}h ago'
        elif diff.days == 1:
            return 'Yesterday'
        else:
            return local_dt.strftime('%d %b')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)