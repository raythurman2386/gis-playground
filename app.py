from flask import Flask, render_template, jsonify
from data.data_processor import GeoDataProcessor
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    'flask_app',
    log_level=CURRENT_LOGGING_CONFIG['log_level'],
    log_dir=CURRENT_LOGGING_CONFIG['log_dir']
)

app = Flask(__name__)

# Initialize the data processor
data_processor = GeoDataProcessor()


@app.route('/')
def index():
    logger.debug("Serving index page")
    return render_template('index.html')


@app.route('/api/states')
def get_states():
    """API endpoint to serve state boundary data"""
    logger.debug("Handling /api/states request")
    state_data = data_processor.get_state_boundaries()
    if state_data:
        logger.info("Successfully served state boundary data")
        return jsonify(state_data)
    logger.error("Failed to serve state boundary data")
    return jsonify({"error": "Failed to load state data"}), 500


if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True)