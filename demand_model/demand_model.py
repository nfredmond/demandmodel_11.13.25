"""
Transportation Demand Model
Main application class that orchestrates data loading and model components
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple, List
import logging
import os

from .census_loader import CensusDataLoader
from .osm_loader import OSMNetworkLoader
from .taz_handler import TAZHandler
from .visualizer import DemandModelVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransportationDemandModel:
    """
    Main Transportation Demand Model class
    Integrates Census data, OSM network, and TAZ geographies
    """

    def __init__(self, census_api_key: str, project_name: str = "demand_model"):
        """
        Initialize Transportation Demand Model

        Args:
            census_api_key: Census API key
            project_name: Name of the project
        """
        self.project_name = project_name
        self.census_loader = CensusDataLoader(census_api_key)
        self.network_loader = OSMNetworkLoader()
        self.taz_handler = TAZHandler()
        self.visualizer = DemandModelVisualizer()

        # Data containers
        self.demographic_data = None
        self.network_graph = None
        self.nodes_gdf = None
        self.links_gdf = None
        self.taz_gdf = None
        self.od_matrix = None

        # Create output directories
        self.output_dir = f"output/{project_name}"
        self.data_dir = f"data/{project_name}"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Set visualizer output directory
        self.visualizer.output_dir = self.output_dir

        logger.info(f"Initialized Transportation Demand Model: {project_name}")

    def load_study_area_by_place(
        self,
        place_name: str,
        state_fips: str,
        county_fips: Optional[str] = None,
        network_type: str = 'drive'
    ):
        """
        Load complete study area data by place name

        Args:
            place_name: Name of place for OSM (e.g., "Berkeley, California, USA")
            state_fips: State FIPS code for Census (e.g., '06')
            county_fips: County FIPS code for Census (optional)
            network_type: OSM network type ('drive', 'walk', 'bike', 'all')
        """
        logger.info(f"Loading study area: {place_name}")

        # Load Census demographic data
        logger.info("Step 1/3: Loading Census demographic data...")
        self.demographic_data = self.census_loader.get_demographic_geodataframe(
            state=state_fips,
            county=county_fips,
            geo_level='tract'
        )

        # Load OSM network
        logger.info("Step 2/3: Loading OpenStreetMap network...")
        self.network_graph = self.network_loader.load_network_by_place(
            place_name,
            network_type=network_type
        )
        self.nodes_gdf, self.links_gdf = self.network_loader.get_nodes_and_links()

        # Create TAZ from census tracts
        logger.info("Step 3/3: Creating Traffic Analysis Zones...")
        self.taz_gdf = self.taz_handler.create_taz_from_census(
            self.demographic_data,
            method='direct'
        )

        logger.info("Study area loaded successfully!")
        self._print_summary()

    def load_study_area_by_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        state_fips: str,
        county_fips: Optional[str] = None,
        network_type: str = 'drive'
    ):
        """
        Load complete study area data by bounding box

        Args:
            north: Northern latitude
            south: Southern latitude
            east: Eastern longitude
            west: Western longitude
            state_fips: State FIPS code for Census
            county_fips: County FIPS code for Census (optional)
            network_type: OSM network type
        """
        logger.info("Loading study area by bounding box")

        # Load Census demographic data
        logger.info("Step 1/3: Loading Census demographic data...")
        self.demographic_data = self.census_loader.get_demographic_geodataframe(
            state=state_fips,
            county=county_fips,
            geo_level='tract'
        )

        # Filter demographic data to bounding box
        self.demographic_data = self.demographic_data.cx[west:east, south:north]

        # Load OSM network
        logger.info("Step 2/3: Loading OpenStreetMap network...")
        self.network_graph = self.network_loader.load_network_by_bbox(
            north, south, east, west,
            network_type=network_type
        )
        self.nodes_gdf, self.links_gdf = self.network_loader.get_nodes_and_links()

        # Create TAZ from census tracts
        logger.info("Step 3/3: Creating Traffic Analysis Zones...")
        self.taz_gdf = self.taz_handler.create_taz_from_census(
            self.demographic_data,
            method='direct'
        )

        logger.info("Study area loaded successfully!")
        self._print_summary()

    def assign_nodes_to_taz(self):
        """Assign network nodes to TAZs"""
        if self.nodes_gdf is None or self.taz_gdf is None:
            raise ValueError("Load study area first")

        logger.info("Assigning nodes to TAZs...")
        self.nodes_gdf = self.taz_handler.assign_nodes_to_taz(self.nodes_gdf)

    def calculate_taz_statistics(self) -> pd.DataFrame:
        """
        Calculate TAZ-level statistics

        Returns:
            DataFrame with TAZ statistics
        """
        if self.taz_gdf is None:
            raise ValueError("Load study area first")

        return self.taz_handler.calculate_taz_statistics()

    def create_od_matrix(self) -> pd.DataFrame:
        """
        Create origin-destination matrix template

        Returns:
            DataFrame with OD pairs
        """
        if self.taz_gdf is None:
            raise ValueError("Load study area first")

        self.od_matrix = self.taz_handler.create_od_matrix_template()
        return self.od_matrix

    def estimate_trip_generation(self) -> pd.DataFrame:
        """
        Estimate trip generation (productions and attractions) by TAZ
        Uses simple ITE-based trip rates

        Returns:
            DataFrame with trip productions and attractions by TAZ
        """
        if self.taz_gdf is None:
            raise ValueError("Load study area first")

        logger.info("Estimating trip generation...")

        trip_gen = self.taz_gdf[['TAZ_ID']].copy()

        # Trip production rates (trips per person per day)
        if 'total_population' in self.taz_gdf.columns:
            trip_gen['productions'] = (
                self.taz_gdf['total_population'] * 2.5  # Average trips per person
            )
        else:
            trip_gen['productions'] = 0

        # Trip attraction rates (trips per employee per day)
        if 'total_employment' in self.taz_gdf.columns:
            trip_gen['attractions'] = (
                self.taz_gdf['total_employment'] * 3.0  # Average trips per employee
            )
        else:
            trip_gen['attractions'] = 0

        # Balance productions and attractions
        total_prod = trip_gen['productions'].sum()
        total_attr = trip_gen['attractions'].sum()

        if total_attr > 0:
            balance_factor = total_prod / total_attr
            trip_gen['attractions'] = trip_gen['attractions'] * balance_factor

        logger.info(
            f"Trip generation complete: "
            f"{trip_gen['productions'].sum():.0f} total trips"
        )

        return trip_gen

    def distribute_trips_gravity(
        self,
        trip_gen: pd.DataFrame,
        friction_factor: float = 1.0
    ) -> pd.DataFrame:
        """
        Distribute trips using gravity model

        Args:
            trip_gen: DataFrame with productions and attractions by TAZ
            friction_factor: Friction factor for distance decay

        Returns:
            DataFrame with OD matrix
        """
        if self.taz_gdf is None:
            raise ValueError("Load study area first")

        logger.info("Distributing trips using gravity model...")

        # Calculate centroid-to-centroid distances
        centroids = self.taz_handler.calculate_taz_centroids()

        # Create OD matrix
        od_list = []

        for _, orig in trip_gen.iterrows():
            orig_taz = orig['TAZ_ID']
            orig_prod = orig['productions']

            if orig_prod == 0:
                continue

            # Get origin centroid
            orig_centroid = centroids[centroids['TAZ_ID'] == orig_taz]
            if len(orig_centroid) == 0:
                continue

            orig_x = orig_centroid['centroid_x'].values[0]
            orig_y = orig_centroid['centroid_y'].values[0]

            # Calculate impedance to all destinations
            impedances = []

            for _, dest in trip_gen.iterrows():
                dest_taz = dest['TAZ_ID']
                dest_attr = dest['attractions']

                if dest_attr == 0:
                    impedances.append(0)
                    continue

                # Get destination centroid
                dest_centroid = centroids[centroids['TAZ_ID'] == dest_taz]
                if len(dest_centroid) == 0:
                    impedances.append(0)
                    continue

                dest_x = dest_centroid['centroid_x'].values[0]
                dest_y = dest_centroid['centroid_y'].values[0]

                # Calculate Euclidean distance
                distance = np.sqrt((orig_x - dest_x)**2 + (orig_y - dest_y)**2)

                # Apply friction factor
                if distance > 0:
                    impedance = dest_attr / (distance ** friction_factor)
                else:
                    impedance = dest_attr * 1000  # High value for intra-zonal

                impedances.append(impedance)

            # Normalize impedances
            total_impedance = sum(impedances)

            if total_impedance == 0:
                continue

            # Distribute trips
            for idx, dest in trip_gen.iterrows():
                dest_taz = dest['TAZ_ID']
                trips = orig_prod * (impedances[idx] / total_impedance)

                if trips > 0.1:  # Ignore very small trip values
                    od_list.append({
                        'origin_taz': orig_taz,
                        'dest_taz': dest_taz,
                        'trips': trips
                    })

        self.od_matrix = pd.DataFrame(od_list)

        logger.info(
            f"Trip distribution complete: "
            f"{len(self.od_matrix)} OD pairs with trips"
        )

        return self.od_matrix

    def export_to_csv(self, prefix: Optional[str] = None):
        """
        Export all data to CSV files

        Args:
            prefix: Optional prefix for filenames
        """
        prefix = prefix or self.project_name

        logger.info("Exporting data to CSV...")

        if self.taz_gdf is not None:
            # Export TAZ data (non-spatial)
            taz_df = pd.DataFrame(self.taz_gdf.drop(columns='geometry'))
            taz_df.to_csv(f"{self.output_dir}/{prefix}_taz.csv", index=False)

        if self.nodes_gdf is not None:
            nodes_df = pd.DataFrame(self.nodes_gdf.drop(columns='geometry'))
            nodes_df.to_csv(f"{self.output_dir}/{prefix}_nodes.csv", index=False)

        if self.links_gdf is not None:
            links_df = pd.DataFrame(self.links_gdf.drop(columns='geometry'))
            links_df.to_csv(f"{self.output_dir}/{prefix}_links.csv", index=False)

        if self.od_matrix is not None:
            self.od_matrix.to_csv(
                f"{self.output_dir}/{prefix}_od_matrix.csv",
                index=False
            )

        logger.info(f"Data exported to {self.output_dir}/")

    def export_to_geopackage(self, filename: Optional[str] = None):
        """
        Export spatial data to GeoPackage

        Args:
            filename: Output filename (default: project_name.gpkg)
        """
        filename = filename or f"{self.project_name}.gpkg"
        filepath = f"{self.output_dir}/{filename}"

        logger.info(f"Exporting to GeoPackage: {filepath}")

        if self.taz_gdf is not None:
            self.taz_gdf.to_file(filepath, layer='taz', driver='GPKG')

        if self.nodes_gdf is not None:
            self.nodes_gdf.to_file(filepath, layer='nodes', driver='GPKG')

        if self.links_gdf is not None:
            self.links_gdf.to_file(filepath, layer='links', driver='GPKG')

        logger.info(f"Spatial data exported to {filepath}")

    def _print_summary(self):
        """Print summary of loaded data"""
        logger.info("=" * 60)
        logger.info("DATA SUMMARY")
        logger.info("=" * 60)

        if self.demographic_data is not None:
            logger.info(f"Census Tracts: {len(self.demographic_data)}")
            if 'total_population' in self.demographic_data.columns:
                total_pop = self.demographic_data['total_population'].sum()
                logger.info(f"Total Population: {total_pop:,.0f}")

        if self.network_graph is not None:
            logger.info(f"Network Nodes: {len(self.network_graph.nodes):,}")
            logger.info(f"Network Links: {len(self.network_graph.edges):,}")

        if self.links_gdf is not None and 'length_m' in self.links_gdf.columns:
            total_length = self.links_gdf['length_m'].sum() / 1000
            logger.info(f"Total Network Length: {total_length:,.1f} km")

        if self.taz_gdf is not None:
            logger.info(f"Traffic Analysis Zones: {len(self.taz_gdf)}")

        logger.info("=" * 60)

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics

        Returns:
            Dictionary with summary statistics
        """
        stats = {
            'project_name': self.project_name,
        }

        if self.demographic_data is not None:
            stats['num_census_tracts'] = len(self.demographic_data)
            if 'total_population' in self.demographic_data.columns:
                stats['total_population'] = int(
                    self.demographic_data['total_population'].sum()
                )

        if self.network_graph is not None:
            stats['num_nodes'] = len(self.network_graph.nodes)
            stats['num_links'] = len(self.network_graph.edges)

        if self.links_gdf is not None and 'length_m' in self.links_gdf.columns:
            stats['total_network_length_km'] = (
                self.links_gdf['length_m'].sum() / 1000
            )

        if self.taz_gdf is not None:
            stats['num_taz'] = len(self.taz_gdf)

        if self.od_matrix is not None:
            stats['num_od_pairs'] = len(self.od_matrix)
            stats['total_trips'] = self.od_matrix['trips'].sum()

        return stats

    def create_visualizations(
        self,
        create_maps: bool = True,
        create_plots: bool = True
    ) -> Dict[str, str]:
        """
        Create all visualizations for the model

        Args:
            create_maps: Whether to create interactive maps
            create_plots: Whether to create static plots

        Returns:
            Dictionary with paths to created visualizations
        """
        if self.taz_gdf is None or self.links_gdf is None:
            raise ValueError("Load study area first")

        logger.info("Creating visualizations...")

        output_files = {}

        if create_maps:
            # TAZ map
            if self.taz_gdf is not None and 'total_population' in self.taz_gdf.columns:
                logger.info("Creating TAZ population map...")
                taz_map_path = f"{self.output_dir}/map_taz_population.html"
                self.visualizer.create_taz_map(
                    self.taz_gdf,
                    variable='total_population',
                    title=f"{self.project_name}: Population by TAZ",
                    save_path=taz_map_path
                )
                output_files['taz_population_map'] = taz_map_path

            # Employment map
            if self.taz_gdf is not None and 'total_employment' in self.taz_gdf.columns:
                logger.info("Creating TAZ employment map...")
                employment_map_path = f"{self.output_dir}/map_taz_employment.html"
                self.visualizer.create_taz_map(
                    self.taz_gdf,
                    variable='total_employment',
                    title=f"{self.project_name}: Employment by TAZ",
                    save_path=employment_map_path
                )
                output_files['taz_employment_map'] = employment_map_path

            # Network map
            if self.links_gdf is not None and self.nodes_gdf is not None:
                logger.info("Creating network map...")
                network_map_path = f"{self.output_dir}/map_network.html"
                self.visualizer.create_network_map(
                    self.nodes_gdf,
                    self.links_gdf,
                    title=f"{self.project_name}: Road Network",
                    save_path=network_map_path
                )
                output_files['network_map'] = network_map_path

            # Combined map
            if self.taz_gdf is not None and self.links_gdf is not None:
                logger.info("Creating combined map...")
                combined_map_path = f"{self.output_dir}/map_combined.html"
                self.visualizer.create_combined_map(
                    self.taz_gdf,
                    self.links_gdf,
                    variable='total_population',
                    title=f"{self.project_name}: TAZ and Network",
                    save_path=combined_map_path
                )
                output_files['combined_map'] = combined_map_path

        if create_plots:
            # TAZ statistics plots
            if self.taz_gdf is not None:
                logger.info("Creating TAZ statistics plots...")
                taz_stats = self.calculate_taz_statistics()
                taz_plot_path = f"{self.output_dir}/plot_taz_statistics.png"
                self.visualizer.plot_taz_statistics(taz_stats, save_path=taz_plot_path)
                output_files['taz_statistics_plot'] = taz_plot_path

            # Network statistics plots
            if self.links_gdf is not None:
                logger.info("Creating network statistics plots...")
                network_plot_path = f"{self.output_dir}/plot_network_statistics.png"
                self.visualizer.plot_network_statistics(self.links_gdf, save_path=network_plot_path)
                output_files['network_statistics_plot'] = network_plot_path

            # OD flow plots
            if self.od_matrix is not None and len(self.od_matrix) > 0:
                logger.info("Creating OD flow plots...")
                od_plot_path = f"{self.output_dir}/plot_od_flows.png"
                self.visualizer.plot_od_flows(self.od_matrix, save_path=od_plot_path)
                output_files['od_flows_plot'] = od_plot_path

        logger.info(f"Created {len(output_files)} visualizations")
        return output_files

    def create_taz_map(
        self,
        variable: str = 'total_population',
        save_path: Optional[str] = None
    ):
        """
        Create interactive map of TAZ data

        Args:
            variable: Variable to visualize
            save_path: Path to save HTML file

        Returns:
            Folium map object
        """
        if self.taz_gdf is None:
            raise ValueError("Load study area first")

        if save_path is None:
            save_path = f"{self.output_dir}/map_taz_{variable}.html"

        return self.visualizer.create_taz_map(
            self.taz_gdf,
            variable=variable,
            save_path=save_path
        )

    def create_network_map(self, save_path: Optional[str] = None):
        """
        Create interactive map of road network

        Args:
            save_path: Path to save HTML file

        Returns:
            Folium map object
        """
        if self.links_gdf is None or self.nodes_gdf is None:
            raise ValueError("Load study area first")

        if save_path is None:
            save_path = f"{self.output_dir}/map_network.html"

        return self.visualizer.create_network_map(
            self.nodes_gdf,
            self.links_gdf,
            save_path=save_path
        )

    def create_combined_map(
        self,
        variable: str = 'total_population',
        save_path: Optional[str] = None
    ):
        """
        Create map with both TAZ and network layers

        Args:
            variable: Variable to visualize on TAZ
            save_path: Path to save HTML file

        Returns:
            Folium map object
        """
        if self.taz_gdf is None or self.links_gdf is None:
            raise ValueError("Load study area first")

        if save_path is None:
            save_path = f"{self.output_dir}/map_combined.html"

        return self.visualizer.create_combined_map(
            self.taz_gdf,
            self.links_gdf,
            variable=variable,
            save_path=save_path
        )
