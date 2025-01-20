from flask import Blueprint, render_template

from processors.factory import DataProcessorFactory
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


@bp.route("/upload", methods=["GET"])
def upload_form():
    """Render the upload form"""
    supported_types = DataProcessorFactory.get_supported_types()
    return render_template("upload.html", supported_types=supported_types)
