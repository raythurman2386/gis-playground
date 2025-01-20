from flask import Blueprint, request, jsonify, render_template
import os
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG
from app.database.base import get_db
from processors.factory import DataProcessorFactory
from pathlib import Path

logger = setup_logger(
    "upload_routes",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = Path("data/uploads")
REQUIRED_EXTENSIONS = {".shp", ".shx", ".dbf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.route("/shapefile", methods=["POST"])
def upload_shapefile():
    """Upload and process shapefile components"""
    try:
        # Validate request
        layer_name = request.form.get("layer_name")
        if not layer_name:
            return render_template(
                "upload_error.html", error_message="Layer name is required"
            )

        # Get the shapefile processor
        processor = DataProcessorFactory.get_processor("shapefile")

        # Validate files
        if not processor.validate_files(request.files):
            return render_template(
                "upload_error.html", error_message="Missing required files"
            )

        # Process the files
        result = processor.process_data(
            files=request.files,
            layer_name=layer_name,
            db_session=next(get_db()),
            description=request.form.get("description", ""),
        )

        if result["success"]:
            result["layer_name"] = layer_name
            return render_template("upload_success.html", result=result)
        return render_template("upload_error.html", error_message=result["error"])

    except Exception as e:
        logger.error(f"Error in upload process: {e}", exc_info=True)
        return render_template("upload_error.html", error_message=str(e))
