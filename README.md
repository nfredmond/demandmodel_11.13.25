# Transportation Demand Model

A comprehensive Python application for building transportation demand models that automatically loads data from:
- **US Census API** - demographic and socioeconomic data
- **OpenStreetMap** - road network (nodes and links)
- **Census TIGER/Line** - Traffic Analysis Zone (TAZ) geographies

## Features

- 🌐 **Automatic Data Loading**: Fetches Census and OpenStreetMap data automatically
- 🗺️ **TAZ Management**: Creates and manages Traffic Analysis Zones from census geographies
- 🚗 **Network Analysis**: Processes road networks with nodes, links, and attributes
- 📊 **Demand Modeling**: Includes trip generation and distribution (gravity model)
- 💾 **Multiple Export Formats**: Export to CSV, GeoPackage, Shapefile
- 🎯 **Flexible Geography**: Load data by place name, bounding box, or custom polygon

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages

- `requests` - HTTP requests for Census API
- `pandas` - Data manipulation
- `geopandas` - Geospatial data handling
- `shapely` - Geometric operations
- `osmnx` - OpenStreetMap network data
- `numpy` - Numerical computing
- `censusdata` - Census API wrapper
- `folium` - Interactive mapping
- `networkx` - Network analysis
- `matplotlib` - Visualization

## Quick Start

### Basic Usage

```python
from demand_model import TransportationDemandModel

# Initialize with Census API key
model = TransportationDemandModel(
    census_api_key="your_api_key_here",
    project_name="my_model"
)

# Load study area by place name
model.load_study_area_by_place(
    place_name="Berkeley, California, USA",
    state_fips="06",  # California
    county_fips="001",  # Alameda County
    network_type='drive'
)

# Get summary statistics
stats = model.get_summary_stats()
print(stats)

# Export results
model.export_to_csv()
model.export_to_geopackage()
```

### Run Demo

```bash
# Run Berkeley demo
python examples/demo.py --demo berkeley

# Run San Francisco demo
python examples/demo.py --demo sf

# Run both demos
python examples/demo.py --demo both
```

## Census API Key

This project includes a Census API key in `firstfile.txt`. You can also get your own free API key from:
https://api.census.gov/data/key_signup.html

## Project Structure

```
demandmodel_11.13.25/
├── demand_model/           # Main package
│   ├── __init__.py
│   ├── census_loader.py   # Census API data loader
│   ├── osm_loader.py      # OpenStreetMap network loader
│   ├── taz_handler.py     # TAZ geography handler
│   └── demand_model.py    # Main demand model class
├── config/                 # Configuration
│   ├── __init__.py
│   └── config.py
├── examples/              # Example scripts
│   └── demo.py
├── output/                # Output directory (created automatically)
├── data/                  # Data cache (created automatically)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Data Components

### 1. Census Demographic Data

Automatically fetches from Census API:
- Total population
- Total employment
- Commuter statistics (transit, walk, bike)
- Median household income
- Housing units
- Worker counts

### 2. OpenStreetMap Network

Automatically downloads road network with:
- **Nodes**: Network intersections with coordinates
- **Links**: Road segments with attributes:
  - Length (meters)
  - Road type (highway classification)
  - Speed limits
  - Number of lanes
  - Estimated capacity

### 3. Traffic Analysis Zones (TAZ)

Creates TAZ from census geographies:
- Based on census tracts or block groups
- Includes demographic data
- Calculates centroids for OD matrices
- Supports custom TAZ boundaries

## Main Classes

### TransportationDemandModel

Main application class that orchestrates all components.

**Key Methods:**
- `load_study_area_by_place()` - Load data by place name
- `load_study_area_by_bbox()` - Load data by bounding box
- `estimate_trip_generation()` - Calculate trip productions/attractions
- `distribute_trips_gravity()` - Distribute trips using gravity model
- `export_to_csv()` - Export data to CSV files
- `export_to_geopackage()` - Export spatial data to GeoPackage

### CensusDataLoader

Handles Census API data retrieval.

**Key Methods:**
- `fetch_demographic_data()` - Fetch key demographic variables
- `get_geometry()` - Download census boundaries
- `get_demographic_geodataframe()` - Combined data and geometries

### OSMNetworkLoader

Manages OpenStreetMap network data.

**Key Methods:**
- `load_network_by_place()` - Download network for named place
- `load_network_by_bbox()` - Download network for bounding box
- `get_nodes_gdf()` - Extract nodes as GeoDataFrame
- `get_links_gdf()` - Extract links as GeoDataFrame
- `calculate_network_stats()` - Calculate network statistics

### TAZHandler

Manages Traffic Analysis Zones.

**Key Methods:**
- `create_taz_from_census()` - Create TAZ from census data
- `calculate_taz_centroids()` - Calculate TAZ centroids
- `assign_nodes_to_taz()` - Assign network nodes to TAZs
- `create_od_matrix_template()` - Create OD matrix structure

## Usage Examples

### Example 1: Load Study Area by Place Name

```python
from demand_model import TransportationDemandModel

