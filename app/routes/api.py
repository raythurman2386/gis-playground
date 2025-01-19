from flask import Blueprint, jsonify, request, json
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG
from app.database.base import get_db
from app.database import crud

logger = setup_logger(
    "api_routes",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

bp = Blueprint("api", __name__)


@bp.route("/layers")
def get_layers():
    """Get all available layers with their styles"""
    try:
        db = next(get_db())
        layers = crud.get_all_layers(db)
        return jsonify(
            [
                {
                    "id": layer.id,
                    "name": layer.name,
                    "description": layer.description,
                    "geometry_type": layer.geometry_type,
                    "style": json.loads(layer.style) if layer.style else None,
                    "created_at": layer.created_at.isoformat(),
                }
                for layer in layers
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching layers: {e}")
        return jsonify({"error": "Failed to fetch layers"}), 500


@bp.route("/layers/<int:layer_id>")
def get_layer_data(layer_id):
    """Get GeoJSON data for a specific layer"""
    try:
        db = next(get_db())
        features = crud.get_layer_features(db, layer_id)

        if not features:
            return jsonify({"error": "No features found"}), 404

        try:
            from app.database.utils import features_to_geojson
            geojson = features_to_geojson(features)
            return jsonify(geojson)
        except Exception as e:
            logger.error(f"Error converting features to GeoJSON: {e}")
            return jsonify({"error": "Error processing feature data"}), 500

    except Exception as e:
        logger.error(f"Error fetching layer {layer_id}: {e}")
        return jsonify({"error": f"Failed to fetch layer {layer_id}"}), 500


@bp.route("/layers/<int:layer_id>/style", methods=["PUT"])
def update_layer_style(layer_id):
    """Update layer style settings"""
    try:
        style_data = request.json
        db = next(get_db())
        crud.update_layer_style(db, layer_id, style_data)
        return jsonify({"message": "Style updated successfully"})
    except Exception as e:
        logger.error(f"Error updating layer style: {e}")
        return jsonify({"error": "Failed to update style"}), 500


@bp.route("/layers/<int:layer_id>", methods=["DELETE"])
def delete_layer(layer_id):
    """Delete a layer"""
    try:
        db = next(get_db())
        crud.delete_layer(db, layer_id)
        return jsonify({"message": "Layer deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting layer: {e}")
        return jsonify({"error": "Failed to delete layer"}), 500
