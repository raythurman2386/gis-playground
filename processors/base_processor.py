from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.orm import Session
from pathlib import Path


class BaseDataProcessor(ABC):
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def validate_files(self, files: Dict[str, Any]) -> bool:
        """Validate the uploaded files"""
        pass

    @abstractmethod
    def process_data(
        self,
        files: Dict[str, Any],
        layer_name: str,
        db_session: Session,
        description: str = "",
    ) -> Dict[str, Any]:
        """Process the data and store it in the database"""
        pass

    @abstractmethod
    def get_required_files(self) -> Dict[str, str]:
        """Return a dictionary of required files and their descriptions"""
        pass

    @abstractmethod
    def get_file_extensions(self) -> set:
        """Return a set of allowed file extensions"""
        pass
