import geopandas as gpd
from typing import Dict, Any, Union
import pandas as pd
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import crud
from processors.base_processor import BaseDataProcessor
from tools.ai.smart_processor import SmartProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG
import json

logger = setup_logger(
    "geojson_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class GeoJSONProcessor(BaseDataProcessor):
    def __init__(self, upload_dir: str = "data/uploads"):
        super().__init__(upload_dir)
        self.smart_processor = SmartProcessor()

    def get_required_files(self) -> Dict[str, str]:
        return {"geojson": "GeoJSON file containing spatial features"}

    def get_file_extensions(self) -> set:
        return {".geojson", ".json"}

    def validate_files(self, files: Dict[str, Any]) -> bool:
        return "file_geojson" in files

    def process_data(
        self,
        files: Dict[str, Any],
        layer_name: str,
        db_session: Session,
        description: str = "",
        selected_layer: str = None,
    ) -> Dict[str, Any]:
        try:
            # Save GeoJSON file temporarily
            geojson_file = files["file_geojson"]
            temp_path = self.upload_dir / f"{layer_name}_temp.geojson"
            geojson_file.save(temp_path)

            try:
                # Validate GeoJSON structure
                with open(temp_path, "r") as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "error": f"Invalid JSON format: {str(e)}",
                        }

                # Read GeoJSON file
                logger.info(f"Reading GeoJSON from: {temp_path}")
                gdf = self._load_and_standardize_geodataframe(temp_path)

                # Determine geometry type
                geometry_type = self._get_geometry_type(gdf)

                # AI Analysis
                ai_analysis = self.smart_processor.analyze_dataset(gdf, layer_name)

                # Use AI-suggested name and description if not provided
                if not layer_name and ai_analysis.get("suggested_name"):
                    layer_name = ai_analysis["suggested_name"]

                if not description and ai_analysis.get("suggested_description"):
                    description = ai_analysis["suggested_description"]

                # Create the layer
                layer = crud.create_spatial_layer(
                    db=db_session,
                    name=layer_name,
                    description=description,
                    geometry_type=geometry_type,
                )

                # Process features
                features_added = self._process_features(gdf, layer.id, db_session)

                return {
                    "success": True,
                    "message": "GeoJSON processed successfully",
                    "layer_id": layer.id,
                    "feature_count": features_added,
                    "total_features": len(gdf),
                    "geometry_type": geometry_type,
                    "crs": str(gdf.crs),
                    "ai_analysis": {
                        "data_quality": ai_analysis.get("data_quality"),
                        "clusters": ai_analysis.get("clusters"),
                    },
                }

            finally:
                # Clean up
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Error processing GeoJSON: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _load_and_standardize_geodataframe(
        self, file_path: Union[str, Path]
    ) -> gpd.GeoDataFrame:
        """Load and standardize a GeoDataFrame from a GeoJSON file"""
        gdf = gpd.read_file(file_path)

        # Handle CRS
        if gdf.crs is None:
            logger.warning("No CRS found, assuming WGS84 (EPSG:4326)")
            gdf.set_crs(epsg=4326, inplace=True)
        elif gdf.crs != "EPSG:4326":
            logger.info(f"Converting CRS from {gdf.crs} to EPSG:4326")
            gdf = gdf.to_crs(epsg=4326)

        # Validate and fix geometries
        invalid_geometries = gdf[~gdf.geometry.is_valid]
        if len(invalid_geometries) > 0:
            logger.warning(
                f"Found {len(invalid_geometries)} invalid geometries. Attempting to fix..."
            )
            gdf.geometry = gdf.geometry.buffer(0)

        return gdf

    def _get_geometry_type(self, gdf: gpd.GeoDataFrame) -> str:
        """Determine the geometry type of a GeoDataFrame"""
        geom_types = gdf.geometry.geom_type.unique()
        if len(geom_types) == 1:
            return geom_types[0].upper()
        return "GEOMETRY"  # Mixed geometry types

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
                    if pd.isna(value):
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
