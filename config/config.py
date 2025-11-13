"""
Configuration management for Transportation Demand Model
"""
import os

class Config:
    """Configuration class for the demand model application"""

    # Census API Configuration
    CENSUS_API_KEY = "be5b4855accd13808b0bd0f17311ee4b90392e39"
    CENSUS_BASE_URL = "https://api.census.gov/data"

    # Default Census variables to fetch
    CENSUS_VARIABLES = {
        'B01003_001E': 'total_population',
        'B08301_001E': 'total_commuters',
        'B08301_010E': 'public_transit_commuters',
        'B19013_001E': 'median_household_income',
        'B25001_001E': 'total_housing_units',
        'B08134_001E': 'total_employment'
    }

    # Geographic levels
    GEO_LEVELS = ['tract', 'block group', 'county']

    # OSM Configuration
    OSM_NETWORK_TYPES = ['drive', 'walk', 'bike', 'all']
    DEFAULT_NETWORK_TYPE = 'drive'

    # TAZ Configuration
    DEFAULT_TAZ_METHOD = 'census_tract'  # Can be 'census_tract', 'block_group', or 'custom'

    # Output Configuration
    OUTPUT_DIR = 'output'
    DATA_DIR = 'data'

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)

    @classmethod
    def set_census_api_key(cls, api_key):
        """Set Census API key"""
        cls.CENSUS_API_KEY = api_key
