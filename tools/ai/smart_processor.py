from datetime import datetime
import nltk
import numpy as np
import pandas as pd
from pyproj import CRS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from typing import Dict, List
import geopandas as gpd
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG

logger = setup_logger(
    "smart_processor",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class SmartProcessor:
    """
    Provides AI-assisted processing for spatial data, including:
    - Layer name suggestions
    - Description generation
    - Data quality analysis
    - Basic feature clustering
    """

    def __init__(self):
        try:
            # Download required NLTK data
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            nltk.download("averaged_perceptron_tagger_eng", quiet=True)
            nltk.download("maxent_ne_chunker", quiet=True)
            nltk.download("words", quiet=True)
            nltk.download("stopwords", quiet=True)
            self.stop_words = set(nltk.corpus.stopwords.words("english"))
        except Exception as e:
            logger.warning(f"Error downloading NLTK data: {e}")
            self.stop_words = set()

    def analyze_dataset(self, gdf: gpd.GeoDataFrame, layer_name: str = None) -> Dict:
        """
        Analyze a GeoDataFrame and provide insights and suggestions
        """
        try:
            results = {
                "suggested_name": None,
                "suggested_description": None,
                "data_quality": self._analyze_data_quality(gdf),
                "clusters": None,
            }

            # Suggest layer name if not provided
            if not layer_name:
                results["suggested_name"] = self._suggest_layer_name(gdf)

            # Generate description
            results["suggested_description"] = self._generate_description(
                gdf, results["suggested_name"] or layer_name
            )

            # Add clustering for larger datasets
            if len(gdf) > 100:
                results["clusters"] = self._cluster_features(gdf)

            return results

        except Exception as e:
            logger.error(f"Error analyzing dataset: {e}", exc_info=True)
            return {"error": str(e)}

    def _suggest_layer_name(self, gdf: gpd.GeoDataFrame) -> str:
        """Generate a suggested layer name based on intelligent attribute analysis"""
        try:
            column_scores = {}

            for col in gdf.columns:
                if col == "geometry":
                    continue

                score = 0
                col_lower = col.lower()
                tokens = nltk.word_tokenize(col_lower)
                pos_tags = nltk.pos_tag(tokens)

                # Give higher scores to columns with nouns
                for word, pos in pos_tags:
                    if pos.startswith("NN"):
                        score += 1
                    if word not in self.stop_words:
                        score += 0.5

                # Analyze column content
                sample_values = gdf[col].dropna().astype(str).head(10)
                if not sample_values.empty:
                    # Check if values are primarily text and meaningful
                    sample_text = " ".join(sample_values)
                    if sample_text.strip():
                        value_tokens = nltk.word_tokenize(sample_text.lower())
                        value_pos = nltk.pos_tag(value_tokens)

                        # Count meaningful words in values
                        meaningful_words = [
                            word
                            for word, pos in value_pos
                            if pos.startswith("NN") and word not in self.stop_words
                        ]

                        # Add to score based on meaningful content
                        score += len(set(meaningful_words)) * 0.2

                        # Prefer columns with reasonable unique value counts
                        unique_ratio = len(gdf[col].unique()) / len(gdf)
                        if 0.01 < unique_ratio < 0.9:
                            score += 1

                column_scores[col] = score

            # Get the column with the highest score
            if column_scores:
                best_column = max(column_scores.items(), key=lambda x: x[1])[0]
                most_common = (
                    gdf[best_column].dropna().mode().iloc[0] if not gdf[best_column].empty else None
                )

                if most_common:
                    return str(most_common).lower().replace(" ", "_")[:50]

            # Generate timestamp-based name if no meaningful name found
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"layer_{timestamp}"

        except Exception as e:
            logger.error(f"Error suggesting layer name: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"layer_{timestamp}"

    def _generate_description(self, gdf: gpd.GeoDataFrame, layer_name: str) -> str:
        """
        Generate a descriptive summary of the dataset
        """
        try:
            # Basic dataset information
            feature_count = len(gdf)
            geometry_type = gdf.geometry.geom_type.iloc[0]

            # Get spatial extent
            bounds = gdf.total_bounds
            extent = f"({bounds[0]:.2f}, {bounds[1]:.2f}) to ({bounds[2]:.2f}, {bounds[3]:.2f})"

            # Analyze attributes
            attribute_count = len(gdf.columns) - 1  # Excluding geometry
            numeric_cols = gdf.select_dtypes(include=[np.number]).columns
            text_cols = gdf.select_dtypes(include=["object"]).columns
            text_cols = [col for col in text_cols if col != "geometry"]

            # Get key attributes
            key_attributes = []
            for col in gdf.columns:
                if col != "geometry":
                    unique_count = gdf[col].nunique()
                    if unique_count > 0 and unique_count < len(gdf) * 0.5:
                        sample_values = gdf[col].dropna().unique()[:3]
                        if len(sample_values) > 0:
                            key_attributes.append(
                                f"{col} (e.g., {', '.join(str(x) for x in sample_values)})"
                            )

            # Build description
            description_parts = [
                f"{layer_name} contains {feature_count} {geometry_type.lower()} features",
                f"with {attribute_count} attributes.",
                f"The data covers a spatial extent of {extent}.",
            ]

            # Add attribute information
            if len(numeric_cols) > 0:
                description_parts.append(f"It includes {len(numeric_cols)} numeric fields")
                if len(text_cols) > 0:
                    description_parts.append(f"and {len(text_cols)} text fields.")
                else:
                    description_parts.append(".")

            # Add key attributes if found
            if key_attributes:
                description_parts.append(
                    "Key attributes include: " + "; ".join(key_attributes[:3]) + "."
                )

            # Add data completeness
            completeness = (1 - gdf.isnull().mean().mean()) * 100
            description_parts.append(f"The dataset is approximately {completeness:.1f}% complete.")

            # Combine all parts
            description = " ".join(description_parts)

            # Add any cluster information if available
            if len(gdf) > 100:
                clusters = self._cluster_features(gdf)
                if clusters and "n_clusters" in clusters:
                    description += f" The data can be naturally grouped into {clusters['n_clusters']} clusters based on its attributes."

            return description

        except Exception as e:
            logger.error(f"Error generating description: {e}", exc_info=True)
            return (
                f"Dataset containing {len(gdf)} features of type {gdf.geometry.geom_type.iloc[0]}."
            )

    def _analyze_data_quality(self, gdf: gpd.GeoDataFrame) -> Dict:
        """Analyze data quality metrics"""
        quality_report = {}

        try:
            for col in gdf.columns:
                if col != "geometry":
                    column_stats = {
                        "completeness": (1 - gdf[col].isnull().mean()) * 100,
                        "unique_values": len(gdf[col].unique()),
                        "data_type": str(gdf[col].dtype),
                    }

                    # Additional numeric column statistics
                    if np.issubdtype(gdf[col].dtype, np.number):
                        column_stats.update(
                            {
                                "mean": (
                                    float(gdf[col].mean()) if not gdf[col].isnull().all() else None
                                ),
                                "std": (
                                    float(gdf[col].std()) if not gdf[col].isnull().all() else None
                                ),
                            }
                        )

                    # Text column analysis
                    elif gdf[col].dtype == "object":
                        non_null_values = gdf[col].dropna()
                        if len(non_null_values) > 0:
                            # Get sample of text values
                            sample_text = " ".join(non_null_values.head(10).astype(str))
                            tokens = nltk.word_tokenize(sample_text)

                            column_stats.update(
                                {
                                    "avg_length": np.mean([len(str(x)) for x in non_null_values]),
                                    "common_terms": [
                                        word
                                        for word, _ in nltk.FreqDist(tokens).most_common(5)
                                        if word.isalpha()
                                    ],
                                }
                            )

                    quality_report[col] = column_stats

            return quality_report

        except Exception as e:
            logger.error(f"Error analyzing data quality: {e}", exc_info=True)
            return {"error": str(e)}

    def _cluster_features(self, gdf: gpd.GeoDataFrame, n_clusters: int = 5) -> Dict:
        """Cluster features based on numeric attributes and spatial location"""
        try:
            # Prepare feature matrix
            numeric_cols = gdf.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return None

            # Create feature matrix with numeric columns
            features = gdf[numeric_cols].fillna(0).copy()

            # Check if the CRS is geographic
            if gdf.crs is None or CRS(gdf.crs).is_geographic:
                # Reproject to a suitable projected CRS (e.g., Web Mercator)
                gdf_projected = gdf.to_crs(epsg=3857)
            else:
                gdf_projected = gdf

            # Calculate centroids in the projected CRS
            centroids = gdf_projected.geometry.centroid
            features["centroid_x"] = centroids.x
            features["centroid_y"] = centroids.y

            # Normalize features
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            X = scaler.fit_transform(features)

            # Perform clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(gdf)))
            clusters = kmeans.fit_predict(X)

            return {
                "cluster_assignments": clusters.tolist(),
                "n_clusters": len(np.unique(clusters)),
                "features_used": numeric_cols.tolist(),
            }

        except Exception as e:
            logger.error(f"Error clustering features: {e}", exc_info=True)
            return None
