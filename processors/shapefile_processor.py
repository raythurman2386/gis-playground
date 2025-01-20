import geopandas as gpd
from typing import Dict, Any, Union, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import math
import pandas as pd
from app.database import crud
from processors.base_processor import BaseDataProcessor
from tools.ai.smart_processor import SmartProcessor
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
            temp_dir = self.upload_dir / layer_name
            temp_dir.mkdir(exist_ok=True)
            saved_paths = []

            try:
                # Save files
                for ext in self.get_file_extensions():
                    file = files[f"file_{ext[1:]}"]
                    filepath = temp_dir / f"{layer_name}_temp{ext}"
                    file.save(filepath)
                    saved_paths.append(filepath)

                # Process shapefile
                shp_path = temp_dir / f"{layer_name}.shp"
                return self.process_shapefile(
                    shp_path=shp_path,
                    layer_name=layer_name,
                    db_session=db_session,
                    description=description,
                )

            finally:
                # Clean up
                for path in saved_paths:
                    if path.exists():
                        path.unlink()
                if temp_dir.exists():
                    temp_dir.rmdir()

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
            # Read the shapefile
            logger.info(f"Reading shapefile from: {shp_path}")
            gdf = self._load_and_standardize_geodataframe(shp_path)

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

            logger.info(f"AI Analysis for {layer_name}:")
            logger.info(f"Suggested Name: {ai_analysis.get('suggested_name')}")
            logger.info(
                f"Suggested Description: {ai_analysis.get('suggested_description')}"
            )
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

    def _load_and_standardize_geodataframe(
        self, file_path: Union[str, Path]
    ) -> gpd.GeoDataFrame:
        """
        Load and standardize a GeoDataFrame from a file

        Args:
            file_path: Path to the spatial data file

        Returns:
            Standardized GeoDataFrame
        """
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
        """
        Determine the geometry type of a GeoDataFrame

        Args:
            gdf: GeoDataFrame to analyze

        Returns:
            String representing the geometry type
        """
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

    def get_layer_as_geojson(
        self, layer_id: int, db_session: Session
    ) -> Optional[Dict]:
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
