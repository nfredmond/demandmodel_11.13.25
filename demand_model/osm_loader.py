"""
OpenStreetMap Network Data Loader
Fetches road network nodes and links from OpenStreetMap
"""
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from typing import Optional, Tuple, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OSMNetworkLoader:
    """
    Loads road network data from OpenStreetMap
    Provides nodes and links for transportation network modeling
    """

    def __init__(self, network_type: str = 'drive'):
        """
        Initialize OSM Network Loader

        Args:
            network_type: Type of network ('drive', 'walk', 'bike', 'all')
        """
        self.network_type = network_type
        self.graph = None
        self.nodes_gdf = None
        self.links_gdf = None

        # Configure OSMnx settings
        ox.settings.log_console = True
        ox.settings.use_cache = True

    def load_network_by_place(
        self,
        place_name: str,
        network_type: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Load network for a named place

        Args:
            place_name: Name of place (e.g., "Berkeley, California, USA")
            network_type: Override default network type

        Returns:
            NetworkX MultiDiGraph
        """
        net_type = network_type or self.network_type

        logger.info(f"Downloading {net_type} network for {place_name}...")

        try:
            self.graph = ox.graph_from_place(
                place_name,
                network_type=net_type,
                simplify=True
            )

            logger.info(
                f"Network loaded: {len(self.graph.nodes)} nodes, "
                f"{len(self.graph.edges)} edges"
            )

            return self.graph

        except Exception as e:
            logger.error(f"Error loading network: {e}")
            raise

    def load_network_by_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        network_type: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Load network within a bounding box

        Args:
            north: Northern latitude
            south: Southern latitude
            east: Eastern longitude
            west: Western longitude
            network_type: Override default network type

        Returns:
            NetworkX MultiDiGraph
        """
        net_type = network_type or self.network_type

        logger.info(f"Downloading {net_type} network for bounding box...")

        try:
            self.graph = ox.graph_from_bbox(
                north, south, east, west,
                network_type=net_type,
                simplify=True
            )

            logger.info(
                f"Network loaded: {len(self.graph.nodes)} nodes, "
                f"{len(self.graph.edges)} edges"
            )

            return self.graph

        except Exception as e:
            logger.error(f"Error loading network: {e}")
            raise

    def load_network_from_polygon(
        self,
        polygon,
        network_type: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Load network within a polygon

        Args:
            polygon: Shapely Polygon or MultiPolygon
            network_type: Override default network type

        Returns:
            NetworkX MultiDiGraph
        """
        net_type = network_type or self.network_type

        logger.info(f"Downloading {net_type} network for polygon...")

        try:
            self.graph = ox.graph_from_polygon(
                polygon,
                network_type=net_type,
                simplify=True
            )

            logger.info(
                f"Network loaded: {len(self.graph.nodes)} nodes, "
                f"{len(self.graph.edges)} edges"
            )

            return self.graph

        except Exception as e:
            logger.error(f"Error loading network: {e}")
            raise

    def get_nodes_gdf(self) -> gpd.GeoDataFrame:
        """
        Get network nodes as GeoDataFrame

        Returns:
            GeoDataFrame of nodes
        """
        if self.graph is None:
            raise ValueError("No network loaded. Call load_network_* first.")

        self.nodes_gdf = ox.graph_to_gdfs(self.graph, edges=False)

        # Add additional node attributes
        self.nodes_gdf['node_id'] = self.nodes_gdf.index
        self.nodes_gdf = self.nodes_gdf.reset_index(drop=True)

        logger.info(f"Extracted {len(self.nodes_gdf)} nodes")

        return self.nodes_gdf

    def get_links_gdf(self) -> gpd.GeoDataFrame:
        """
        Get network edges/links as GeoDataFrame

        Returns:
            GeoDataFrame of links
        """
        if self.graph is None:
            raise ValueError("No network loaded. Call load_network_* first.")

        _, self.links_gdf = ox.graph_to_gdfs(self.graph)

        # Add link attributes
        self.links_gdf['link_id'] = range(len(self.links_gdf))
        self.links_gdf = self.links_gdf.reset_index()

        # Rename key columns for clarity
        if 'u' in self.links_gdf.columns:
            self.links_gdf = self.links_gdf.rename(columns={
                'u': 'from_node',
                'v': 'to_node',
                'length': 'length_m'
            })

        # Calculate additional link attributes
        if 'maxspeed' in self.links_gdf.columns:
            # Convert maxspeed to numeric (handle string values)
            self.links_gdf['speed_limit'] = pd.to_numeric(
                self.links_gdf['maxspeed'],
                errors='coerce'
            )
        else:
            # Default speeds by road type (km/h)
            speed_defaults = {
                'motorway': 100,
                'trunk': 80,
                'primary': 60,
                'secondary': 50,
                'tertiary': 40,
                'residential': 30,
                'unclassified': 30,
                'service': 20
            }

            if 'highway' in self.links_gdf.columns:
                self.links_gdf['speed_limit'] = self.links_gdf['highway'].apply(
                    lambda x: speed_defaults.get(
                        x[0] if isinstance(x, list) else x,
                        30
                    )
                )
            else:
                self.links_gdf['speed_limit'] = 30

        # Calculate free flow travel time (minutes)
        if 'length_m' in self.links_gdf.columns:
            self.links_gdf['fft_min'] = (
                self.links_gdf['length_m'] / 1000 /
                self.links_gdf['speed_limit'] * 60
            )

        # Add capacity estimates based on road type
        if 'lanes' in self.links_gdf.columns:
            self.links_gdf['lanes'] = pd.to_numeric(
                self.links_gdf['lanes'],
                errors='coerce'
            ).fillna(1)
        else:
            self.links_gdf['lanes'] = 1

        # Estimate capacity (vehicles per hour)
        self.links_gdf['capacity_vph'] = self.links_gdf['lanes'] * 1800

        logger.info(f"Extracted {len(self.links_gdf)} links")

        return self.links_gdf

    def get_nodes_and_links(self) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        Get both nodes and links as GeoDataFrames

        Returns:
            Tuple of (nodes_gdf, links_gdf)
        """
        nodes = self.get_nodes_gdf()
        links = self.get_links_gdf()

        return nodes, links

    def add_elevation_data(self):
        """Add elevation data to nodes using Google Elevation API"""
        if self.graph is None:
            raise ValueError("No network loaded. Call load_network_* first.")

        try:
            logger.info("Adding elevation data...")
            self.graph = ox.add_node_elevations_google(
                self.graph,
                api_key=None,  # Uses default/cached data
                max_locations_per_batch=350
            )
            logger.info("Elevation data added")
        except Exception as e:
            logger.warning(f"Could not add elevation data: {e}")

    def calculate_network_stats(self) -> Dict:
        """
        Calculate basic network statistics

        Returns:
            Dictionary of network statistics
        """
        if self.graph is None:
            raise ValueError("No network loaded. Call load_network_* first.")

        stats = ox.basic_stats(self.graph)

        # Add more statistics
        stats['total_nodes'] = len(self.graph.nodes)
        stats['total_edges'] = len(self.graph.edges)

        if self.links_gdf is not None:
            stats['total_length_km'] = self.links_gdf['length_m'].sum() / 1000
            stats['avg_link_length_m'] = self.links_gdf['length_m'].mean()

        logger.info("Network statistics calculated")

        return stats

    def save_network(self, filepath: str, format: str = 'graphml'):
        """
        Save network to file

        Args:
            filepath: Output file path
            format: File format ('graphml', 'shapefile', 'geopackage')
        """
        if self.graph is None:
            raise ValueError("No network loaded. Call load_network_* first.")

        try:
            if format == 'graphml':
                ox.save_graphml(self.graph, filepath)
            elif format == 'shapefile':
                ox.save_graph_shapefile(self.graph, filepath)
            elif format == 'geopackage':
                if self.nodes_gdf is None:
                    self.get_nodes_gdf()
                if self.links_gdf is None:
                    self.get_links_gdf()

                self.nodes_gdf.to_file(
                    f"{filepath}_nodes.gpkg",
                    driver='GPKG'
                )
                self.links_gdf.to_file(
                    f"{filepath}_links.gpkg",
                    driver='GPKG'
                )
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Network saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving network: {e}")
            raise

    def load_saved_network(self, filepath: str):
        """
        Load network from GraphML file

        Args:
            filepath: Path to GraphML file
        """
        try:
            self.graph = ox.load_graphml(filepath)
            logger.info(f"Network loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading network: {e}")
            raise
