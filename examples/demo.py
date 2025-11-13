"""
Transportation Demand Model - Demo Script

This script demonstrates how to use the Transportation Demand Model application
to load Census data, OpenStreetMap network data, and create a basic demand model.

Example usage for Berkeley, California
"""
import sys
import os

# Add parent directory to path to import demand_model package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from demand_model import TransportationDemandModel


def demo_berkeley():
    """
    Demo: Load and analyze transportation demand for Berkeley, California
    """
    print("=" * 70)
    print("TRANSPORTATION DEMAND MODEL - BERKELEY, CA DEMO")
    print("=" * 70)

    # Initialize model with Census API key
    # The API key is from firstfile.txt
    api_key = "be5b4855accd13808b0bd0f17311ee4b90392e39"

    model = TransportationDemandModel(
        census_api_key=api_key,
        project_name="berkeley_demo"
    )

    # Load study area data
    # Berkeley is in Alameda County, California
    # State FIPS: 06 (California)
    # County FIPS: 001 (Alameda)
    print("\nLoading study area data for Berkeley, CA...")
    print("This will download:")
    print("  - Census demographic data (ACS 5-year estimates)")
    print("  - OpenStreetMap road network")
    print("  - Create Traffic Analysis Zones from census tracts")
    print()

    try:
        model.load_study_area_by_place(
            place_name="Berkeley, California, USA",
            state_fips="06",  # California
            county_fips="001",  # Alameda County
            network_type='drive'
        )

        # Get summary statistics
        print("\n" + "=" * 70)
        print("SUMMARY STATISTICS")
        print("=" * 70)
        stats = model.get_summary_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Calculate TAZ statistics
        print("\n" + "=" * 70)
        print("TAZ STATISTICS (First 5 TAZs)")
        print("=" * 70)
        taz_stats = model.calculate_taz_statistics()
        print(taz_stats.head().to_string())

        # Estimate trip generation
        print("\n" + "=" * 70)
        print("TRIP GENERATION")
        print("=" * 70)
        trip_gen = model.estimate_trip_generation()
        print(f"Total Productions: {trip_gen['productions'].sum():,.0f} trips/day")
        print(f"Total Attractions: {trip_gen['attractions'].sum():,.0f} trips/day")
        print("\nTrip Generation by TAZ (First 5 TAZs):")
        print(trip_gen.head().to_string())

        # Distribute trips using gravity model
        print("\n" + "=" * 70)
        print("TRIP DISTRIBUTION (Gravity Model)")
        print("=" * 70)
        od_matrix = model.distribute_trips_gravity(trip_gen, friction_factor=1.5)
        print(f"Total OD pairs with trips: {len(od_matrix)}")
        print(f"Total trips: {od_matrix['trips'].sum():,.0f}")
        print("\nSample OD pairs (First 10):")
        print(od_matrix.head(10).to_string())

        # Export results
        print("\n" + "=" * 70)
        print("EXPORTING RESULTS")
        print("=" * 70)

        # Export to CSV
        model.export_to_csv()
        print("✓ CSV files exported to output/berkeley_demo/")

        # Export to GeoPackage
        model.export_to_geopackage()
        print("✓ GeoPackage exported to output/berkeley_demo/berkeley_demo.gpkg")

        print("\n" + "=" * 70)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nOutput files:")
        print("  - output/berkeley_demo/berkeley_demo_taz.csv")
        print("  - output/berkeley_demo/berkeley_demo_nodes.csv")
        print("  - output/berkeley_demo/berkeley_demo_links.csv")
        print("  - output/berkeley_demo/berkeley_demo_od_matrix.csv")
        print("  - output/berkeley_demo/berkeley_demo.gpkg")
        print("\nYou can open the .gpkg file in QGIS or other GIS software")
        print("to visualize the network, TAZs, and demographic data.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: This demo requires internet connection to download data")
        print("from Census API and OpenStreetMap.")
        import traceback
        traceback.print_exc()


def demo_custom_area():
    """
    Demo: Load custom area by bounding box
    San Francisco downtown area
    """
    print("=" * 70)
    print("TRANSPORTATION DEMAND MODEL - CUSTOM AREA DEMO")
    print("San Francisco Downtown")
    print("=" * 70)

    api_key = "be5b4855accd13808b0bd0f17311ee4b90392e39"

    model = TransportationDemandModel(
        census_api_key=api_key,
        project_name="sf_downtown"
    )

    # San Francisco downtown bounding box
    # Roughly covers Financial District and surrounding areas
    north = 37.8000
    south = 37.7800
    east = -122.3900
    west = -122.4100

    print(f"\nLoading data for bounding box:")
    print(f"  North: {north}, South: {south}")
    print(f"  East: {east}, West: {west}")

    try:
        model.load_study_area_by_bbox(
            north=north,
            south=south,
            east=east,
            west=west,
            state_fips="06",  # California
            county_fips="075",  # San Francisco County
            network_type='all'  # All transportation modes
        )

        # Get summary
        stats = model.get_summary_stats()
        print("\nSummary Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Export
        model.export_to_csv()
        model.export_to_geopackage()

        print("\n✓ Demo completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Transportation Demand Model Demo"
    )
    parser.add_argument(
        '--demo',
        choices=['berkeley', 'sf', 'both'],
        default='berkeley',
        help='Which demo to run (default: berkeley)'
    )

    args = parser.parse_args()

    if args.demo == 'berkeley' or args.demo == 'both':
        demo_berkeley()

    if args.demo == 'sf' or args.demo == 'both':
        if args.demo == 'both':
            print("\n\n")
        demo_custom_area()

    print("\n" + "=" * 70)
    print("All demos completed!")
    print("=" * 70)
