import geopandas as gpd
from typing import Tuple
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "geometry_validation",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def validate_and_fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Validate and fix invalid geometries in a GeoDataFrame
    """
    try:
        invalid_geometries = gdf[~gdf.geometry.is_valid]
        if len(invalid_geometries) > 0:
            logger.warning(
                f"Found {len(invalid_geometries)} invalid geometries. Attempting to fix..."
            )
            gdf.geometry = gdf.geometry.buffer(0)
        return gdf
    except Exception as e:
        logger.error(f"Error fixing geometries: {e}")
        raise


def check_geometry_types(gdf: gpd.GeoDataFrame):
    """
    Check geometry types and determine if they're mixed
    """
    try:
        geom_types = gdf.geometry.geom_type.unique()
        if len(geom_types) == 1:
            return geom_types[0].upper()
        return "GEOMETRY"  # Mixed geometry types
    except Exception as e:
        logger.error(f"Error checking geometry types: {e}")
        raise
