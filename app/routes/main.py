from flask import Blueprint, render_template
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "main_routes",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    logger.debug("Serving index page")
    return render_template("index.html")
