#!/usr/bin/env python3
"""
Visualization Viewer for Transportation Demand Model

Opens and displays visualizations created by the demand model.
Automatically finds HTML maps and PNG plots and opens them in the default viewer.

Usage:
    python view_outputs.py                    # View latest project
    python view_outputs.py --project my_model  # View specific project
    python view_outputs.py --list             # List available projects
"""
import argparse
import os
import sys
import webbrowser
import subprocess
from pathlib import Path
import time


def find_projects():
    """Find all available model projects"""
    output_dir = Path("output")
    if not output_dir.exists():
        return []

    projects = []
    for item in output_dir.iterdir():
        if item.is_dir():
            projects.append(item.name)

    return sorted(projects)


def find_visualizations(project_name):
    """Find all visualization files for a project"""
    project_dir = Path(f"output/{project_name}")

    if not project_dir.exists():
        print(f"Error: Project '{project_name}' not found")
        return None

    visualizations = {
        'maps': [],
        'plots': [],
        'data': []
    }

    # Find HTML maps
    for html_file in project_dir.glob("map_*.html"):
        visualizations['maps'].append(html_file)

    # Find PNG plots
    for png_file in project_dir.glob("plot_*.png"):
        visualizations['plots'].append(png_file)

    # Find data files
    for csv_file in project_dir.glob("*.csv"):
        visualizations['data'].append(csv_file)

    for gpkg_file in project_dir.glob("*.gpkg"):
        visualizations['data'].append(gpkg_file)

    return visualizations


