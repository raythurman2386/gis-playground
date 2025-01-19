from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from geoalchemy2.types import Geography
from app.database.base import Base


class SpatialLayer(Base):
    __tablename__ = "spatial_layers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    geometry_type = Column(String)
    srid = Column(Integer, default=4326)
    style = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    layer_id = Column(Integer, ForeignKey("spatial_layers.id"), index=True)
    geometry = Column(
        Geography("GEOMETRY", srid=4326)
    )  # Using Geography type for lat/lon
    properties = Column(String)  # JSON string of properties
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LayerAttribute(Base):
    __tablename__ = "layer_attributes"

    id = Column(Integer, primary_key=True, index=True)
    layer_id = Column(Integer, ForeignKey("spatial_layers.id"), index=True)
    name = Column(String)
    attribute_type = Column(String)  # string, number, date, etc.
    description = Column(String, nullable=True)


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_type = Column(String)
    layer_id = Column(Integer, ForeignKey("spatial_layers.id"), index=True)
    status = Column(String)  # success, failed, processing
    error_message = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
