from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import mapping
import json
from tools.conversion.geometry_converter import convert_to_2d


def feature_to_geojson(feature):
    """Convert a database feature to GeoJSON"""
    # Convert geometry to GeoJSON
    geom = to_shape(feature.geometry)
    geojson_geom = mapping(geom)

    # Parse properties from JSON string
    properties = json.loads(feature.properties)

    return {
        "type": "Feature",
        "geometry": geojson_geom,
        "properties": {"id": feature.id, **properties},
    }


def features_to_geojson(features):
    """Convert multiple features to a GeoJSON FeatureCollection"""
    return {
        "type": "FeatureCollection",
        "features": [feature_to_geojson(f) for f in features],
    }


def prepare_geometry_for_db(geometry):
    """
    Prepare a geometry for database storage by ensuring it's 2D.
    
    Args:
        geometry: Shapely geometry object
        
    Returns:
        WKB representation of the 2D geometry ready for database storage
    """
    # Convert to 2D if necessary
    geometry_2d = convert_to_2d(geometry)
    
    # Convert to WKB format for database storage
    return from_shape(geometry_2d)
