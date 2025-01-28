from flask import Flask
from config.logging_config import CURRENT_LOGGING_CONFIG
from utils.logger import setup_logger
from app.database.base import check_tables_exist

logger = setup_logger(
    "flask_app",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def create_app():
    app = Flask(__name__)

    if not check_tables_exist():
        logger.error(
            "Database tables do not exist. Please run 'python manage.py init' to initialize the database."
        )
        raise RuntimeError(
            "Database tables do not exist. Please run 'python manage.py init' to initialize the database."
        )

    # Register blueprints
    from app.routes import main, api, upload

    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp, url_prefix="/api")
    app.register_blueprint(upload.bp, url_prefix="/api/upload")

    logger.info("Flask application initialized")
    return app
