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
        # Check if AI name generation is requested
        use_ai_name = request.form.get("use_ai_name") == "on"
        layer_name = request.form.get("layer_name")

        # Only validate layer name if AI name generation is not requested
        if not use_ai_name and not layer_name:
            return render_template(
                "upload_error.html",
                error_message="Layer name is required when not using AI generation",
            )

        # Get the shapefile processor
        processor = DataProcessorFactory.get_processor("shapefile")

        # Validate files
        if not processor.validate_files(request.files):
            return render_template("upload_error.html", error_message="Missing required files")

        # Process the files
        result = processor.process_data(
            files=request.files,
            layer_name=layer_name if not use_ai_name else None,
            db_session=next(get_db()),
            description=request.form.get("description", ""),
        )

        if result["success"]:
            return render_template("upload_success.html", result=result)
        return render_template("upload_error.html", error_message=result["error"])

    except Exception as e:
        logger.error(f"Error in upload process: {e}", exc_info=True)
        return render_template("upload_error.html", error_message=str(e))


@bp.route("/csv", methods=["POST"])
def upload_csv():
    """Upload and process CSV file"""
    try:
        use_ai_name = request.form.get("use_ai_name") == "on"
        layer_name = request.form.get("layer_name")

        if not use_ai_name and not layer_name:
            return render_template(
                "upload_error.html",
                error_message="Layer name is required when not using AI generation",
            )

        processor = DataProcessorFactory.get_processor("csv")
        if not processor.validate_files(request.files):
            return render_template("upload_error.html", error_message="Missing CSV file")

        result = processor.process_data(
            files=request.files,
            layer_name=layer_name if not use_ai_name else None,
            db_session=next(get_db()),
            description=request.form.get("description", ""),
            lat_column=request.form.get("lat_column"),
            lon_column=request.form.get("lon_column"),
        )

        if result["success"]:
            return render_template("upload_success.html", result=result)
        return render_template("upload_error.html", error_message=result["error"])

    except Exception as e:
        logger.error(f"Error in CSV upload process: {e}", exc_info=True)
        return render_template("upload_error.html", error_message=str(e))


@bp.route("/geojson", methods=["POST"])
def upload_geojson():
    """Upload and process GeoJSON file"""
    try:
        use_ai_name = request.form.get("use_ai_name") == "on"
        layer_name = request.form.get("layer_name")

        if not use_ai_name and not layer_name:
            return render_template(
                "upload_error.html",
                error_message="Layer name is required when not using AI generation",
            )

        processor = DataProcessorFactory.get_processor("geojson")
        if not processor.validate_files(request.files):
            return render_template("upload_error.html", error_message="Missing GeoJSON file")

        result = processor.process_data(
            files=request.files,
            layer_name=layer_name if not use_ai_name else None,
            db_session=next(get_db()),
            description=request.form.get("description", ""),
        )

        if result["success"]:
            return render_template("upload_success.html", result=result)
        return render_template("upload_error.html", error_message=result["error"])

    except Exception as e:
        logger.error(f"Error in GeoJSON upload process: {e}", exc_info=True)
        return render_template("upload_error.html", error_message=str(e))


@bp.route("/geopackage", methods=["POST"])
def upload_geopackage():
    """Upload and process GeoPackage file"""
    try:
        use_ai_name = request.form.get("use_ai_name") == "on"
        process_all_layers = request.form.get("process_all_layers") == "on"
        layer_name = request.form.get("layer_name")

        # Only validate layer name if AI name generation is not requested and not processing all layers
        if not use_ai_name and not process_all_layers and not layer_name:
            return render_template(
                "upload_error.html",
                error_message="Layer name is required when not using AI generation or processing all layers",
            )

        processor = DataProcessorFactory.get_processor("geopackage")
        if not processor.validate_files(request.files):
            return render_template("upload_error.html", error_message="Missing GeoPackage file")

        # Get selected layer if not processing all layers
        selected_layer = None if process_all_layers else request.form.get("selected_layer")

        result = processor.process_data(
            files=request.files,
            layer_name=layer_name if not use_ai_name else None,
            db_session=next(get_db()),
            description=request.form.get("description", ""),
            selected_layer=selected_layer,
        )

        if result["success"]:
            return render_template("upload_success.html", result=result)

        # If multiple layers were found and none selected (only when not processing all)
        if not result["success"] and "available_layers" in result and not process_all_layers:
            return render_template(
                "upload_error.html",
                error_message="Please select a layer from the GeoPackage",
                available_layers=result["available_layers"],
            )

        return render_template("upload_error.html", error_message=result["error"])

    except Exception as e:
        logger.error(f"Error in GeoPackage upload process: {e}", exc_info=True)
        return render_template("upload_error.html", error_message=str(e))
