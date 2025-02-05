import geopandas as gpd
import numpy as np
import osmnx as ox
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import networkx as nx
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt

from config.logging_config import CURRENT_LOGGING_CONFIG
from utils.logger import setup_logger

logger = setup_logger(
    "data_generator",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)


class GeospatialDataGenerator:
    _boundary_cache = {}
    _graph_cache = {}
    _region_queries = {
        # West Coast
        "seattle": {"city": "Seattle", "state": "Washington", "country": "USA"},
        "portland": {"city": "Portland", "state": "Oregon", "country": "USA"},
        "san_francisco": {"city": "San Francisco", "state": "California", "country": "USA"},
        "los_angeles": {"city": "Los Angeles", "state": "California", "country": "USA"},

        # Mountain States
        "denver": {"city": "Denver", "state": "Colorado", "country": "USA"},
        "salt_lake_city": {"city": "Salt Lake City", "state": "Utah", "country": "USA"},
        "phoenix": {"city": "Phoenix", "state": "Arizona", "country": "USA"},
        "las_vegas": {"city": "Las Vegas", "state": "Nevada", "country": "USA"},
        "boise": {"city": "Boise", "state": "Idaho", "country": "USA"},
        "helena": {"city": "Helena", "state": "Montana", "country": "USA"},
        "santa_fe": {"city": "Santa Fe", "state": "New Mexico", "country": "USA"},
        "cheyenne": {"city": "Cheyenne", "state": "Wyoming", "country": "USA"},

        # Midwest
        "chicago": {"city": "Chicago", "state": "Illinois", "country": "USA"},
        "detroit": {"city": "Detroit", "state": "Michigan", "country": "USA"},
        "minneapolis": {"city": "Minneapolis", "state": "Minnesota", "country": "USA"},
        "milwaukee": {"city": "Milwaukee", "state": "Wisconsin", "country": "USA"},
        "indianapolis": {"city": "Indianapolis", "state": "Indiana", "country": "USA"},
        "columbus": {"city": "Columbus", "state": "Ohio", "country": "USA"},
        "kansas_city": {"city": "Kansas City", "state": "Missouri", "country": "USA"},
        "omaha": {"city": "Omaha", "state": "Nebraska", "country": "USA"},
        "des_moines": {"city": "Des Moines", "state": "Iowa", "country": "USA"},
        "sioux_falls": {"city": "Sioux Falls", "state": "South Dakota", "country": "USA"},
        "bismarck": {"city": "Bismarck", "state": "North Dakota", "country": "USA"},

        # Northeast
        "new_york": {"city": "New York City", "state": "New York", "country": "USA"},
        "boston": {"city": "Boston", "state": "Massachusetts", "country": "USA"},
        "philadelphia": {"city": "Philadelphia", "state": "Pennsylvania", "country": "USA"},
        "providence": {"city": "Providence", "state": "Rhode Island", "country": "USA"},
        "hartford": {"city": "Hartford", "state": "Connecticut", "country": "USA"},
        "portland_me": {"city": "Portland", "state": "Maine", "country": "USA"},
        "manchester": {"city": "Manchester", "state": "New Hampshire", "country": "USA"},
        "burlington": {"city": "Burlington", "state": "Vermont", "country": "USA"},
        "baltimore": {"city": "Baltimore", "state": "Maryland", "country": "USA"},
        "newark": {"city": "Newark", "state": "New Jersey", "country": "USA"},
        "wilmington": {"city": "Wilmington", "state": "Delaware", "country": "USA"},

        # South
        "miami": {"city": "Miami", "state": "Florida", "country": "USA"},
        "atlanta": {"city": "Atlanta", "state": "Georgia", "country": "USA"},
        "nashville": {"city": "Nashville", "state": "Tennessee", "country": "USA"},
        "charlotte": {"city": "Charlotte", "state": "North Carolina", "country": "USA"},
        "virginia_beach": {"city": "Virginia Beach", "state": "Virginia", "country": "USA"},
        "charleston": {"city": "Charleston", "state": "South Carolina", "country": "USA"},
        "new_orleans": {"city": "New Orleans", "state": "Louisiana", "country": "USA"},
        "houston": {"city": "Houston", "state": "Texas", "country": "USA"},
        "birmingham": {"city": "Birmingham", "state": "Alabama", "country": "USA"},
        "jackson": {"city": "Jackson", "state": "Mississippi", "country": "USA"},
        "little_rock": {"city": "Little Rock", "state": "Arkansas", "country": "USA"},
        "louisville": {"city": "Louisville", "state": "Kentucky", "country": "USA"},
        "oklahoma_city": {"city": "Oklahoma City", "state": "Oklahoma", "country": "USA"},
        "charleston_wv": {"city": "Charleston", "state": "West Virginia", "country": "USA"},

        # Non-Contiguous States
        "anchorage": {"city": "Anchorage", "state": "Alaska", "country": "USA"},
        "honolulu": {"city": "Honolulu", "state": "Hawaii", "country": "USA"},

        # Additional Major Cities
        "san_diego": {"city": "San Diego", "state": "California", "country": "USA"},
        "dallas": {"city": "Dallas", "state": "Texas", "country": "USA"},
        "san_antonio": {"city": "San Antonio", "state": "Texas", "country": "USA"},
        "austin": {"city": "Austin", "state": "Texas", "country": "USA"},
        "memphis": {"city": "Memphis", "state": "Tennessee", "country": "USA"},
        "st_louis": {"city": "St. Louis", "state": "Missouri", "country": "USA"},
        "pittsburgh": {"city": "Pittsburgh", "state": "Pennsylvania", "country": "USA"},
        "cincinnati": {"city": "Cincinnati", "state": "Ohio", "country": "USA"},
        "cleveland": {"city": "Cleveland", "state": "Ohio", "country": "USA"},
        "tampa": {"city": "Tampa", "state": "Florida", "country": "USA"},
        "orlando": {"city": "Orlando", "state": "Florida", "country": "USA"},
        "sacramento": {"city": "Sacramento", "state": "California", "country": "USA"},
        "portland_or": {"city": "Portland", "state": "Oregon", "country": "USA"},
        "albuquerque": {"city": "Albuquerque", "state": "New Mexico", "country": "USA"},
        "tucson": {"city": "Tucson", "state": "Arizona", "country": "USA"},
        "fresno": {"city": "Fresno", "state": "California", "country": "USA"},
        "raleigh": {"city": "Raleigh", "state": "North Carolina", "country": "USA"},
        "buffalo": {"city": "Buffalo", "state": "New York", "country": "USA"},
        "richmond": {"city": "Richmond", "state": "Virginia", "country": "USA"},
        "grand_rapids": {"city": "Grand Rapids", "state": "Michigan", "country": "USA"}
    }

    def __init__(self, data_type="points", region="seattle", num_points=1000):
        self.data_type = data_type
        self.region = region
        self.num_points = num_points
        self.data = None
        self.boundary = None
        self.DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.graph = None
        self.street_network = None

        # Load cached data or create new
        try:
            self._load_cached_data()
            if self.boundary is not None:
                self.plot_boundary()
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")

    def _load_cached_data(self):
        """Load data from cache or create new"""
        try:
            # Check if region data is in cache
            if self.region in self._boundary_cache:
                logger.info(f"Loading boundary for {self.region} from cache")
                self.boundary = self._boundary_cache[self.region]
                self.graph = self._graph_cache.get(self.region)
            else:
                # Load new data and cache it
                logger.info(f"Loading new data for {self.region}")
                success = self.load_boundary()  # Check if loading was successful
                if success and self.boundary is not None:
                    self._boundary_cache[self.region] = self.boundary
                    if self.graph is not None:
                        self._graph_cache[self.region] = self.graph

            # Ensure CRS is correct
            if self.boundary is not None:
                self.boundary = self._ensure_crs(self.boundary)
            else:
                raise ValueError(f"Failed to load boundary for {self.region}")

        except Exception as e:
            logger.error(f"Error loading cached data: {str(e)}")
            self.load_boundary()

    def load_boundary(self):
        """Load boundary data from OpenStreetMap"""
        try:
            if self.region in self._region_queries:
                logger.info(f"Loading boundary data for {self.region} from OpenStreetMap...")

                try:
                    # First attempt: Try to get the administrative boundary
                    gdf = ox.geocode_to_gdf(
                        self._region_queries[self.region],
                        which_result=1
                    )
                except Exception as e:
                    logger.warning(f"Could not get administrative boundary: {e}")
                    # Second attempt: Get the place boundary
                    gdf = ox.features_from_place(
                        self._region_queries[self.region],
                        tags={'boundary': 'administrative'}
                    )
                    # Dissolve all boundaries into one
                    gdf = gdf.dissolve()

                # Ensure we have a valid boundary
                if gdf.empty:
                    raise ValueError(f"No boundary found for {self.region}")

                # Convert to EPSG:4326 if needed
                if gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")

                # Simplify the boundary slightly to improve performance
                gdf.geometry = gdf.geometry.simplify(tolerance=0.001)

                # Create a single polygon if multiple exist
                if len(gdf) > 1:
                    combined_geom = unary_union(gdf.geometry.values)
                    gdf = gpd.GeoDataFrame(
                        geometry=[combined_geom],
                        crs="EPSG:4326"
                    )

                self.boundary = gdf

                # Optional: Load street network for the area
                if hasattr(self, 'graph'):
                    logger.info("Loading street network...")
                    G = ox.graph_from_place(
                        self._region_queries[self.region],
                        network_type='drive'
                    )
                    self.graph = G

                    # Convert street network to GeoDataFrame
                    nodes, edges = ox.graph_to_gdfs(G)
                    self.nodes_gdf = nodes
                    self.street_network = edges

                logger.info(f"Successfully loaded boundary and street network for {self.region}")

                # Save boundary to file for caching
                cache_dir = os.path.join(self.DATA_DIR, 'cache')
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, f"{self.region}_boundary.geojson")
                self.boundary.to_file(cache_file, driver='GeoJSON')

            else:
                # Fallback to simple rectangular boundary if region not found
                logger.warning(f"Region {self.region} not found in preset queries, using fallback boundary")
                boundaries = {
                    "default": Polygon([
                        (-122.4359, 47.5003),
                        (-122.4359, 47.7340),
                        (-122.2359, 47.7340),
                        (-122.2359, 47.5003),
                        (-122.4359, 47.5003)
                    ])
                }

                self.boundary = gpd.GeoDataFrame(
                    {'geometry': [boundaries["default"]]},
                    crs="EPSG:4326"
                )

            return True

        except Exception as e:
            logger.error(f"Error loading boundary: {str(e)}")
            logger.error("Falling back to default boundary")
            # Create a simple default boundary
            default_boundary = Polygon([
                (-122.4359, 47.5003),
                (-122.4359, 47.7340),
                (-122.2359, 47.7340),
                (-122.2359, 47.5003),
                (-122.4359, 47.5003)
            ])
            self.boundary = gpd.GeoDataFrame(
                {'geometry': [default_boundary]},
                crs="EPSG:4326"
            )
            return False

    def generate_random_points(self):
        """Generate random points within boundary"""
        try:
            minx, miny, maxx, maxy = self.boundary.total_bounds

            # Generate more points than needed to account for points outside boundary
            factor = 1.5
            points = []
            while len(points) < self.num_points:
                # Generate random points
                x = np.random.uniform(minx, maxx, int(self.num_points * factor))
                y = np.random.uniform(miny, maxy, int(self.num_points * factor))

                # Create Points and check if they're within boundary
                for i in range(len(x)):
                    point = Point(x[i], y[i])
                    if self.boundary.geometry.iloc[0].contains(point):
                        points.append(point)
                        if len(points) >= self.num_points:
                            break

            return gpd.GeoDataFrame(geometry=points[: self.num_points], crs="EPSG:4326")

        except Exception as e:
            logger.error(f"Error generating points: {str(e)}")
            raise

    def generate_routes(self):
        """Generate routes using real street network data from OSM"""
        try:
            self.graph = self._ensure_graph_loaded()

            nodes_gdf, edges_gdf = ox.graph_to_gdfs(self.graph)

            routes = []
            route_data = []

            nodes = list(self.graph.nodes())

            if len(nodes) < 2:
                raise ValueError("Not enough nodes in the network")

            for i in range(self.num_points):
                try:
                    origin_node = np.random.choice(nodes)
                    dest_node = np.random.choice(nodes)
                    while origin_node == dest_node:
                        dest_node = np.random.choice(nodes)

                    route_nodes = nx.shortest_path(self.graph, origin_node, dest_node, weight='length')
                    route_coords = [(nodes_gdf.loc[node].geometry.x, nodes_gdf.loc[node].geometry.y) for node in route_nodes]

                    route = LineString(route_coords)
                    route_length = sum(edges_gdf.loc[(route_nodes[i], route_nodes[i + 1], 0), 'length'] for i in range(len(route_nodes) - 1))

                    routes.append(route)
                    route_data.append({
                        'route_id': i,
                        'distance': route_length,
                        'duration': route_length / 1609.34 / np.random.uniform(20, 40) * 60,
                        'vehicle_type': np.random.choice(['car', 'truck', 'bike']),
                        'start_time': datetime.now() + timedelta(minutes=np.random.randint(0, 1440)),
                        'num_stops': len(route_nodes) - 1
                    })

                    if (i + 1) % 10 == 0:
                        logger.info(f"Generated {i+1} routes...")

                except Exception as e:
                    logger.warning(f"Error generating route {i}: {str(e)}")
                    continue

            if not routes:
                raise ValueError("No valid routes were generated")

            routes_gdf = gpd.GeoDataFrame(route_data, geometry=routes)
            logger.info(f"Successfully generated {len(routes_gdf)} routes")
            return routes_gdf

        except Exception as e:
            logger.error(f"Error generating routes: {str(e)}")
            raise

    def generate_polygons(self):
        """Generate fake polygon data (e.g., service areas, zones) without overlaps"""
        try:
            # Generate center points for polygons with minimum distance constraint
            points = self.generate_random_points()
            points_gdf = self._ensure_crs(points)

            polygons = []
            polygon_data = []

            # Create a list to store polygon bounds for overlap checking
            existing_polygons = []

            for idx, point in enumerate(points_gdf.geometry):
                attempts = 0
                max_attempts = 10
                buffer_distance = 0.002

                while attempts < max_attempts:
                    # Create random polygon around point
                    num_points = np.random.randint(6, 10)
                    angles = np.linspace(0, 360, num_points)
                    base_distance = np.random.uniform(0.001, 0.003)
                    distances = base_distance + np.random.uniform(-0.0005, 0.0005, len(angles))

                    polygon_points = []
                    for angle, distance in zip(angles, distances):
                        dx = distance * np.cos(np.radians(angle))
                        dy = distance * np.sin(np.radians(angle))
                        polygon_points.append((point.x + dx, point.y + dy))

                    # Close the polygon
                    polygon_points.append(polygon_points[0])

                    # Create and validate polygon
                    polygon = Polygon(polygon_points)
                    if not polygon.is_valid:
                        attempts += 1
                        continue

                    # Buffer slightly to ensure no edges touch
                    buffered = polygon.buffer(0.0001)

                    # Check if within boundary
                    if not self.boundary.geometry.iloc[0].contains(buffered):
                        attempts += 1
                        continue

                    # Check for overlaps with existing polygons
                    overlapping = False
                    for existing_poly in existing_polygons:
                        if buffered.intersects(existing_poly):
                            overlapping = True
                            break

                    if not overlapping:
                        polygons.append(polygon)
                        existing_polygons.append(buffered)
                        polygon_data.append({
                            'zone_id': len(polygons)-1,
                            'area': polygon.area * (111000 ** 2),
                            'category': np.random.choice(['residential', 'commercial', 'industrial']),
                            'population': np.random.randint(100, 10000),
                            'density': np.random.uniform(1000, 5000)
                        })
                        break

                    attempts += 1

                if attempts == max_attempts:
                    logger.warning(f"Could not create non-overlapping polygon for point {idx}")

            if not polygons:
                raise ValueError("No valid polygons were generated")

            # Create GeoDataFrame with polygons
            polygons_gdf = gpd.GeoDataFrame(
                polygon_data,
                geometry=polygons,
            )
            polygons_gdf = self._ensure_crs(polygons_gdf)

            logger.info(f"Successfully generated {len(polygons_gdf)} non-overlapping polygons")
            return polygons_gdf

        except Exception as e:
            logger.error(f"Error generating polygons: {str(e)}")
            raise

    def generate_data(self):
        """Generate fake geospatial data based on type"""
        try:
            # Check if the cache needs cleared
            self.clear_cache(max_cache_size=50)

            if self.data_type == "points":
                points_gdf = self.generate_random_points()
                # Add additional point attributes
                points_gdf["point_id"] = range(len(points_gdf))
                points_gdf["timestamp"] = [
                    datetime.now() + timedelta(minutes=i)
                    for i in range(len(points_gdf))
                ]
                points_gdf["value"] = np.random.normal(50, 10, len(points_gdf))
                self.data = points_gdf

            elif self.data_type == "routes":
                self.data = self.generate_routes()

            elif self.data_type == "polygons":
                self.data = self.generate_polygons()

            else:
                raise ValueError(f"Unknown data type: {self.data_type}")

            logger.info(f"Successfully generated {len(self.data)} {self.data_type}")
            return True

        except Exception as e:
            logger.error(f"Error generating data: {str(e)}")
            return False

    def plot_data(self):
        """Plot the generated geospatial data"""
        try:
            if self.data is None:
                raise ValueError("No data to plot. Run generate_data first.")

            fig, ax = plt.subplots(figsize=(15, 10))

            boundary_plot = self.boundary.copy()
            plot_data = self.data.copy()

            # Plot boundary
            boundary_plot.plot(ax=ax, alpha=0.1, color='gray', zorder=1)

            # Plot street network
            if hasattr(self, 'graph') and self.graph is not None:
                nodes, edges = ox.graph_to_gdfs(self.graph)
                edges = self._ensure_crs(edges.copy())
                edges.plot(ax=ax, color='lightgray', alpha=0.5, linewidth=0.5, zorder=2)

            # Plot data based on type
            if self.data_type == "routes":
                for vtype in ['car', 'truck', 'bike']:
                    mask = plot_data['vehicle_type'] == vtype
                    if mask.any():
                        plot_data[mask].plot(
                            ax=ax,
                            alpha=0.6,
                            label=vtype,
                            linewidth=2,
                            zorder=3
                        )
                plt.legend()
            elif self.data_type == "polygons":
                plot_data.plot(
                    ax=ax,
                    column='category',
                    categorical=True,
                    legend=True,
                    alpha=0.5,
                    edgecolor='black',
                    linewidth=0.5,
                    zorder=3
                )
            else:
                plot_data.plot(
                    ax=ax,
                    alpha=0.6,
                    column='point_id' if 'point_id' in plot_data.columns else None,
                    cmap='viridis',
                    zorder=3
                )

            plt.title(f'{self.data_type.title()} in {self.region.title()}')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')

            # Save plot
            plt.savefig(os.path.join(self.DATA_DIR, f'geospatial_{self.region}_{self.data_type}_plot.png'))
            plt.close()

            logger.info(f"Plot saved as 'geospatial_{self.region}_{self.data_type}_plot.png'")
            return True

        except Exception as e:
            logger.error(f"Error plotting data: {str(e)}")
            return False

    def plot_boundary(self):
        """Plot the loaded boundary with contextual information"""
        try:
            if self.boundary is None:
                logger.warning("No boundary data available to plot")
                return False

            fig, ax = plt.subplots(figsize=(15, 10))

            # Plot the boundary
            self.boundary.plot(
                ax=ax,
                alpha=0.5,
                edgecolor='black',
                facecolor='lightgray'
            )

            # If we have street network data, plot it
            if hasattr(self, 'street_network') and self.street_network is not None:
                self.street_network.plot(
                    ax=ax,
                    color='blue',
                    alpha=0.2,
                    linewidth=0.5
                )

            # Add title and labels
            plt.title(f'{self.region.title()} Boundary')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')

            # Add north arrow
            ax.annotate('N', xy=(0.02, 0.98), xycoords='axes fraction',
                        fontsize=12, ha='center', va='center')

            # Add scale bar (approximate)
            bbox = self.boundary.total_bounds
            scale_length = (bbox[2] - bbox[0]) / 5  # 1/5 of the width
            scale_x = bbox[0] + scale_length/2
            scale_y = bbox[1] + (bbox[3] - bbox[1])/10
            ax.plot([scale_x - scale_length/2, scale_x + scale_length/2],
                    [scale_y, scale_y], 'k-', linewidth=2)
            ax.text(scale_x, scale_y * 0.99, f'{scale_length*111:.1f} km',
                    ha='center', va='top')

            # Save the plot
            plt.savefig(os.path.join(self.DATA_DIR, f'{self.region}_boundary.png'))
            plt.close()

            logger.info(f"Boundary plot saved as '{self.region}_boundary.png'")
            return True

        except Exception as e:
            logger.error(f"Error plotting boundary: {str(e)}")
            return False

    def save_data(self, format="geojson"):
        """Save the generated data to file"""
        try:
            if self.data is None:
                raise ValueError("No data to save. Run generate_data first.")

            if self.data.crs is None:
                self.data = self._ensure_crs(self.data)

            filename = (
                f"{self.data_type}_{self.region}_{datetime.now().strftime('%Y%m%d')}"
            )
            os.makedirs(self.DATA_DIR, exist_ok=True)

            if format == "geojson":
                filepath = os.path.join(self.DATA_DIR, f"{filename}.geojson")
                self.data.to_file(filepath, driver="GeoJSON")
            elif format == "shapefile":
                filepath = os.path.join(self.DATA_DIR, f"{filename}.shp")
                self.data.to_file(filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Data saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return None

    def _ensure_graph_loaded(self):
        """Ensure the graph is loaded with proper CRS"""
        try:
            # Check cache first
            if self.region in self._graph_cache:
                self.graph = self._graph_cache[self.region]
                logger.info(f"Loaded street network for {self.region} from cache")
                return self.graph

            if not hasattr(self, 'graph') or self.graph is None:
                logger.info("Loading street network from OSM...")

                # Create graph with explicit CRS
                self.graph = ox.graph_from_polygon(
                    self.boundary.geometry.iloc[0],
                    network_type='drive',
                    simplify=True,
                    retain_all=False,
                    truncate_by_edge=True,
                    clean_periphery=True
                )

                # Force the graph to use EPSG:4326
                self.graph = ox.project_graph(self.graph, to_crs="EPSG:4326")

                # Convert to GeoDataFrames and back to ensure CRS is set
                nodes, edges = ox.graph_to_gdfs(self.graph)
                nodes = self._ensure_crs(nodes)
                edges = self._ensure_crs(edges)
                self.graph = ox.graph_from_gdfs(nodes, edges)

                # Cache the graph
                self._graph_cache[self.region] = self.graph
                logger.info("Street network loaded successfully and cached")

            return self.graph
        except Exception as e:
            logger.error(f"Error ensuring graph is loaded: {str(e)}")
            raise

    def _ensure_crs(self, gdf, target_crs="EPSG:4326"):
        """Bulletproof CRS handling"""
        try:
            if gdf is None:
                raise ValueError("Input GeoDataFrame is None")

            # Force set CRS if None
            if gdf.crs is None:
                gdf = gdf.set_crs(target_crs)
                logger.debug(f"Set CRS to {target_crs} for GeoDataFrame")

            # Convert if different CRS
            if str(gdf.crs).upper() != str(target_crs).upper():
                gdf = gdf.to_crs(target_crs)
                logger.debug(f"Converted CRS from {gdf.crs} to {target_crs}")

            return gdf

        except Exception as e:
            logger.error(f"Error in _ensure_crs: {str(e)}")
            # If all else fails, force EPSG:4326
            try:
                gdf.set_crs("EPSG:4326", inplace=True, allow_override=True)
                return gdf
            except:
                raise ValueError(f"Could not ensure CRS: {str(e)}")

    @classmethod
    def clear_cache(cls, max_cache_size=50):
        """Clear the cached boundary and graph data when size exceeds limit

        Args:
            max_cache_size (int): Maximum number of items to keep in cache before clearing

        Returns:
            bool: True if cache was cleared, False if no clearing was needed
        """
        try:
            total_cache_size = len(cls._boundary_cache) + len(cls._graph_cache)

            if total_cache_size > max_cache_size:
                cls._boundary_cache.clear()
                cls._graph_cache.clear()
                logger.info(f"Cache cleared - exceeded max size of {max_cache_size} items")
                return True

            logger.debug(f"Cache size ({total_cache_size}) within limits ({max_cache_size})")
            return False

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False


def main():
    region = "portland"

    # Generate point data
    point_generator = GeospatialDataGenerator(
        data_type="points", region=region, num_points=1000
    )
    point_generator.generate_data()
    point_generator.plot_data()
    point_generator.save_data(format="geojson")

    # Generate route data
    route_generator = GeospatialDataGenerator(
        data_type="routes", region=region, num_points=100
    )
    route_generator.generate_data()
    route_generator.plot_data()
    route_generator.save_data(format="geojson")

    # Generate polygon data
    polygon_generator = GeospatialDataGenerator(
        data_type="polygons", region=region, num_points=50
    )
    polygon_generator.generate_data()
    polygon_generator.plot_data()
    polygon_generator.save_data(format="shapefile")


if __name__ == "__main__":
    main()
