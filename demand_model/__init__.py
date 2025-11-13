"""
Transportation Demand Model Package
Automatically loads Census API data, OpenStreetMap networks, and TAZ geographies
"""
from .demand_model import TransportationDemandModel
from .census_loader import CensusDataLoader
from .osm_loader import OSMNetworkLoader
from .taz_handler import TAZHandler

__version__ = "1.0.0"

__all__ = [
    'TransportationDemandModel',
    'CensusDataLoader',
    'OSMNetworkLoader',
    'TAZHandler'
]
