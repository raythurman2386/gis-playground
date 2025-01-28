import geopandas as gpd
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "crs_conversion",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def standardize_crs(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """
    Standardize the CRS of a GeoDataFrame to a target CRS
    """
    try:
        if gdf.crs is None:
            logger.warning(f"No CRS found, assuming {target_crs}")
            gdf.set_crs(target_crs, inplace=True)
        elif gdf.crs != target_crs:
            logger.info(f"Converting CRS from {gdf.crs} to {target_crs}")
            gdf = gdf.to_crs(target_crs)
        return gdf
    except Exception as e:
        logger.error(f"Error standardizing CRS: {e}")
        raise


def get_crs_info(gdf: gpd.GeoDataFrame) -> dict:
    """
    Get detailed information about the CRS
    """
    try:
        if gdf.crs is None:
            return {"has_crs": False, "crs": None, "is_geographic": None}

        return {
            "has_crs": True,
            "crs": str(gdf.crs),
            "is_geographic": gdf.crs.is_geographic,
        }
    except Exception as e:
        logger.error(f"Error getting CRS info: {e}")
        raise
