from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
import json


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
