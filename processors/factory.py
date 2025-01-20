from typing import Optional

from processors.base_processor import BaseDataProcessor
from processors.shapefile_processor import ShapefileProcessor


class DataProcessorFactory:
    _processors = {"shapefile": ShapefileProcessor}

    @classmethod
    def get_processor(cls, file_type: str) -> Optional[BaseDataProcessor]:
        processor_class = cls._processors.get(file_type)
        if processor_class:
            return processor_class()
        return None
