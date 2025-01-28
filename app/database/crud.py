from sqlalchemy.orm import Session
from app.models.spatial import SpatialLayer, Feature, LayerAttribute, UploadHistory
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from typing import Dict, Any, Optional
import json
from .utils import prepare_geometry_for_db


def create_spatial_layer(
    db: Session, name: str, description: str, geometry_type: str
) -> SpatialLayer:
    """Create a new spatial layer"""
    db_layer = SpatialLayer(
        name=name, description=description, geometry_type=geometry_type
    )
    db.add(db_layer)
    db.commit()
    db.refresh(db_layer)
    return db_layer


def add_feature(
    db: Session, layer_id: int, geometry: dict, properties: dict
) -> Feature:
    """Add a new feature to a layer"""
    try:
        # Convert GeoJSON geometry to Shapely and ensure it's 2D
        shp = shape(geometry)
        geom = prepare_geometry_for_db(shp)

        # Ensure properties can be serialized to JSON
        cleaned_properties = json.dumps(properties, default=lambda x: None)

        db_feature = Feature(
            layer_id=layer_id, geometry=geom, properties=cleaned_properties
        )
        db.add(db_feature)
        db.commit()
        db.refresh(db_feature)
        return db_feature
    except Exception as e:
        db.rollback()
        raise e


def get_layer_by_name(db: Session, name: str) -> SpatialLayer:
    """Get a layer by name"""
    return db.query(SpatialLayer).filter(SpatialLayer.name == name).first()


def get_layer_features(db: Session, layer_id: int) -> list[Feature]:
    """Get all features for a layer"""
    return db.query(Feature).filter(Feature.layer_id == layer_id).all()


def get_all_layers(db: Session) -> list[SpatialLayer]:
    """Get all spatial layers"""
    return db.query(SpatialLayer).all()


def get_layer_by_id(db: Session, layer_id: int) -> SpatialLayer:
    """Get a layer by ID"""
    return db.query(SpatialLayer).filter(SpatialLayer.id == layer_id).first()


def update_layer_style(db: Session, layer_id: int, style_data: Dict[str, Any]) -> bool:
    """
    Update the style settings for a layer

    Args:
        db: Database session
        layer_id: ID of the layer to update
        style_data: Dictionary containing style properties

    Returns:
        Boolean indicating success
    """
    try:
        layer = db.query(SpatialLayer).filter(SpatialLayer.id == layer_id).first()
        if not layer:
            return False

        # Store style data in the layer's metadata
        if not hasattr(layer, "style"):
            layer.style = {}

        # Update style properties
        layer.style = json.dumps(style_data)

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e


def delete_layer(db: Session, layer_id: int) -> bool:
    """
    Delete a layer and all its associated features

    Args:
        db: Database session
        layer_id: ID of the layer to delete

    Returns:
        Boolean indicating success
    """
    try:
        # Delete associated features first
        db.query(Feature).filter(Feature.layer_id == layer_id).delete()

        # Delete layer attributes
        db.query(LayerAttribute).filter(LayerAttribute.layer_id == layer_id).delete()

        # Delete upload history
        db.query(UploadHistory).filter(UploadHistory.layer_id == layer_id).delete()

        # Delete the layer itself
        layer = db.query(SpatialLayer).filter(SpatialLayer.id == layer_id).first()
        if layer:
            db.delete(layer)

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e


def get_layer_style(db: Session, layer_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the style settings for a layer

    Args:
        db: Database session
        layer_id: ID of the layer

    Returns:
        Dictionary containing style properties or None if not found
    """
    try:
        layer = db.query(SpatialLayer).filter(SpatialLayer.id == layer_id).first()
        if layer and layer.style:
            return json.loads(layer.style)
        return None
    except Exception as e:
        raise e