model = TransportationDemandModel(
    census_api_key="your_key",
    project_name="oakland_model"
)

model.load_study_area_by_place(
    place_name="Oakland, California, USA",
    state_fips="06",
    county_fips="001",
    network_type='drive'
)
```

### Example 2: Load Study Area by Bounding Box

```python
model = TransportationDemandModel(
    census_api_key="your_key",
    project_name="custom_area"
)

model.load_study_area_by_bbox(
    north=37.9,
    south=37.8,
    east=-122.2,
    west=-122.3,
    state_fips="06",
    county_fips="001",
    network_type='all'
)
```

### Example 3: Run Complete Demand Model

```python
# Load study area
model.load_study_area_by_place(
    place_name="Berkeley, California, USA",
    state_fips="06",
    county_fips="001"
)

# Generate trips
trip_gen = model.estimate_trip_generation()

# Distribute trips
od_matrix = model.distribute_trips_gravity(
    trip_gen,
    friction_factor=1.5
)

# Export results
model.export_to_csv()
model.export_to_geopackage()
```

### Example 4: Analyze TAZ Statistics

```python
# Calculate TAZ-level statistics
taz_stats = model.calculate_taz_statistics()
print(taz_stats.head())

# Get centroids
centroids = model.taz_handler.calculate_taz_centroids()
print(centroids.head())
```

## Output Files

### CSV Files
- `{project}_taz.csv` - TAZ data with demographics
- `{project}_nodes.csv` - Network nodes
- `{project}_links.csv` - Network links
- `{project}_od_matrix.csv` - Origin-destination trip matrix

### GeoPackage
- `{project}.gpkg` - Spatial data with layers:
  - `taz` - TAZ polygons
  - `nodes` - Network nodes (points)
  - `links` - Network links (lines)

## State and County FIPS Codes

Common FIPS codes for California:
- **State**: 06
- **Alameda County**: 001
- **San Francisco County**: 075
- **Santa Clara County**: 085
- **Contra Costa County**: 013

Find more FIPS codes at: https://www.census.gov/geographies/reference-files/2021/demo/popest/2021-fips.html

## Network Types

OpenStreetMap network types:
- `drive` - Drivable roads only
- `walk` - Walkable paths
- `bike` - Bikeable paths
- `all` - All transportation modes

## Trip Generation

The model uses simplified ITE-based trip rates:
- **Productions**: 2.5 trips per person per day
- **Attractions**: 3.0 trips per employee per day

Productions and attractions are automatically balanced.

## Trip Distribution

Implements gravity model:
```
Trips(i,j) = Productions(i) * Attractions(j) / Distance(i,j)^friction_factor
```

Default friction factor: 1.0 (adjustable)

## Limitations

- Requires internet connection for data downloads
- Census data limited to US geographies
- OpenStreetMap coverage varies by location
- Simplified trip generation rates (not calibrated)
- Basic gravity model (no impedance matrices)

## Future Enhancements

- Mode choice modeling
- Route assignment
- Time-of-day modeling
- Calibration tools
- Integration with activity-based models
- Support for transit networks
- Integration with GTFS data

## Troubleshooting

### Census API Errors
- Verify your API key is valid
- Check FIPS codes are correct
- Ensure internet connection is active

### OSM Download Errors
- Try smaller geographic areas
- Check place name spelling
- Verify bounding box coordinates

### Memory Issues
- Reduce study area size
- Use simplified network (`simplify=True`)
- Process data in chunks

## License

This project is provided as-is for educational and research purposes.

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs and feature requests.

## Contact

For questions or support, please open an issue on the project repository.

## Acknowledgments

- US Census Bureau for demographic data API
- OpenStreetMap contributors for network data
- OSMnx library by Geoff Boeing
- Python geospatial community

## Version

Current version: 1.0.0

Last updated: November 2025
