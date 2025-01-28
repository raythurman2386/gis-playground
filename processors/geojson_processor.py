import geopandas as gpd
from typing import Dict, Any, Union
import pandas as pd
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import crud
from processors.base_processor import BaseDataProcessor
from tools.ai.smart_processor import SmartProcessor
from tools.conversion.crs_correction import standardize_crs
from tools.validation.geometry import check_geometry_types, validate_and_fix_geometries
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
            safe_name = layer_name.replace(" ", "_") if layer_name else "temp"
            temp_path = self.upload_dir / f"{safe_name}_temp.geojson"
            geojson_file.save(temp_path)

            try:
                # Validate GeoJSON structure
                encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
                json_data = None

                for encoding in encodings_to_try:
                    try:
                        with open(temp_path, "r", encoding=encoding) as f:
                            try:
                                json_data = json.load(f)
                                logger.debug(f"Successfully read file with {encoding} encoding")
                                break
                            except json.JSONDecodeError:
                                continue
                    except UnicodeDecodeError:
                        continue

                if json_data is None:
                    return {
                        "success": False,
                        "error": "Unable to read GeoJSON file. File may be corrupted or using unsupported encoding.",
                    }

                # Read GeoJSON file with detected encoding
                logger.info(f"Reading GeoJSON from: {temp_path}")
                gdf = gpd.read_file(
                    temp_path, encoding="utf-8"
                )  # GeoJSON should be UTF-8 after json.load

                # AI Analysis
                ai_analysis = self.smart_processor.analyze_dataset(gdf, layer_name)

                # Use AI-suggested name and description if not provided
                if not layer_name and ai_analysis.get("suggested_name"):
                    layer_name = ai_analysis["suggested_name"]

                if not description and ai_analysis.get("suggested_description"):
                    description = ai_analysis["suggested_description"]

                # Determine geometry type
                geometry_type = check_geometry_types(gdf)

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
                    "message": "GeoJSON processed successfully",
                    "layer_id": layer.id,
                    "layer_name": layer_name,
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

    def _load_and_standardize_geodataframe(self, file_path: Union[str, Path]) -> gpd.GeoDataFrame:
        """Load and standardize a GeoDataFrame from a GeoJSON file"""
        try:
            # Try different encodings
            encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

            for encoding in encodings_to_try:
                try:
                    gdf = gpd.read_file(file_path, encoding=encoding)
                    logger.debug(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Unable to read file with any supported encoding")

            # Handle CRS
            gdf = standardize_crs(gdf)

            # Validate and fix geometries
            gdf = validate_and_fix_geometries(gdf)

            return gdf

        except Exception as e:
            logger.error(f"Error loading geodataframe: {e}", exc_info=True)
            raise

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
