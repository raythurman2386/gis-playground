from sqlalchemy.orm import Session
from app.models.spatial import SpatialLayer, Feature, LayerAttribute, UploadHistory
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape
from typing import Dict, Any
import json


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
    db: Session, layer_id: int, geometry: Dict[str, Any], properties: Dict[str, Any]
) -> Feature:
    """Add a new feature to a layer"""
    # Convert GeoJSON geometry to WKB
    shp = shape(geometry)
    geom = from_shape(shp, srid=4326)

    db_feature = Feature(
        layer_id=layer_id, geometry=geom, properties=json.dumps(properties)
    )
    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature


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
