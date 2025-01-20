import geopandas as gpd
import fiona
from typing import Dict, Any, List

import pandas as pd
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import crud
from processors.base_processor import BaseDataProcessor
from tools.ai.smart_processor import SmartProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "geopackage_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class GeoPackageProcessor(BaseDataProcessor):
    def __init__(self, upload_dir: str = "data/uploads"):
        super().__init__(upload_dir)
        self.smart_processor = SmartProcessor()

    def get_required_files(self) -> Dict[str, str]:
        return {"gpkg": "GeoPackage file (.gpkg)"}

    def get_file_extensions(self) -> set:
        return {".gpkg"}

    def validate_files(self, files: Dict[str, Any]) -> bool:
        return "file_gpkg" in files

    def process_data(
        self,
        files: Dict[str, Any],
        layer_name: str,
        db_session: Session,
        description: str = "",
        selected_layer: str = None,
    ) -> Dict[str, Any]:
        try:
            # Save GPKG file temporarily
            gpkg_file = files["file_gpkg"]
            temp_path = self.upload_dir / f"{layer_name}_temp.gpkg"
            gpkg_file.save(temp_path)

            try:
                # List available layers in the GeoPackage
                available_layers = fiona.listlayers(str(temp_path))

                if not available_layers:
                    return {"success": False, "error": "No layers found in GeoPackage"}

                # Process all layers
                processed_layers = []
                for layer_name in available_layers:
                    result = self._process_single_layer(
                        gpkg_path=temp_path,
                        layer_name=layer_name,
                        db_session=db_session,
                    )
                    processed_layers.append(result)

                # Prepare summary result
                successful_layers = [
                    layer for layer in processed_layers if layer["success"]
                ]
                failed_layers = [
                    layer for layer in processed_layers if not layer["success"]
                ]

                return {
                    "success": len(successful_layers) > 0,
                    "message": f"Processed {len(successful_layers)} layers successfully"
                    + (f", {len(failed_layers)} failed" if failed_layers else ""),
                    "processed_layers": processed_layers,
                    "total_layers": len(available_layers),
                    "successful_layers": len(successful_layers),
                    "failed_layers": len(failed_layers),
                }

            finally:
                # Clean up
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Error processing GeoPackage: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _process_single_layer(
        self, gpkg_path: Path, layer_name: str, db_session: Session
    ) -> Dict[str, Any]:
        """Process a single layer from the GeoPackage"""
        try:
            # Read the layer
            logger.info(f"Reading layer '{layer_name}' from GeoPackage")
            gdf = gpd.read_file(gpkg_path, layer=layer_name)

            # Standardize the GeoDataFrame
            gdf = self._load_and_standardize_geodataframe(gdf)

            # Get AI insights
            ai_analysis = self.smart_processor.analyze_dataset(gdf, layer_name)

            # Use AI-suggested name and description
            suggested_name = ai_analysis.get("suggested_name") or f"layer_{layer_name}"
            suggested_description = ai_analysis.get("suggested_description") or ""

            # Determine geometry type
            geometry_type = self._get_geometry_type(gdf)

            # Create the layer
            layer = crud.create_spatial_layer(
                db=db_session,
                name=suggested_name,
                description=suggested_description,
                geometry_type=geometry_type,
            )

            # Process features
            features_added = self._process_features(gdf, layer.id, db_session)

            return {
                "success": True,
                "source_layer": layer_name,
                "layer_id": layer.id,
                "layer_name": suggested_name,
                "description": suggested_description,
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
            logger.error(f"Error processing layer '{layer_name}': {e}", exc_info=True)
            return {"success": False, "source_layer": layer_name, "error": str(e)}

    def _load_and_standardize_geodataframe(
        self, gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Standardize the GeoDataFrame"""
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
