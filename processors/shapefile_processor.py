import geopandas as gpd
from typing import Dict, Any, Union, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import math
import pandas as pd
from app.database import crud
from processors.base_processor import BaseDataProcessor
from tools.ai.smart_processor import SmartProcessor
from tools.conversion.crs_correction import standardize_crs
from tools.validation.geometry import validate_and_fix_geometries, check_geometry_types
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "shapefile_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class ShapefileProcessor(BaseDataProcessor):
    def __init__(self, upload_dir: str = "data/uploads"):
        super().__init__(upload_dir)
        self.smart_processor = SmartProcessor()

    def get_required_files(self) -> Dict[str, str]:
        return {
            "shp": "Main shapefile",
            "shx": "Shape index file",
            "dbf": "Attribute database file",
        }

    def get_file_extensions(self) -> set:
        return {".shp", ".shx", ".dbf"}

    def validate_files(self, files: Dict[str, Any]) -> bool:
        required_extensions = self.get_file_extensions()
        return all(f"file_{ext[1:]}" in files for ext in required_extensions)

    def process_data(
        self,
        files: Dict[str, Any],
        layer_name: str,
        db_session: Session,
        description: str = "",
        selected_layer: str = None,
    ) -> Dict[str, Any]:
        try:
            # Create temporary directory for files
            safe_name = layer_name.replace(" ", "_") if layer_name else "temp"
            temp_dir = self.upload_dir / safe_name
            temp_dir.mkdir(exist_ok=True)
            saved_paths = []

            try:
                # Save files with consistent naming
                base_filename = f"{safe_name}_temp"
                shp_path = None

                for ext in self.get_file_extensions():
                    file_key = f"file_{ext[1:]}"
                    if file_key in files:
                        filepath = temp_dir / f"{base_filename}{ext}"
                        files[file_key].save(filepath)
                        saved_paths.append(filepath)
                        if ext == ".shp":
                            shp_path = filepath

                if not shp_path:
                    return {"success": False, "error": "No .shp file found"}

                logger.debug(f"Processing shapefile at: {shp_path}")

                # Process shapefile using the temporary path
                result = self.process_shapefile(
                    shp_path=shp_path,
                    layer_name=layer_name,
                    db_session=db_session,
                    description=description,
                )

                return result

            finally:
                # Clean up
                for path in saved_paths:
                    try:
                        if path.exists():
                            path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {path}: {e}")

                try:
                    if temp_dir.exists():
                        temp_dir.rmdir()
                except Exception as e:
                    logger.warning(f"Failed to delete temporary directory {temp_dir}: {e}")

        except Exception as e:
            logger.error(f"Error processing shapefile: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def process_shapefile(
        self,
        shp_path: Union[str, Path],
        layer_name: str,
        db_session: Session,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Process a shapefile and store it in the database
        """
        try:
            # Convert to Path and verify existence
            shp_path = Path(shp_path)
            if not shp_path.exists():
                raise FileNotFoundError(f"Shapefile not found at: {shp_path}")

            logger.info(f"Reading shapefile from: {shp_path}")
            gdf = self._load_and_standardize_geodataframe(shp_path)

            # Determine geometry type
            geometry_type = check_geometry_types(gdf)

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

            logger.info(f"AI Analysis for {layer_name}:")
            logger.info(f"Suggested Name: {ai_analysis.get('suggested_name')}")
            logger.info(f"Suggested Description: {ai_analysis.get('suggested_description')}")
            logger.info(f"Data Quality Report: {ai_analysis.get('data_quality')}")

            return {
                "success": True,
                "message": "Layer created successfully",
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

        except Exception as e:
            logger.error(f"Error processing shapefile: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _load_and_standardize_geodataframe(self, file_path: Union[str, Path]) -> gpd.GeoDataFrame:
        """
        Load and standardize a GeoDataFrame from a file
        """
        gdf = gpd.read_file(file_path)

        # Handle CRS
        gdf = standardize_crs(gdf)

        # Validate and fix geometries
        gdf = validate_and_fix_geometries(gdf)

        return gdf

    def _process_features(self, gdf: gpd.GeoDataFrame, layer_id: int, db_session: Session) -> int:
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
                    elif isinstance(value, float) and math.isinf(value):
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

    def get_layer_as_geojson(self, layer_id: int, db_session: Session) -> Optional[Dict]:
        """
        Retrieve a layer from the database as GeoJSON

        Args:
            layer_id: ID of the layer to retrieve
            db_session: Database session

        Returns:
            GeoJSON representation of the layer
        """
        try:
            features = crud.get_layer_features(db_session, layer_id)
            if not features:
                return None

            from app.database.utils import features_to_geojson

            return features_to_geojson(features)

        except Exception as e:
            logger.error(f"Error retrieving layer {layer_id}: {e}", exc_info=True)
            return None
