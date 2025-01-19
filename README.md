# GIS Playground

GIS Playground is an interactive web mapping application that combines real-time wildfire data from ESRI's feature services with state boundary visualization, allowing users to explore active fire incidents and their perimeters while toggling between various base maps. The project demonstrates modern web GIS capabilities, featuring dynamic data visualization, interactive statistics panels, and will expand to include custom shapefile uploads and Census data integration.

![GIS Playground](app/static/images/gis_playground.png)

## Features

- Interactive heatmap/choropleth visualization of demographic data
- Region comparison tools
- Dynamic data filtering
- Custom query builder
- Detailed region statistics

## Prerequisites

- Python 3.8+
- Census API key
- Natural Earth Data files

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/census-heatmap.git
cd census-heatmap
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Set up your Census API key:

    - Create a copy of `config/config.example.py` as `config/config.py`
    - Add your Census API key to the configuration file

## Project Structure

- `app/`: Source code directory
    - `database/`: Data processing and management
    - `models/`: Census API interaction
    - `routes/`: Census API interaction
    - `static/`: Map generation and visualization
    - `templates/`: HTML templates
    - __init__.py: Package initialization
- `config/`: Configuration files
- `data/`: Raw and processed data storage
- `logs/`: Log files
- `processors/`: Data processing scripts
- `tools/`: Geoprocessing tools
- `utils/`: Utility functions
- `requirements.txt`: List of dependencies
- `README.md`: Project documentation
- `manage.py`: Database management commands
- `run.py`: Main Flask application

## Usage

1. Start the Flask development server:
```bash
python run.py
```

2. Open your web browser and navigate to `http://localhost:5000`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- U.S. Census Bureau for providing the API
- Natural Earth Data for boundary files

## Additional Resources

- [Natural Earth Data](https://www.naturalearthdata.com/)
- [Census Data API](https://api.census.gov)
- [Leaflet Providers](https://leaflet-extras.github.io/leaflet-providers/preview/)