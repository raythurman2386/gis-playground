import geopandas as gpd
import fiona
from typing import Dict, Any, List

import pandas as pd
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import crud
from processors.base_processor import BaseDataProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "geopackage_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class GeoPackageProcessor(BaseDataProcessor):
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

                # If no specific layer is selected and there's only one layer, use it
                if not selected_layer:
                    if len(available_layers) == 1:
                        selected_layer = available_layers[0]
                    else:
                        return {
                            "success": False,
                            "error": "Multiple layers found in GeoPackage. Please specify a layer.",
                            "available_layers": available_layers,
                        }

                # Read the selected layer
                logger.info(f"Reading layer '{selected_layer}' from GeoPackage")
                gdf = gpd.read_file(temp_path, layer=selected_layer)

                # Standardize the GeoDataFrame
                gdf = self._load_and_standardize_geodataframe(gdf)

                # Determine geometry type
                geometry_type = self._get_geometry_type(gdf)

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
                    "message": "GeoPackage layer processed successfully",
                    "layer_id": layer.id,
                    "feature_count": features_added,
                    "total_features": len(gdf),
                    "geometry_type": geometry_type,
                    "crs": str(gdf.crs),
                    "source_layer": selected_layer,
                }

            finally:
                # Clean up
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Error processing GeoPackage: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

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