def open_file(filepath):
    """Open file in default application"""
    filepath = Path(filepath).absolute()

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return False

    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', str(filepath)])
        elif sys.platform == 'win32':  # Windows
            os.startfile(str(filepath))
        else:  # Linux
            # Try different viewers
            if filepath.suffix == '.html':
                webbrowser.open(f'file://{filepath}')
            elif filepath.suffix == '.png':
                # Try common image viewers
                viewers = ['xdg-open', 'eog', 'display', 'feh']
                for viewer in viewers:
                    try:
                        subprocess.run([viewer, str(filepath)], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            else:
                subprocess.run(['xdg-open', str(filepath)])

        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False


def view_project(project_name, file_type='all', auto_open=True):
    """View visualizations for a project"""
    print("=" * 70)
    print(f"TRANSPORTATION DEMAND MODEL - VISUALIZATION VIEWER")
    print(f"Project: {project_name}")
    print("=" * 70)

    visualizations = find_visualizations(project_name)

    if visualizations is None:
        return

    # Display available files
    print("\nAvailable Visualizations:")
    print()

    all_files = []

    if visualizations['maps']:
        print("📊 Interactive Maps (HTML):")
        for i, map_file in enumerate(visualizations['maps'], 1):
            print(f"  {i}. {map_file.name}")
            all_files.append(('map', map_file))
        print()

    if visualizations['plots']:
        print("📈 Static Plots (PNG):")
        for i, plot_file in enumerate(visualizations['plots'], 1):
            print(f"  {i + len(visualizations['maps'])}. {plot_file.name}")
            all_files.append(('plot', plot_file))
        print()

    if visualizations['data']:
        print("💾 Data Files:")
        for i, data_file in enumerate(visualizations['data'], 1):
            print(f"  {i + len(visualizations['maps']) + len(visualizations['plots'])}. {data_file.name}")
            all_files.append(('data', data_file))
        print()

    if not all_files:
        print("No visualizations found.")
        print("\nRun your model with visualizations enabled:")
        print("  model.create_visualizations()")
        return

    # Auto-open files
    if auto_open:
        print("=" * 70)
        print("Opening visualizations...")
        print("=" * 70)
        print()

        if file_type == 'all' or file_type == 'maps':
            for map_file in visualizations['maps']:
                print(f"Opening map: {map_file.name}")
                open_file(map_file)
                time.sleep(0.5)  # Small delay between opens

        if file_type == 'all' or file_type == 'plots':
            for plot_file in visualizations['plots']:
                print(f"Opening plot: {plot_file.name}")
                open_file(plot_file)
                time.sleep(0.5)

        print()
        print("✓ Visualizations opened in default applications")
    else:
        # Interactive mode
        print("=" * 70)
        print("Select files to open (comma-separated numbers, or 'all'):")
        print("=" * 70)

        choice = input("> ").strip()

        if choice.lower() == 'all':
            for _, filepath in all_files:
                open_file(filepath)
                time.sleep(0.5)
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                for idx in indices:
                    if 0 <= idx < len(all_files):
                        _, filepath = all_files[idx]
                        open_file(filepath)
                        time.sleep(0.5)
            except ValueError:
                print("Invalid input")


def create_index_html(project_name):
    """Create an index.html file that shows all visualizations"""
    visualizations = find_visualizations(project_name)

    if visualizations is None:
        return

    project_dir = Path(f"output/{project_name}")
    index_path = project_dir / "index.html"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transportation Demand Model - {project_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .card {{
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .card h3 {{
            margin-top: 0;
            color: #4CAF50;
        }}
        .card a {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 15px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.3s;
        }}
        .card a:hover {{
            background: #45a049;
        }}
        .preview {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            margin-top: 10px;
        }}
        iframe {{
            width: 100%;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>🚗 Transportation Demand Model</h1>
    <p><strong>Project:</strong> {project_name}</p>

    <div class="section">
        <h2>📊 Interactive Maps</h2>
        <p>Click on any map to view it in full screen:</p>
        <div class="grid">
"""

    # Add map cards
    for map_file in visualizations['maps']:
        map_name = map_file.stem.replace('map_', '').replace('_', ' ').title()
        html_content += f"""
            <div class="card">
                <h3>{map_name}</h3>
                <p>Interactive HTML map</p>
                <a href="{map_file.name}" target="_blank">Open Map →</a>
            </div>
"""

    html_content += """
        </div>
    </div>

    <div class="section">
        <h2>📈 Statistical Plots</h2>
        <p>View detailed analysis plots:</p>
        <div class="grid">
"""

    # Add plot cards
    for plot_file in visualizations['plots']:
        plot_name = plot_file.stem.replace('plot_', '').replace('_', ' ').title()
        html_content += f"""
            <div class="card">
                <h3>{plot_name}</h3>
                <img src="{plot_file.name}" class="preview" alt="{plot_name}">
                <a href="{plot_file.name}" target="_blank">View Full Size →</a>
            </div>
"""

    html_content += """
        </div>
    </div>

    <div class="section">
        <h2>💾 Data Files</h2>
        <p>Download model outputs:</p>
        <ul>
"""

    # Add data files
    for data_file in visualizations['data']:
        size_mb = data_file.stat().st_size / (1024 * 1024)
        html_content += f"""
            <li>
                <strong>{data_file.name}</strong>
                ({size_mb:.2f} MB) -
                <a href="{data_file.name}" download>Download</a>
            </li>
"""

    html_content += """
        </ul>
    </div>

    <div class="section">
        <h2>ℹ️ About</h2>
        <p>This dashboard shows the outputs from the Transportation Demand Model.</p>
        <p>The model integrates:</p>
        <ul>
            <li>US Census demographic data</li>
            <li>OpenStreetMap road network</li>
            <li>Traffic Analysis Zones (TAZ)</li>
            <li>Trip generation and distribution</li>
        </ul>
    </div>

</body>
</html>
"""

    # Write index file
    with open(index_path, 'w') as f:
        f.write(html_content)

    print(f"Created index page: {index_path}")
    return index_path


def main():
    parser = argparse.ArgumentParser(
        description='View Transportation Demand Model visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--project',
        type=str,
        help='Project name to view (default: latest project)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available projects'
    )

    parser.add_argument(
        '--type',
        choices=['all', 'maps', 'plots'],
        default='all',
        help='Type of visualizations to open (default: all)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode - select files to open'
    )

    parser.add_argument(
        '--index',
        action='store_true',
        help='Create and open index.html with all visualizations'
    )

    args = parser.parse_args()

    # List projects
    if args.list:
        projects = find_projects()
        if projects:
            print("Available projects:")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project}")
        else:
            print("No projects found in output/ directory")
        return

    # Determine project
    if args.project:
        project_name = args.project
    else:
        projects = find_projects()
        if not projects:
            print("No projects found in output/ directory")
            print("\nRun your model first:")
            print("  python run_model.py --place 'Your City' --state XX")
            return
        project_name = projects[-1]  # Use latest project
        print(f"Using latest project: {project_name}")
        print()

    # Create index page
    if args.index:
        index_path = create_index_html(project_name)
        print(f"\nOpening index page...")
        open_file(index_path)
    else:
        # View project
        view_project(
            project_name,
            file_type=args.type,
            auto_open=not args.interactive
        )


if __name__ == "__main__":
    main()
