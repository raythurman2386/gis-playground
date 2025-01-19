import geopandas as gpd
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from config.logging_config import CURRENT_LOGGING_CONFIG
from utils.logger import setup_logger
from app.database import crud
from sqlalchemy.orm import Session

logger = setup_logger(
    "data_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class GeoDataProcessor:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Initialized GeoDataProcessor with upload directory: {self.upload_dir}"
        )

    def process_shapefile(
        self,
        shp_path: Union[str, Path],
        layer_name: str,
        db_session: Session,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Process a shapefile and store it in the database

        Args:
            shp_path: Path to the shapefile
            layer_name: Name for the layer in the database
            db_session: Database session
            description: Optional description of the layer

        Returns:
            Dict containing processing results
        """
        try:
            # Read the shapefile
            logger.info(f"Reading shapefile from: {shp_path}")
            gdf = self._load_and_standardize_geodataframe(shp_path)

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
                "message": "Layer created successfully",
                "layer_id": layer.id,
                "feature_count": features_added,
                "total_features": len(gdf),
                "geometry_type": geometry_type,
                "crs": str(gdf.crs),
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
        """
        Process features from a GeoDataFrame into the database

        Args:
            gdf: GeoDataFrame containing features
            layer_id: ID of the layer in the database
            db_session: Database session

        Returns:
            Number of features successfully processed
        """
        features_added = 0
        for idx, row in gdf.iterrows():
            try:
                geometry = row.geometry.__geo_interface__
                properties = row.drop("geometry").to_dict()

                crud.add_feature(
                    db=db_session,
                    layer_id=layer_id,
                    geometry=geometry,
                    properties=properties,
                )
                features_added += 1
            except Exception as e:
                logger.error(f"Error adding feature {idx}: {e}")
                continue

        if features_added == 0:
            raise ValueError("No features were successfully added to the database")

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
