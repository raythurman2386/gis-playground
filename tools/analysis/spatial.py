import geopandas as gpd
from typing import Tuple, Dict, Optional
import numpy as np
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "spatial_analysis",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def get_spatial_extent(gdf: gpd.GeoDataFrame) -> Dict[str, float]:
    """
    Get the spatial extent and center of a GeoDataFrame
    """
    try:
        bounds = gdf.total_bounds
        center = [(bounds[0] + bounds[2])/2, (bounds[1] + bounds[3])/2]

        return {
            "bounds": {
                "minx": bounds[0],
                "miny": bounds[1],
                "maxx": bounds[2],
                "maxy": bounds[3]
            },
            "center": {
                "x": center[0],
                "y": center[1]
            }
        }
    except Exception as e:
        logger.error(f"Error calculating spatial extent: {e}")
        raise


def analyze_feature_density(
        gdf: gpd.GeoDataFrame,
        grid_size: Optional[float] = None
) -> Dict:
    """
    Analyze the spatial density of features
    """
    try:
        bounds = gdf.total_bounds
        area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        density = len(gdf) / area if area > 0 else 0

        return {
            "feature_count": len(gdf),
            "total_area": area,
            "density": density,
            "units": "features per square degree"
        }
    except Exception as e:
        logger.error(f"Error analyzing feature density: {e}")
        raise


def calculate_feature_statistics(gdf: gpd.GeoDataFrame) -> Dict:
    """
    Calculate basic spatial statistics for features
    """
    try:
        areas = gdf.geometry.area
        lengths = gdf.geometry.length

        return {
            "area_stats": {
                "min": float(areas.min()),
                "max": float(areas.max()),
                "mean": float(areas.mean()),
                "std": float(areas.std())
            },
            "length_stats": {
                "min": float(lengths.min()),
                "max": float(lengths.max()),
                "mean": float(lengths.mean()),
                "std": float(lengths.std())
            }
        }
    except Exception as e:
        logger.error(f"Error calculating feature statistics: {e}")
        raise