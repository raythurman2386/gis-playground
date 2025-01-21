import pandas as pd
import geopandas as gpd
from typing import Dict, List
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "attribute_validation",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def validate_attribute_types(gdf: gpd.GeoDataFrame) -> Dict:
    """
    Validate attribute types and identify potential issues
    """
    try:
        issues = {}
        for col in gdf.columns:
            if col != "geometry":
                # Check for mixed types
                actual_type = gdf[col].dtype
                unique_types = set(type(x) for x in gdf[col].dropna())

                if len(unique_types) > 1:
                    issues[col] = {
                        "issue": "mixed_types",
                        "declared_type": str(actual_type),
                        "found_types": [str(t) for t in unique_types],
                    }

        return {"has_issues": len(issues) > 0, "issues": issues}
    except Exception as e:
        logger.error(f"Error validating attribute types: {e}")
        raise


def check_attribute_completeness(gdf: gpd.GeoDataFrame) -> Dict:
    """
    Check completeness of attributes
    """
    try:
        completeness = {}
        for col in gdf.columns:
            if col != "geometry":
                null_count = gdf[col].isnull().sum()
                completeness[col] = {
                    "total_rows": len(gdf),
                    "null_count": int(null_count),
                    "completeness_ratio": float((len(gdf) - null_count) / len(gdf)),
                }

        return completeness
    except Exception as e:
        logger.error(f"Error checking attribute completeness: {e}")
        raise
