from sqlalchemy import create_engine, text
from app.database.base import Base, engine
from app.models.spatial import SpatialLayer, Feature, LayerAttribute, UploadHistory
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "db_management",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


def truncate_tables():
    """Truncate all tables in the database"""
    try:
        # Create a new connection
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # Disable foreign key checks temporarily
                connection.execute(
                    text(
                        "ALTER TABLE features DROP CONSTRAINT IF EXISTS features_layer_id_fkey"
                    )
                )
                connection.execute(
                    text(
                        "ALTER TABLE layer_attributes DROP CONSTRAINT IF EXISTS layer_attributes_layer_id_fkey"
                    )
                )
                connection.execute(
                    text(
                        "ALTER TABLE upload_history DROP CONSTRAINT IF EXISTS upload_history_layer_id_fkey"
                    )
                )

                # Truncate all tables
                connection.execute(text("TRUNCATE TABLE spatial_layers CASCADE"))
                connection.execute(text("TRUNCATE TABLE features CASCADE"))
                connection.execute(text("TRUNCATE TABLE layer_attributes CASCADE"))
                connection.execute(text("TRUNCATE TABLE upload_history CASCADE"))

                # Re-enable foreign key constraints
                connection.execute(
                    text(
                        """
                    ALTER TABLE features 
                    ADD CONSTRAINT features_layer_id_fkey 
                    FOREIGN KEY (layer_id) REFERENCES spatial_layers(id)
                """
                    )
                )
                connection.execute(
                    text(
                        """
                    ALTER TABLE layer_attributes 
                    ADD CONSTRAINT layer_attributes_layer_id_fkey 
                    FOREIGN KEY (layer_id) REFERENCES spatial_layers(id)
                """
                    )
                )
                connection.execute(
                    text(
                        """
                    ALTER TABLE upload_history 
                    ADD CONSTRAINT upload_history_layer_id_fkey 
                    FOREIGN KEY (layer_id) REFERENCES spatial_layers(id)
                """
                    )
                )

        logger.info("Successfully truncated all tables")
        return True
    except Exception as e:
        logger.error(f"Error truncating tables: {e}")
        return False


def reset_database():
    """Drop and recreate all tables"""
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("Successfully dropped all tables")

        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully recreated all tables")

        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False


def get_table_counts():
    """Get the current count of records in each table"""
    try:
        with engine.connect() as connection:
            counts = {}
            tables = [
                "spatial_layers",
                "features",
                "layer_attributes",
                "upload_history",
            ]

            for table in tables:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()

        return counts
    except Exception as e:
        logger.error(f"Error getting table counts: {e}")
        return None
