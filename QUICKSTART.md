# Quick Start Guide

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Model

### Option 1: Use the Command Line Interface (Easiest)

```bash
# Load data for Berkeley, CA
python run_model.py --place "Berkeley, California, USA" --state 06 --county 001

# Load data for a custom bounding box (San Francisco downtown)
python run_model.py --bbox 37.8 37.78 -122.39 -122.41 --state 06 --county 075

# Load all network types (drive, walk, bike)
python run_model.py --place "Oakland, CA, USA" --state 06 --county 001 --network all
```

### Option 2: Run the Demo Script

```bash
# Run Berkeley demo
python examples/demo.py --demo berkeley

# Run San Francisco demo
python examples/demo.py --demo sf

# Run both demos
python examples/demo.py --demo both
```

### Option 3: Use Python Code

```python
from demand_model import TransportationDemandModel

# Initialize
model = TransportationDemandModel(
    census_api_key="be5b4855accd13808b0bd0f17311ee4b90392e39",
    project_name="my_model"
)

# Load study area
model.load_study_area_by_place(
    place_name="Berkeley, California, USA",
    state_fips="06",
    county_fips="001",
    network_type='drive'
)

# Generate and distribute trips
trip_gen = model.estimate_trip_generation()
od_matrix = model.distribute_trips_gravity(trip_gen)

# Export results
model.export_to_csv()
model.export_to_geopackage()
```

## Output Files

All outputs are saved to `output/{project_name}/`:

- **CSV files:**
  - `{project}_taz.csv` - Traffic Analysis Zones with demographic data
  - `{project}_nodes.csv` - Network nodes
  - `{project}_links.csv` - Network links/edges
  - `{project}_od_matrix.csv` - Origin-Destination trip matrix

- **GeoPackage (for GIS):**
  - `{project}.gpkg` - Spatial data (open in QGIS, ArcGIS, etc.)

## Common State FIPS Codes

| State | FIPS Code |
|-------|-----------|
| California | 06 |
| New York | 36 |
| Texas | 48 |
| Florida | 12 |
| Illinois | 17 |
| Pennsylvania | 42 |
| Ohio | 39 |
| Michigan | 26 |
| Georgia | 13 |
| North Carolina | 37 |

## Common California County FIPS Codes

| County | FIPS Code |
|--------|-----------|
| Alameda | 001 |
| Contra Costa | 013 |
| Marin | 041 |
| San Francisco | 075 |
| San Mateo | 081 |
| Santa Clara | 085 |
| Los Angeles | 037 |
| Orange | 059 |
| San Diego | 073 |

## Troubleshooting

**Error: "Census API key invalid"**
- Check that the API key in `firstfile.txt` is correct
- Or provide your own with `--api-key YOUR_KEY`

**Error: "Place not found"**
- Check spelling of place name
- Try adding state and country (e.g., "Berkeley, California, USA")

**Error: "No network found"**
- Area may not have OSM coverage
- Try a larger or different area

**Memory issues:**
- Reduce the study area size
- Use `--no-trips` to skip trip generation

## Next Steps

1. Open the `.gpkg` file in QGIS to visualize:
   - TAZ boundaries
   - Road network
   - Demographic data

2. Analyze the CSV files:
   - OD matrix for trip patterns
   - Link attributes for network analysis
   - TAZ data for planning

3. Customize the model:
   - Adjust trip rates in `demand_model.py`
   - Modify gravity model friction factor
   - Add custom TAZ boundaries

## Need Help?

See the full README.md for detailed documentation.
