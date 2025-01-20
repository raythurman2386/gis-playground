import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import crud
from processors.base_processor import BaseDataProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "csv_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class CSVProcessor(BaseDataProcessor):
    def get_required_files(self) -> Dict[str, str]:
        return {
            "csv": "CSV file with spatial data (must include latitude and longitude columns)"
        }

    def get_file_extensions(self) -> set:
        return {".csv"}

    def validate_files(self, files: Dict[str, Any]) -> bool:
        return "file_csv" in files

    def process_data(
        self,
        files: Dict[str, Any],
        layer_name: str,
        db_session: Session,
        description: str = "",
        lat_column: str = None,
        lon_column: str = None,
    ) -> Dict[str, Any]:
        try:
            # Save CSV file temporarily
            csv_file = files["file_csv"]
            temp_path = self.upload_dir / f"{layer_name}_temp.csv"
            csv_file.save(temp_path)

            try:
                df = pd.read_csv(temp_path)

                # Validate and identify coordinate columns
                lat_col, lon_col = self._identify_coordinate_columns(
                    df, lat_column, lon_column
                )

                if not (lat_col and lon_col):
                    return {
                        "success": False,
                        "error": "Could not identify latitude and longitude columns",
                    }

                # Create GeoDataFrame
                geometry = gpd.points_from_xy(df[lon_col], df[lat_col])
                gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

                # Create the layer
                layer = crud.create_spatial_layer(
                    db=db_session,
                    name=layer_name,
                    description=description,
                    geometry_type="POINT",
                )

                # Process features
                features_added = self._process_features(gdf, layer.id, db_session)

                return {
                    "success": True,
                    "message": "CSV data processed successfully",
                    "layer_id": layer.id,
                    "feature_count": features_added,
                    "total_features": len(gdf),
                    "geometry_type": "POINT",
                    "crs": "EPSG:4326",
                }

            finally:
                # Clean up
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Error processing CSV: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _identify_coordinate_columns(
        self,
        df: pd.DataFrame,
        lat_column: Optional[str] = None,
        lon_column: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Identify latitude and longitude columns in the DataFrame.
        Returns a tuple of (latitude_column, longitude_column)
        """
        # If columns are specified and valid, use them
        if (
            lat_column
            and lon_column
            and lat_column in df.columns
            and lon_column in df.columns
        ):
            return lat_column, lon_column

        # Common names for latitude and longitude columns
        lat_names = ["lat", "latitude", "y", "Latitude", "LAT", "LATITUDE"]
        lon_names = ["lon", "long", "longitude", "x", "Longitude", "LON", "LONGITUDE"]

        # Find latitude column
        lat_col = None
        for name in lat_names:
            if name in df.columns:
                lat_col = name
                break

        # Find longitude column
        lon_col = None
        for name in lon_names:
            if name in df.columns:
                lon_col = name
                break

        return lat_col, lon_col

    def _process_features(
        self, gdf: gpd.GeoDataFrame, layer_id: int, db_session: Session
    ) -> int:
        """Process features from a GeoDataFrame into the database"""
        features_added = 0
        for idx, row in gdf.iterrows():
            try:
                geometry = row.geometry.__geo_interface__

                # Clean properties before storing
                properties = row.drop("geometry").to_dict()
                cleaned_properties = {}

                for key, value in properties.items():
                    if pd.isna(value):  # Check for NaN or None
                        cleaned_properties[key] = None
                    else:
                        cleaned_properties[key] = value

                crud.add_feature(
                    db=db_session,
                    layer_id=layer_id,
                    geometry=geometry,
                    properties=cleaned_properties,
                )
                features_added += 1

            except Exception as e:
                logger.error(f"Error adding feature {idx}: {e}")
                continue

        return features_added
