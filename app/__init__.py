import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .config import Config

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from . import models  # noqa: F401, ensure models registered
    from .routes import main_bp
    from .auth import auth_bp
    from .api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year}

    with app.app_context():
        charts_path = Path(app.config["CHART_OUTPUT_DIR"])
        charts_path.mkdir(parents=True, exist_ok=True)
        models.seed_assets()
        models.ensure_admin_user()

    return app
