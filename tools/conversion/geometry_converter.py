from typing import Union
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry.base import BaseGeometry
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "geometry_converter",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

def convert_to_2d(geometry: Union[BaseGeometry, gpd.GeoSeries, gpd.GeoDataFrame]) -> Union[BaseGeometry, gpd.GeoSeries, gpd.GeoDataFrame]:
    """
    Convert 3D geometries to 2D by removing Z coordinates.
    
    Args:
        geometry: Input geometry, can be a Shapely geometry, GeoSeries, or GeoDataFrame
        
    Returns:
        The input geometry converted to 2D
    """
    try:
        if isinstance(geometry, (gpd.GeoDataFrame, gpd.GeoSeries)):
            return geometry.apply(lambda geom: _convert_single_geometry_to_2d(geom))
        else:
            return _convert_single_geometry_to_2d(geometry)
    except Exception as e:
        logger.error(f"Error converting geometry to 2D: {e}")
        raise

def _convert_single_geometry_to_2d(geom: BaseGeometry) -> BaseGeometry:
    """
    Convert a single Shapely geometry from 3D to 2D.
    
    Args:
        geom: Input Shapely geometry
        
    Returns:
        2D version of the input geometry
    """
    if geom is None:
        return None
        
    # Get coordinates based on geometry type
    if isinstance(geom, Point):
        return Point(geom.x, geom.y)
    
    elif isinstance(geom, LineString):
        return LineString([(p[0], p[1]) for p in geom.coords])
    
    elif isinstance(geom, Polygon):
        exterior = [(p[0], p[1]) for p in geom.exterior.coords]
        interiors = [[(p[0], p[1]) for p in interior.coords] 
                    for interior in geom.interiors]
        return Polygon(exterior, interiors)
    
    elif isinstance(geom, MultiPoint):
        return MultiPoint([Point(p.x, p.y) for p in geom.geoms])
    
    elif isinstance(geom, MultiLineString):
        return MultiLineString([LineString([(p[0], p[1]) for p in line.coords]) 
                              for line in geom.geoms])
    
    elif isinstance(geom, MultiPolygon):
        polygons = []
        for poly in geom.geoms:
            exterior = [(p[0], p[1]) for p in poly.exterior.coords]
            interiors = [[(p[0], p[1]) for p in interior.coords] 
                        for interior in poly.interiors]
            polygons.append(Polygon(exterior, interiors))
        return MultiPolygon(polygons)
    
    else:
        logger.warning(f"Unsupported geometry type: {type(geom)}")
        return geom
