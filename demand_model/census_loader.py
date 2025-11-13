"""
Census API Data Loader
Fetches demographic and socioeconomic data from the US Census Bureau API
"""
import requests
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CensusDataLoader:
    """
    Loads demographic data from the US Census API
    Supports American Community Survey (ACS) 5-year estimates
    """

    def __init__(self, api_key: str):
        """
        Initialize Census Data Loader

        Args:
            api_key: Census API key
        """
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data"
        self.year = 2021  # Default to 2021 ACS 5-year estimates
        self.dataset = "acs/acs5"

    def set_year(self, year: int):
        """Set the year for data retrieval"""
        self.year = year
        logger.info(f"Census year set to {year}")

    def get_variables_info(self) -> pd.DataFrame:
        """
        Get information about available Census variables

        Returns:
            DataFrame with variable information
        """
        url = f"{self.base_url}/{self.year}/{self.dataset}/variables.json"
        response = requests.get(url)
        response.raise_for_status()

        variables = response.json()['variables']
        var_list = []

        for var_id, var_info in variables.items():
            if 'label' in var_info:
                var_list.append({
                    'variable_id': var_id,
                    'label': var_info.get('label', ''),
                    'concept': var_info.get('concept', '')
                })

        return pd.DataFrame(var_list)

    def fetch_data(
        self,
        variables: List[str],
        state: str,
        county: Optional[str] = None,
        tract: Optional[str] = "*",
        geo_level: str = "tract"
    ) -> pd.DataFrame:
        """
        Fetch Census data for specified geography

        Args:
            variables: List of Census variable codes (e.g., ['B01003_001E'])
            state: State FIPS code (e.g., '06' for California)
            county: County FIPS code (e.g., '001', or None for all counties)
            tract: Tract code (e.g., '*' for all tracts)
            geo_level: Geographic level ('tract', 'block group', 'county')

        Returns:
            DataFrame with Census data
        """
        # Build the geographic query
        if geo_level == "tract":
            geo_for = f"tract:{tract}"
            geo_in = f"state:{state}"
            if county:
                geo_in += f"+county:{county}"
        elif geo_level == "block group":
            geo_for = f"block group:*"
            geo_in = f"state:{state}"
            if county:
                geo_in += f"+county:{county}+tract:*"
        elif geo_level == "county":
            geo_for = f"county:*"
            geo_in = f"state:{state}"
        else:
            raise ValueError(f"Unsupported geo_level: {geo_level}")

        # Build request URL
        var_string = ",".join(variables)
        url = (
            f"{self.base_url}/{self.year}/{self.dataset}"
            f"?get={var_string}"
            f"&for={geo_for}"
            f"&in={geo_in}"
            f"&key={self.api_key}"
        )

        logger.info(f"Fetching Census data from {url[:100]}...")

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Convert to DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])

            # Create GEOID for joining with spatial data
            if geo_level == "tract":
                df['GEOID'] = df['state'] + df['county'] + df['tract']
            elif geo_level == "block group":
                df['GEOID'] = df['state'] + df['county'] + df['tract'] + df['block group']
            elif geo_level == "county":
                df['GEOID'] = df['state'] + df['county']

            # Convert numeric columns
            for var in variables:
                if var in df.columns:
                    df[var] = pd.to_numeric(df[var], errors='coerce')

            logger.info(f"Successfully fetched {len(df)} records")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Census data: {e}")
            raise

    def fetch_demographic_data(
        self,
        state: str,
        county: Optional[str] = None,
        geo_level: str = "tract"
    ) -> pd.DataFrame:
        """
        Fetch key demographic variables for transportation demand modeling

        Args:
            state: State FIPS code
            county: County FIPS code (optional)
            geo_level: Geographic level

        Returns:
            DataFrame with demographic data
        """
        # Key variables for transportation demand modeling
        variables = [
            'B01003_001E',  # Total population
            'B08301_001E',  # Total commuters
            'B08301_010E',  # Public transit commuters
            'B08301_019E',  # Walk commuters
            'B08301_018E',  # Bicycle commuters
            'B19013_001E',  # Median household income
            'B25001_001E',  # Total housing units
            'B08134_001E',  # Total employment
            'B08303_001E',  # Total workers (travel time)
            'B25044_001E',  # Total occupied housing units (vehicles available)
        ]

        df = self.fetch_data(variables, state, county, geo_level=geo_level)

        # Rename columns for clarity
        column_mapping = {
            'B01003_001E': 'total_population',
            'B08301_001E': 'total_commuters',
            'B08301_010E': 'transit_commuters',
            'B08301_019E': 'walk_commuters',
            'B08301_018E': 'bike_commuters',
            'B19013_001E': 'median_income',
            'B25001_001E': 'housing_units',
            'B08134_001E': 'total_employment',
            'B08303_001E': 'workers',
            'B25044_001E': 'occupied_housing_units',
        }

        df = df.rename(columns=column_mapping)

        return df

    def get_geometry(
        self,
        state: str,
        county: Optional[str] = None,
        geo_level: str = "tract"
    ) -> gpd.GeoDataFrame:
        """
        Fetch geographic boundaries from Census TIGER/Line files

        Args:
            state: State FIPS code
            county: County FIPS code (optional)
            geo_level: Geographic level

        Returns:
            GeoDataFrame with geometries
        """
        import warnings
        warnings.filterwarnings('ignore')

        try:
            # Use Census TIGER/Line web service
            year = self.year

            if geo_level == "tract":
                if county:
                    url = (
                        f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/"
                        f"tl_{year}_{state}_tract.zip"
                    )
                else:
                    url = (
                        f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/"
                        f"tl_{year}_{state}_tract.zip"
                    )
            elif geo_level == "block group":
                url = (
                    f"https://www2.census.gov/geo/tiger/TIGER{year}/BG/"
                    f"tl_{year}_{state}_bg.zip"
                )
            elif geo_level == "county":
                url = (
                    f"https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/"
                    f"tl_{year}_us_county.zip"
                )
            else:
                raise ValueError(f"Unsupported geo_level: {geo_level}")

            logger.info(f"Downloading geometry from {url}...")
            gdf = gpd.read_file(url)

            # Filter by state and county if needed
            if geo_level == "county":
                gdf = gdf[gdf['STATEFP'] == state]
            if county and geo_level in ["tract", "block group"]:
                gdf = gdf[gdf['COUNTYFP'] == county]

            logger.info(f"Successfully loaded {len(gdf)} geometries")
            return gdf

        except Exception as e:
            logger.error(f"Error fetching geometry: {e}")
            raise

    def get_demographic_geodataframe(
        self,
        state: str,
        county: Optional[str] = None,
        geo_level: str = "tract"
    ) -> gpd.GeoDataFrame:
        """
        Fetch demographic data with geometries

        Args:
            state: State FIPS code
            county: County FIPS code (optional)
            geo_level: Geographic level

        Returns:
            GeoDataFrame with demographic data and geometries
        """
        # Fetch demographic data
        demo_df = self.fetch_demographic_data(state, county, geo_level)

        # Fetch geometries
        geo_gdf = self.get_geometry(state, county, geo_level)

        # Merge
        gdf = geo_gdf.merge(demo_df, on='GEOID', how='inner')

        logger.info(f"Created GeoDataFrame with {len(gdf)} features")
        return gdf
