from flask import Blueprint, jsonify
from processors.data_processor import GeoDataProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "api_routes",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

bp = Blueprint("api", __name__)

# Initialize the data processor
data_processor = GeoDataProcessor()
