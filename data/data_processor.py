import geopandas as gpd
import json
from pathlib import Path
from config.logging_config import CURRENT_LOGGING_CONFIG
from utils.logger import setup_logger

logger = setup_logger(
    'data_processor',
    log_level=CURRENT_LOGGING_CONFIG['log_level'],
    log_dir=CURRENT_LOGGING_CONFIG['log_dir']
)


class GeoDataProcessor:
    def __init__(self, data_dir="data/raw/natural_earth"):
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized GeoDataProcessor with data directory: {self.data_dir}")

    def load_states(self):
        """Load and process the states shapefile"""
        try:
            shapefile_path = self.data_dir / "110m_states_provinces.shp"
            logger.debug(f"Loading shapefile from: {shapefile_path}")

            states_gdf = gpd.read_file(shapefile_path)
            logger.info(f"Loaded shapefile with {len(states_gdf)} features")

            logger.debug(f"Available columns: {states_gdf.columns.tolist()}")

            if states_gdf.crs is None:
                logger.warning("CRS not defined in shapefile, setting to EPSG:4326")
                states_gdf.set_crs(epsg=4326, inplace=True)

            if states_gdf.crs != "EPSG:4326":
                logger.debug(f"Converting CRS from {states_gdf.crs} to EPSG:4326")
                states_gdf = states_gdf.to_crs("EPSG:4326")

            # Add a simple ID field
            states_gdf['id'] = range(len(states_gdf))
            states_gdf['name'] = [f'Region {i}' for i in range(len(states_gdf))]

            geojson_data = json.loads(states_gdf.to_json())
            logger.info("Successfully converted data to GeoJSON")

            return geojson_data

        except Exception as e:
            logger.error(f"Error loading shapefile: {e}", exc_info=True)
            return None

    def get_state_boundaries(self):
        """Get simplified state boundaries for web display"""
        logger.debug("Fetching state boundaries")
        geojson_data = self.load_states()
        if geojson_data:
            return geojson_data
        logger.error("Failed to get state boundaries")
        return None
