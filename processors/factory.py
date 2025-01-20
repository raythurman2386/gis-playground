from typing import Optional, Dict

from processors.base_processor import BaseDataProcessor
from processors.shapefile_processor import ShapefileProcessor
from processors.csv_processor import CSVProcessor
from processors.geojson_processor import GeoJSONProcessor
from processors.geopackage_processor import GeoPackageProcessor


class DataProcessorFactory:
    _processors = {
        "shapefile": ShapefileProcessor,
        "csv": CSVProcessor,
        "geojson": GeoJSONProcessor,
        "geopackage": GeoPackageProcessor,
    }

    @classmethod
    def get_processor(cls, file_type: str) -> Optional[BaseDataProcessor]:
        processor_class = cls._processors.get(file_type)
        if processor_class:
            return processor_class()
        return None

    @classmethod
    def get_supported_types(cls) -> Dict[str, Dict[str, str]]:
        """
        Returns a dictionary of supported file types and their required files
        """
        supported_types = {}
        for file_type, processor_class in cls._processors.items():
            processor = processor_class()
            supported_types[file_type] = processor.get_required_files()
        return supported_types
