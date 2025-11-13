"""
Traffic Analysis Zone (TAZ) Handler
Manages TAZ geographies and aggregates data to TAZ level
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
from typing import Optional, List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TAZHandler:
    """
    Handles Traffic Analysis Zone (TAZ) operations
    Supports creating TAZs from census geographies or custom polygons
    """

    def __init__(self):
        """Initialize TAZ Handler"""
        self.taz_gdf = None
        self.taz_data = None

    def create_taz_from_census(
        self,
        census_gdf: gpd.GeoDataFrame,
        method: str = 'direct'
    ) -> gpd.GeoDataFrame:
        """
        Create TAZs from census geographies

        Args:
            census_gdf: GeoDataFrame with census data and geometries
            method: 'direct' (use census tracts as TAZs) or
                   'aggregate' (combine multiple tracts)

        Returns:
            GeoDataFrame with TAZ geometries and data
        """
        if method == 'direct':
            # Use census geographies directly as TAZs
            self.taz_gdf = census_gdf.copy()
            self.taz_gdf['TAZ_ID'] = range(1, len(self.taz_gdf) + 1)

            logger.info(f"Created {len(self.taz_gdf)} TAZs from census data")

        elif method == 'aggregate':
            # Placeholder for aggregation logic
            # Could aggregate by county, zip code, etc.
            logger.warning("Aggregation method not yet implemented, using direct method")
            self.taz_gdf = census_gdf.copy()
            self.taz_gdf['TAZ_ID'] = range(1, len(self.taz_gdf) + 1)

        else:
            raise ValueError(f"Unsupported method: {method}")

        return self.taz_gdf

    def load_custom_taz(
        self,
        taz_file: str,
        id_column: str = 'TAZ_ID'
    ) -> gpd.GeoDataFrame:
        """
        Load TAZ from external file

        Args:
            taz_file: Path to TAZ shapefile/geopackage
            id_column: Name of TAZ ID column

        Returns:
            GeoDataFrame with TAZ geometries
        """
        try:
            self.taz_gdf = gpd.read_file(taz_file)

            # Ensure TAZ_ID column exists
            if id_column not in self.taz_gdf.columns:
                raise ValueError(f"Column {id_column} not found in TAZ file")

            if id_column != 'TAZ_ID':
                self.taz_gdf = self.taz_gdf.rename(columns={id_column: 'TAZ_ID'})

            logger.info(f"Loaded {len(self.taz_gdf)} TAZs from {taz_file}")

            return self.taz_gdf

        except Exception as e:
            logger.error(f"Error loading TAZ file: {e}")
            raise

    def aggregate_data_to_taz(
        self,
        data_gdf: gpd.GeoDataFrame,
        variables: List[str],
        method: str = 'sum'
    ) -> gpd.GeoDataFrame:
        """
        Aggregate data from smaller geographies to TAZ level

        Args:
            data_gdf: GeoDataFrame with data to aggregate
            variables: List of variable names to aggregate
            method: Aggregation method ('sum', 'mean', 'weighted_mean')

        Returns:
            GeoDataFrame with aggregated data at TAZ level
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        # Spatial join to find which data geometries fall in which TAZs
        joined = gpd.sjoin(
            data_gdf,
            self.taz_gdf[['TAZ_ID', 'geometry']],
            how='inner',
            predicate='intersects'
        )

        # Aggregate by TAZ
        if method == 'sum':
            agg_data = joined.groupby('TAZ_ID')[variables].sum()
        elif method == 'mean':
            agg_data = joined.groupby('TAZ_ID')[variables].mean()
        elif method == 'weighted_mean':
            # Use area weighting
            logger.warning("Weighted mean not yet implemented, using sum")
            agg_data = joined.groupby('TAZ_ID')[variables].sum()
        else:
            raise ValueError(f"Unsupported method: {method}")

        # Merge with TAZ geometries
        result_gdf = self.taz_gdf.merge(agg_data, on='TAZ_ID', how='left')

        # Fill NaN values with 0
        for var in variables:
            if var in result_gdf.columns:
                result_gdf[var] = result_gdf[var].fillna(0)

        logger.info(f"Aggregated data to {len(result_gdf)} TAZs")

        return result_gdf

    def calculate_taz_centroids(self) -> pd.DataFrame:
        """
        Calculate centroids of TAZs

        Returns:
            DataFrame with TAZ_ID, centroid_x, centroid_y
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        centroids = self.taz_gdf.copy()
        centroids['centroid'] = centroids.geometry.centroid
        centroids['centroid_x'] = centroids['centroid'].x
        centroids['centroid_y'] = centroids['centroid'].y

        result = centroids[['TAZ_ID', 'centroid_x', 'centroid_y']]

        logger.info(f"Calculated centroids for {len(result)} TAZs")

        return result

    def assign_nodes_to_taz(
        self,
        nodes_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Assign network nodes to TAZs

        Args:
            nodes_gdf: GeoDataFrame of network nodes

        Returns:
            GeoDataFrame of nodes with TAZ_ID assigned
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        # Ensure both have same CRS
        if nodes_gdf.crs != self.taz_gdf.crs:
            nodes_gdf = nodes_gdf.to_crs(self.taz_gdf.crs)

        # Spatial join
        nodes_with_taz = gpd.sjoin(
            nodes_gdf,
            self.taz_gdf[['TAZ_ID', 'geometry']],
            how='left',
            predicate='within'
        )

        logger.info(
            f"Assigned {nodes_with_taz['TAZ_ID'].notna().sum()} nodes to TAZs"
        )

        return nodes_with_taz

    def calculate_taz_statistics(self) -> pd.DataFrame:
        """
        Calculate basic statistics for each TAZ

        Returns:
            DataFrame with TAZ statistics
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        stats = self.taz_gdf.copy()

        # Calculate area
        stats['area_sq_km'] = stats.geometry.area / 1_000_000

        # Calculate perimeter
        stats['perimeter_km'] = stats.geometry.length / 1000

        # Demographic statistics if available
        demographic_vars = [
            'total_population', 'total_employment',
            'housing_units', 'median_income'
        ]

        stats_dict = {'TAZ_ID': stats['TAZ_ID']}
        stats_dict['area_sq_km'] = stats['area_sq_km']
        stats_dict['perimeter_km'] = stats['perimeter_km']

        for var in demographic_vars:
            if var in stats.columns:
                stats_dict[var] = stats[var]

        result = pd.DataFrame(stats_dict)

        # Calculate density metrics
        if 'total_population' in result.columns:
            result['pop_density'] = (
                result['total_population'] / result['area_sq_km']
            )

        if 'total_employment' in result.columns:
            result['emp_density'] = (
                result['total_employment'] / result['area_sq_km']
            )

        logger.info(f"Calculated statistics for {len(result)} TAZs")

        return result

    def create_od_matrix_template(self) -> pd.DataFrame:
        """
        Create empty origin-destination matrix template

        Returns:
            DataFrame with origin TAZ, destination TAZ, and trip columns
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        taz_ids = self.taz_gdf['TAZ_ID'].tolist()

        # Create all combinations
        od_pairs = [
            (o, d) for o in taz_ids for d in taz_ids
        ]

        od_matrix = pd.DataFrame(od_pairs, columns=['origin_taz', 'dest_taz'])
        od_matrix['trips'] = 0.0

        logger.info(
            f"Created OD matrix template with {len(od_matrix)} OD pairs "
            f"({len(taz_ids)} TAZs)"
        )

        return od_matrix

    def save_taz(self, filepath: str, format: str = 'gpkg'):
        """
        Save TAZ to file

        Args:
            filepath: Output file path
            format: File format ('gpkg', 'shp', 'geojson')
        """
        if self.taz_gdf is None:
            raise ValueError("No TAZ defined. Call create_taz_from_census first.")

        try:
            if format == 'gpkg':
                self.taz_gdf.to_file(filepath, driver='GPKG')
            elif format == 'shp':
                self.taz_gdf.to_file(filepath, driver='ESRI Shapefile')
            elif format == 'geojson':
                self.taz_gdf.to_file(filepath, driver='GeoJSON')
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"TAZ saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving TAZ: {e}")
            raise

    def load_taz(self, filepath: str):
        """
        Load TAZ from file

        Args:
            filepath: Path to TAZ file
        """
        try:
            self.taz_gdf = gpd.read_file(filepath)

            if 'TAZ_ID' not in self.taz_gdf.columns:
                # Try to find an ID column
                id_cols = [col for col in self.taz_gdf.columns if 'id' in col.lower()]
                if id_cols:
                    self.taz_gdf['TAZ_ID'] = self.taz_gdf[id_cols[0]]
                else:
                    self.taz_gdf['TAZ_ID'] = range(1, len(self.taz_gdf) + 1)

            logger.info(f"Loaded {len(self.taz_gdf)} TAZs from {filepath}")

        except Exception as e:
            logger.error(f"Error loading TAZ: {e}")
            raise
