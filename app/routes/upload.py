from flask import Blueprint, request, jsonify
import os
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG
from app.database.base import get_db
from processors.data_processor import GeoDataProcessor
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
            return jsonify({"error": "Layer name is required"}), 400

        # Check for required files
        required_files = {}
        for ext in REQUIRED_EXTENSIONS:
            file_key = f"file_{ext[1:]}"
            if file_key not in request.files:
                return jsonify({"error": f"Missing {ext} file"}), 400
            file = request.files[file_key]
            if file.filename == "":
                return jsonify({"error": f"No {ext} file selected"}), 400
            required_files[ext] = file

        # Create temporary directory and save files
        temp_dir = UPLOAD_FOLDER / layer_name
        temp_dir.mkdir(exist_ok=True)
        saved_paths = []

        try:
            # Save files
            for ext, file in required_files.items():
                filepath = temp_dir / f"{layer_name}{ext}"
                file.save(filepath)
                saved_paths.append(filepath)

            # Process shapefile
            processor = GeoDataProcessor()
            db = next(get_db())

            result = processor.process_shapefile(
                shp_path=temp_dir / f"{layer_name}.shp",
                layer_name=layer_name,
                db_session=db,
                description=request.form.get("description", ""),
            )

            if result["success"]:
                return jsonify(result), 201
            return jsonify({"error": result["error"]}), 500

        finally:
            # Clean up
            for path in saved_paths:
                if path.exists():
                    path.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()

    except Exception as e:
        logger.error(f"Error in upload process: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
