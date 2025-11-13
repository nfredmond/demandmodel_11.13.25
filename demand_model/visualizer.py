"""
Visualization Module for Transportation Demand Model
Creates interactive maps and static plots for model outputs
"""
import folium
from folium import plugins
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemandModelVisualizer:
    """
    Creates visualizations for transportation demand model outputs
    Supports interactive maps (HTML) and static plots (PNG/PDF)
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory for saving visualizations
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Color schemes
        self.colors = {
            'population': 'YlOrRd',
            'employment': 'YlGnBu',
            'income': 'RdYlGn',
            'density': 'Reds',
            'network': 'viridis'
        }

    def create_taz_map(
        self,
        taz_gdf: gpd.GeoDataFrame,
        variable: str = 'total_population',
        title: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> folium.Map:
        """
        Create interactive choropleth map of TAZ data

        Args:
            taz_gdf: GeoDataFrame with TAZ data
            variable: Variable to visualize
            title: Map title
            save_path: Path to save HTML file

        Returns:
            Folium map object
        """
        logger.info(f"Creating TAZ map for {variable}...")

        # Convert to WGS84 for folium
        if taz_gdf.crs != 'EPSG:4326':
            taz_gdf = taz_gdf.to_crs('EPSG:4326')

        # Calculate center
        center = [taz_gdf.geometry.centroid.y.mean(), taz_gdf.geometry.centroid.x.mean()]

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=12,
            tiles='OpenStreetMap'
        )

        # Add title
        if title is None:
            title = f"TAZ Map: {variable.replace('_', ' ').title()}"

        title_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 50px; width: 400px; height: 50px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:16px; font-weight: bold; padding: 10px">
        {title}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Check if variable exists
        if variable not in taz_gdf.columns:
            logger.warning(f"Variable {variable} not found, using first numeric column")
            numeric_cols = taz_gdf.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                variable = numeric_cols[0]
            else:
                logger.error("No numeric columns found")
                return m

        # Create choropleth
        folium.Choropleth(
            geo_data=taz_gdf,
            name='choropleth',
            data=taz_gdf,
            columns=['TAZ_ID', variable],
            key_on='feature.properties.TAZ_ID',
            fill_color=self.colors.get(variable.split('_')[0], 'YlOrRd'),
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=variable.replace('_', ' ').title(),
            nan_fill_color='white'
        ).add_to(m)

        # Add tooltips
        style_function = lambda x: {
            'fillColor': '#ffffff',
            'color': '#000000',
            'fillOpacity': 0.1,
            'weight': 0.5
        }

        highlight_function = lambda x: {
            'fillColor': '#000000',
            'color': '#000000',
            'fillOpacity': 0.3,
            'weight': 2
        }

        # Create tooltip
        tooltip_fields = ['TAZ_ID', variable]
        tooltip_aliases = ['TAZ ID:', f"{variable.replace('_', ' ').title()}:"]

        # Add TAZ boundaries with tooltips
        folium.GeoJson(
            taz_gdf,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True
            )
        ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Save if path provided
        if save_path:
            m.save(save_path)
            logger.info(f"Map saved to {save_path}")

        return m

    def create_network_map(
        self,
        nodes_gdf: gpd.GeoDataFrame,
        links_gdf: gpd.GeoDataFrame,
        title: str = "Road Network",
        save_path: Optional[str] = None,
        show_nodes: bool = False
    ) -> folium.Map:
        """
        Create interactive map of road network

        Args:
            nodes_gdf: GeoDataFrame of nodes
            links_gdf: GeoDataFrame of links
            title: Map title
            save_path: Path to save HTML file
            show_nodes: Whether to show nodes on map

        Returns:
            Folium map object
        """
        logger.info("Creating network map...")

        # Convert to WGS84
        if links_gdf.crs != 'EPSG:4326':
            links_gdf = links_gdf.to_crs('EPSG:4326')
        if nodes_gdf.crs != 'EPSG:4326':
            nodes_gdf = nodes_gdf.to_crs('EPSG:4326')

        # Calculate center
        center = [links_gdf.geometry.centroid.y.mean(), links_gdf.geometry.centroid.x.mean()]

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=13,
            tiles='OpenStreetMap'
        )

        # Add title
        title_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 50px; width: 300px; height: 50px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:16px; font-weight: bold; padding: 10px">
        {title}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Color roads by type
        def get_road_color(highway_type):
            """Get color based on road type"""
            if isinstance(highway_type, list):
                highway_type = highway_type[0]

            color_map = {
                'motorway': '#e892a2',
                'trunk': '#f9b29c',
                'primary': '#fcd6a4',
                'secondary': '#f7fabf',
                'tertiary': '#ffffff',
                'residential': '#ffffff',
                'unclassified': '#ffffff',
                'service': '#ffffff'
            }
            return color_map.get(str(highway_type), '#cccccc')

        def get_road_weight(highway_type):
            """Get line weight based on road type"""
            if isinstance(highway_type, list):
                highway_type = highway_type[0]

            weight_map = {
                'motorway': 5,
                'trunk': 4,
                'primary': 3,
                'secondary': 2,
                'tertiary': 1.5,
                'residential': 1,
                'unclassified': 1,
                'service': 0.5
            }
            return weight_map.get(str(highway_type), 1)

        # Add links
        for idx, row in links_gdf.iterrows():
            if idx > 5000:  # Limit for performance
                break

            highway_type = row.get('highway', 'unknown')
            color = get_road_color(highway_type)
            weight = get_road_weight(highway_type)

            # Create tooltip text
            tooltip_text = f"Type: {highway_type}"
            if 'length_m' in row:
                tooltip_text += f"<br>Length: {row['length_m']:.0f} m"
            if 'speed_limit' in row:
                tooltip_text += f"<br>Speed: {row['speed_limit']:.0f} km/h"

            folium.GeoJson(
                row.geometry,
                style_function=lambda x, color=color, weight=weight: {
                    'color': color,
                    'weight': weight,
                    'opacity': 0.7
                },
                tooltip=tooltip_text
            ).add_to(m)

        # Add nodes if requested
        if show_nodes:
            for idx, row in nodes_gdf.iterrows():
                if idx > 1000:  # Limit for performance
                    break

                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=2,
                    color='blue',
                    fill=True,
                    fillColor='blue',
                    fillOpacity=0.6
                ).add_to(m)

        # Add legend
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; right: 50px; width: 200px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:12px; padding: 10px">
        <p><b>Road Types</b></p>
        <p><span style="color: #e892a2;">■</span> Motorway</p>
        <p><span style="color: #f9b29c;">■</span> Trunk</p>
        <p><span style="color: #fcd6a4;">■</span> Primary</p>
        <p><span style="color: #f7fabf;">■</span> Secondary</p>
        <p><span style="color: #ffffff; background-color: #000000;">■</span> Other</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save if path provided
        if save_path:
            m.save(save_path)
            logger.info(f"Network map saved to {save_path}")

        return m

    def create_combined_map(
        self,
        taz_gdf: gpd.GeoDataFrame,
        links_gdf: gpd.GeoDataFrame,
        variable: str = 'total_population',
        title: str = "Combined TAZ and Network Map",
        save_path: Optional[str] = None
    ) -> folium.Map:
        """
        Create map with both TAZ and network layers

        Args:
            taz_gdf: GeoDataFrame with TAZ data
            links_gdf: GeoDataFrame with network links
            variable: Variable to visualize on TAZ
            title: Map title
            save_path: Path to save HTML file

        Returns:
            Folium map object
        """
        logger.info("Creating combined map...")

        # Convert to WGS84
        if taz_gdf.crs != 'EPSG:4326':
            taz_gdf = taz_gdf.to_crs('EPSG:4326')
        if links_gdf.crs != 'EPSG:4326':
            links_gdf = links_gdf.to_crs('EPSG:4326')

        # Calculate center
        center = [taz_gdf.geometry.centroid.y.mean(), taz_gdf.geometry.centroid.x.mean()]

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=12,
            tiles='OpenStreetMap'
        )

        # Add title
        title_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 50px; width: 400px; height: 50px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:16px; font-weight: bold; padding: 10px">
        {title}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

        # Add TAZ layer
        if variable in taz_gdf.columns:
            folium.Choropleth(
                geo_data=taz_gdf,
                name='TAZ',
                data=taz_gdf,
                columns=['TAZ_ID', variable],
                key_on='feature.properties.TAZ_ID',
                fill_color=self.colors.get(variable.split('_')[0], 'YlOrRd'),
                fill_opacity=0.5,
                line_opacity=0.3,
                legend_name=variable.replace('_', ' ').title()
            ).add_to(m)

        # Add network layer
        network_layer = folium.FeatureGroup(name='Road Network')

        # Sample links for performance
        sample_size = min(3000, len(links_gdf))
        links_sample = links_gdf.sample(n=sample_size) if len(links_gdf) > sample_size else links_gdf

        for idx, row in links_sample.iterrows():
            folium.GeoJson(
                row.geometry,
                style_function=lambda x: {
                    'color': '#3388ff',
                    'weight': 2,
                    'opacity': 0.6
                }
            ).add_to(network_layer)

        network_layer.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Save if path provided
        if save_path:
            m.save(save_path)
            logger.info(f"Combined map saved to {save_path}")

        return m

    def plot_taz_statistics(
        self,
        taz_stats: pd.DataFrame,
        save_path: Optional[str] = None
    ):
        """
        Create plots of TAZ statistics

        Args:
            taz_stats: DataFrame with TAZ statistics
            save_path: Path to save plot
        """
        logger.info("Creating TAZ statistics plots...")

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Traffic Analysis Zone Statistics', fontsize=16, fontweight='bold')

        # Plot 1: Population distribution
        if 'total_population' in taz_stats.columns:
            ax = axes[0, 0]
            taz_stats['total_population'].hist(bins=30, ax=ax, color='skyblue', edgecolor='black')
            ax.set_xlabel('Population')
            ax.set_ylabel('Number of TAZs')
            ax.set_title('Population Distribution')
            ax.grid(axis='y', alpha=0.3)

        # Plot 2: Employment distribution
        if 'total_employment' in taz_stats.columns:
            ax = axes[0, 1]
            taz_stats['total_employment'].hist(bins=30, ax=ax, color='lightgreen', edgecolor='black')
            ax.set_xlabel('Employment')
            ax.set_ylabel('Number of TAZs')
            ax.set_title('Employment Distribution')
            ax.grid(axis='y', alpha=0.3)

        # Plot 3: Population density
        if 'pop_density' in taz_stats.columns:
            ax = axes[1, 0]
            taz_stats['pop_density'].hist(bins=30, ax=ax, color='coral', edgecolor='black')
            ax.set_xlabel('Population Density (per sq km)')
            ax.set_ylabel('Number of TAZs')
            ax.set_title('Population Density Distribution')
            ax.grid(axis='y', alpha=0.3)

        # Plot 4: Summary statistics table
        ax = axes[1, 1]
        ax.axis('tight')
        ax.axis('off')

        # Create summary table
        summary_data = []
        if 'total_population' in taz_stats.columns:
            summary_data.append(['Total Population', f"{taz_stats['total_population'].sum():,.0f}"])
        if 'total_employment' in taz_stats.columns:
            summary_data.append(['Total Employment', f"{taz_stats['total_employment'].sum():,.0f}"])
        if 'area_sq_km' in taz_stats.columns:
            summary_data.append(['Total Area (sq km)', f"{taz_stats['area_sq_km'].sum():,.1f}"])
        summary_data.append(['Number of TAZs', f"{len(taz_stats):,}"])

        table = ax.table(cellText=summary_data, cellLoc='left', loc='center',
                        colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        ax.set_title('Summary Statistics', pad=20)

        plt.tight_layout()

        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"TAZ statistics plot saved to {save_path}")

        return fig

    def plot_od_flows(
        self,
        od_matrix: pd.DataFrame,
        top_n: int = 20,
        save_path: Optional[str] = None
    ):
        """
        Plot top OD flows

        Args:
            od_matrix: DataFrame with origin_taz, dest_taz, trips
            top_n: Number of top flows to show
            save_path: Path to save plot
        """
        logger.info(f"Creating OD flow plot (top {top_n})...")

        # Get top flows
        top_flows = od_matrix.nlargest(top_n, 'trips')

        # Create plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Origin-Destination Trip Flows', fontsize=16, fontweight='bold')

        # Plot 1: Bar chart of top OD pairs
        od_labels = [f"{int(row['origin_taz'])}→{int(row['dest_taz'])}"
                     for _, row in top_flows.iterrows()]

        ax1.barh(range(len(top_flows)), top_flows['trips'], color='steelblue')
        ax1.set_yticks(range(len(top_flows)))
        ax1.set_yticklabels(od_labels, fontsize=8)
        ax1.set_xlabel('Trips per Day')
        ax1.set_title(f'Top {top_n} OD Pairs by Volume')
        ax1.grid(axis='x', alpha=0.3)
        ax1.invert_yaxis()

        # Plot 2: Trip distribution histogram
        ax2.hist(od_matrix['trips'], bins=50, color='lightcoral', edgecolor='black')
        ax2.set_xlabel('Trips per Day')
        ax2.set_ylabel('Number of OD Pairs')
        ax2.set_title('Distribution of Trip Volumes')
        ax2.set_yscale('log')
        ax2.grid(axis='y', alpha=0.3)

        # Add statistics
        total_trips = od_matrix['trips'].sum()
        avg_trips = od_matrix['trips'].mean()
        textstr = f'Total Trips: {total_trips:,.0f}\nAvg per OD: {avg_trips:.1f}'
        ax2.text(0.65, 0.95, textstr, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"OD flow plot saved to {save_path}")

        return fig

    def plot_network_statistics(
        self,
        links_gdf: gpd.GeoDataFrame,
        save_path: Optional[str] = None
    ):
        """
        Plot network statistics

        Args:
            links_gdf: GeoDataFrame with network links
            save_path: Path to save plot
        """
        logger.info("Creating network statistics plots...")

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Road Network Statistics', fontsize=16, fontweight='bold')

        # Plot 1: Link length distribution
        if 'length_m' in links_gdf.columns:
            ax = axes[0, 0]
            links_gdf['length_m'].hist(bins=50, ax=ax, color='skyblue', edgecolor='black')
            ax.set_xlabel('Link Length (m)')
            ax.set_ylabel('Number of Links')
            ax.set_title('Link Length Distribution')
            ax.grid(axis='y', alpha=0.3)

        # Plot 2: Speed limit distribution
        if 'speed_limit' in links_gdf.columns:
            ax = axes[0, 1]
            links_gdf['speed_limit'].hist(bins=20, ax=ax, color='lightgreen', edgecolor='black')
            ax.set_xlabel('Speed Limit (km/h)')
            ax.set_ylabel('Number of Links')
            ax.set_title('Speed Limit Distribution')
            ax.grid(axis='y', alpha=0.3)

        # Plot 3: Road type distribution
        if 'highway' in links_gdf.columns:
            ax = axes[1, 0]
            # Handle list types
            highway_types = links_gdf['highway'].apply(
                lambda x: x[0] if isinstance(x, list) else x
            )
            highway_counts = highway_types.value_counts().head(10)
            highway_counts.plot(kind='barh', ax=ax, color='coral')
            ax.set_xlabel('Number of Links')
            ax.set_title('Road Type Distribution (Top 10)')
            ax.grid(axis='x', alpha=0.3)

        # Plot 4: Network summary
        ax = axes[1, 1]
        ax.axis('tight')
        ax.axis('off')

        summary_data = [
            ['Total Links', f"{len(links_gdf):,}"],
        ]

        if 'length_m' in links_gdf.columns:
            total_length = links_gdf['length_m'].sum() / 1000
            summary_data.append(['Total Length (km)', f"{total_length:,.1f}"])
            summary_data.append(['Avg Link Length (m)', f"{links_gdf['length_m'].mean():.1f}"])

        if 'speed_limit' in links_gdf.columns:
            summary_data.append(['Avg Speed Limit (km/h)', f"{links_gdf['speed_limit'].mean():.1f}"])

        if 'capacity_vph' in links_gdf.columns:
            total_capacity = links_gdf['capacity_vph'].sum()
            summary_data.append(['Total Capacity (vph)', f"{total_capacity:,.0f}"])

        table = ax.table(cellText=summary_data, cellLoc='left', loc='center',
                        colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        ax.set_title('Network Summary', pad=20)

        plt.tight_layout()

        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Network statistics plot saved to {save_path}")

        return fig

    def create_dashboard(
        self,
        taz_gdf: gpd.GeoDataFrame,
        links_gdf: gpd.GeoDataFrame,
        od_matrix: Optional[pd.DataFrame] = None,
        save_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create complete visualization dashboard

        Args:
            taz_gdf: GeoDataFrame with TAZ data
            links_gdf: GeoDataFrame with network links
            od_matrix: DataFrame with OD trips (optional)
            save_dir: Directory to save all outputs

        Returns:
            Dictionary with paths to all created files
        """
        logger.info("Creating visualization dashboard...")

        if save_dir is None:
            save_dir = self.output_dir

        os.makedirs(save_dir, exist_ok=True)

        output_files = {}

        # 1. TAZ map
        taz_map_path = os.path.join(save_dir, "map_taz.html")
        self.create_taz_map(taz_gdf, variable='total_population', save_path=taz_map_path)
        output_files['taz_map'] = taz_map_path

        # 2. Network map
        nodes_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(
                [links_gdf.geometry.iloc[0].coords[0][0]],
                [links_gdf.geometry.iloc[0].coords[0][1]]
            ),
            crs=links_gdf.crs
        )
        network_map_path = os.path.join(save_dir, "map_network.html")
        self.create_network_map(nodes_gdf, links_gdf, save_path=network_map_path)
        output_files['network_map'] = network_map_path

        # 3. Combined map
        combined_map_path = os.path.join(save_dir, "map_combined.html")
        self.create_combined_map(taz_gdf, links_gdf, save_path=combined_map_path)
        output_files['combined_map'] = combined_map_path

        # 4. TAZ statistics plot
        taz_stats = pd.DataFrame(taz_gdf.drop(columns='geometry'))
        taz_plot_path = os.path.join(save_dir, "plot_taz_statistics.png")
        self.plot_taz_statistics(taz_stats, save_path=taz_plot_path)
        output_files['taz_plot'] = taz_plot_path

        # 5. Network statistics plot
        network_plot_path = os.path.join(save_dir, "plot_network_statistics.png")
        self.plot_network_statistics(links_gdf, save_path=network_plot_path)
        output_files['network_plot'] = network_plot_path

        # 6. OD flow plot (if provided)
        if od_matrix is not None and len(od_matrix) > 0:
            od_plot_path = os.path.join(save_dir, "plot_od_flows.png")
            self.plot_od_flows(od_matrix, save_path=od_plot_path)
            output_files['od_plot'] = od_plot_path

        logger.info(f"Dashboard created with {len(output_files)} visualizations")

        return output_files
