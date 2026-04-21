import os
from datetime import timedelta
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import db, User, SiteSettings

login_manager = LoginManager()


def _add_column_if_missing(table, column, col_type):
    from sqlalchemy import text, inspect
    insp = inspect(db.engine)
    try:
        columns = [c['name'] for c in insp.get_columns(table)]
    except Exception:
        return
    if column not in columns:
        db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
        db.session.commit()


def create_app():
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # Data dir — overridable via DATA_DIR for hosts that require a separate
    # persistent volume (Fly.io, PythonAnywhere). Default: ./data
    data_dir = os.environ.get('DATA_DIR') or os.path.join(base_dir, 'data')
    upload_dir = os.environ.get('UPLOAD_DIR') or os.path.join(base_dir, 'static', 'uploads', 'photos')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bayt-sahour-list-2026-dev-only')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL')
        or f"sqlite:///{os.path.join(data_dir, 'site.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB uploads
    app.config['UPLOAD_DIR'] = upload_dir
    app.config['DATA_DIR'] = data_dir

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.public import public_bp
    from routes.admin import admin_bp
    from routes.meetings import meetings_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(meetings_bp, url_prefix='/meetings')

    @app.context_processor
    def inject_settings():
        settings = SiteSettings.query.first()
        return {'site': settings}

    @app.route('/')
    def index():
        return redirect(url_for('public.home'))

    with app.app_context():
        os.makedirs(app.config['DATA_DIR'], exist_ok=True)
        os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
        db.create_all()
        _seed_all()

    return app


def _seed_all():
    from seed import (seed_settings, seed_admin, seed_candidates,
                      seed_program, seed_priorities, seed_faq)
    seed_settings()
    seed_admin()
    seed_candidates()
    seed_program()
    seed_priorities()
    seed_faq()


# WSGI entry point for gunicorn / PythonAnywhere.
# gunicorn app:app   OR   wsgi.py imports `application` below.
app = create_app()
application = app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
