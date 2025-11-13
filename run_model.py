#!/usr/bin/env python3
"""
Transportation Demand Model - Command Line Interface

Simple CLI for running transportation demand models with automatic data loading
from Census API and OpenStreetMap.

Usage:
    python run_model.py --place "Berkeley, California, USA" --state 06 --county 001
    python run_model.py --bbox 37.9 37.8 -122.2 -122.3 --state 06
"""
import argparse
import sys
from demand_model import TransportationDemandModel


def main():
    parser = argparse.ArgumentParser(
        description='Transportation Demand Model - Automatic Data Loader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load by place name
  python run_model.py --place "Berkeley, California, USA" --state 06 --county 001

  # Load by bounding box
  python run_model.py --bbox 37.9 37.8 -122.2 -122.3 --state 06 --county 001

  # Specify network type
  python run_model.py --place "Oakland, CA, USA" --state 06 --county 001 --network all

State FIPS Codes:
  California: 06, New York: 36, Texas: 48, Florida: 12, etc.
  See: https://www.census.gov/library/reference/code-lists/ansi.html
        """
    )

    # Geography options
    geo_group = parser.add_mutually_exclusive_group(required=True)
    geo_group.add_argument(
        '--place',
        type=str,
        help='Place name (e.g., "Berkeley, California, USA")'
    )
    geo_group.add_argument(
        '--bbox',
        nargs=4,
        type=float,
        metavar=('NORTH', 'SOUTH', 'EAST', 'WEST'),
        help='Bounding box coordinates'
    )

    # Required FIPS codes
    parser.add_argument(
        '--state',
        type=str,
        required=True,
        help='State FIPS code (e.g., "06" for California)'
    )
    parser.add_argument(
        '--county',
        type=str,
        help='County FIPS code (optional, e.g., "001" for Alameda)'
    )

    # Optional parameters
    parser.add_argument(
        '--network',
        type=str,
        choices=['drive', 'walk', 'bike', 'all'],
        default='drive',
        help='Network type (default: drive)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default='demand_model',
        help='Project name (default: demand_model)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='Census API key (default: use key from firstfile.txt)'
    )
    parser.add_argument(
        '--no-trips',
        action='store_true',
        help='Skip trip generation and distribution'
    )
    parser.add_argument(
        '--friction',
        type=float,
        default=1.5,
        help='Friction factor for gravity model (default: 1.5)'
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Create visualizations (maps and plots)'
    )
    parser.add_argument(
        '--view',
        action='store_true',
        help='Automatically open visualizations after creation'
    )

    args = parser.parse_args()

    # Read API key
    if args.api_key:
        api_key = args.api_key
    else:
        try:
            with open('firstfile.txt', 'r') as f:
                content = f.read()
                # Extract API key from firstfile.txt
                if 'Census API:' in content:
                    api_key = content.split('Census API:')[1].strip()
                else:
                    api_key = "be5b4855accd13808b0bd0f17311ee4b90392e39"
        except FileNotFoundError:
            print("Error: firstfile.txt not found and no API key provided")
            print("Please provide --api-key or ensure firstfile.txt exists")
            sys.exit(1)

    # Initialize model
    print("=" * 70)
    print("TRANSPORTATION DEMAND MODEL")
    print("=" * 70)
    print(f"Project: {args.project}")
    print(f"Network Type: {args.network}")
    print()

    model = TransportationDemandModel(
        census_api_key=api_key,
        project_name=args.project
    )

    # Load study area
    try:
        if args.place:
            print(f"Loading study area: {args.place}")
            print(f"State FIPS: {args.state}, County FIPS: {args.county or 'All'}")
            print()

            model.load_study_area_by_place(
                place_name=args.place,
                state_fips=args.state,
                county_fips=args.county,
                network_type=args.network
            )

        elif args.bbox:
            north, south, east, west = args.bbox
            print(f"Loading study area by bounding box:")
            print(f"  North: {north}, South: {south}")
            print(f"  East: {east}, West: {west}")
            print(f"State FIPS: {args.state}, County FIPS: {args.county or 'All'}")
            print()

            model.load_study_area_by_bbox(
                north=north,
                south=south,
                east=east,
                west=west,
                state_fips=args.state,
                county_fips=args.county,
                network_type=args.network
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
        print("TAZ STATISTICS")
        print("=" * 70)
        taz_stats = model.calculate_taz_statistics()
        print(f"Total TAZs: {len(taz_stats)}")
        print(f"\nFirst 5 TAZs:")
        print(taz_stats.head().to_string())

        # Trip generation and distribution (unless --no-trips)
        if not args.no_trips:
            print("\n" + "=" * 70)
            print("TRIP GENERATION")
            print("=" * 70)
            trip_gen = model.estimate_trip_generation()
            total_prod = trip_gen['productions'].sum()
            total_attr = trip_gen['attractions'].sum()
            print(f"Total Productions: {total_prod:,.0f} trips/day")
            print(f"Total Attractions: {total_attr:,.0f} trips/day")

            print("\n" + "=" * 70)
            print("TRIP DISTRIBUTION")
            print("=" * 70)
            print(f"Using gravity model with friction factor: {args.friction}")
            od_matrix = model.distribute_trips_gravity(
                trip_gen,
                friction_factor=args.friction
            )
            print(f"Total OD pairs with trips: {len(od_matrix):,}")
            print(f"Total trips: {od_matrix['trips'].sum():,.0f}")

        # Create visualizations
        if args.visualize or args.view:
            print("\n" + "=" * 70)
            print("CREATING VISUALIZATIONS")
            print("=" * 70)
            viz_files = model.create_visualizations()
            print(f"✓ Created {len(viz_files)} visualizations")
            for name, path in viz_files.items():
                print(f"  - {name}: {path}")

        # Export results
        print("\n" + "=" * 70)
        print("EXPORTING RESULTS")
        print("=" * 70)
        model.export_to_csv()
        print(f"✓ CSV files exported to output/{args.project}/")

        model.export_to_geopackage()
        print(f"✓ GeoPackage exported to output/{args.project}/{args.project}.gpkg")

        # Open visualizations if requested
        if args.view:
            print("\n" + "=" * 70)
            print("OPENING VISUALIZATIONS")
            print("=" * 70)
            import webbrowser
            import os
            for name, path in viz_files.items():
                if path.endswith('.html'):
                    print(f"Opening {name}...")
                    webbrowser.open(f'file://{os.path.abspath(path)}')

        print("\n" + "=" * 70)
        print("MODEL RUN COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nOutput files saved to: output/{args.project}/")
        print("\nNext steps:")
        if args.visualize:
            print("  1. View interactive maps and plots:")
            print(f"     python view_outputs.py --project {args.project}")
            print("  2. Open the .gpkg file in QGIS to visualize the data")
            print("  3. Review the CSV files for tabular analysis")
            print("  4. Use the OD matrix for further modeling")
        else:
            print("  1. Open the .gpkg file in QGIS to visualize the data")
            print("  2. Review the CSV files for tabular analysis")
            print("  3. Use the OD matrix for further modeling")
            print("  4. Run with --visualize to create interactive maps and plots")

    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"{e}")
        print("\nNote: This application requires internet connection")
        print("to download data from Census API and OpenStreetMap.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
