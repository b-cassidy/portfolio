# Import libraries
import os
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Search
import branca


def data_analysis(merged_df, processed_data_path):
    """
    Aggregates our risk based scoring on a LSOA level and generates and interactive map showing different risk areas
    """
    # Begin to aggregate the property level data
    print('--- Aggregating the property risk data ---')
    agg_df = merged_df.groupby(['lsoa21cd', 'LOCAL_AUTHORITY_NAME']).agg(
        avg_risk_score=('total_risk_score', 'mean'),
        avg_age_risk=('age_risk', 'mean'),
        avg_floor_risk=('floor_risk', 'mean'),
        avg_wall_risk=('wall_risk', 'mean'),
        avg_epc_risk=('epc_risk', 'mean'),
        avg_imd_risk=('imd_risk', 'mean'),
        property_count=('LMK_KEY', 'count')
    ).reset_index()

    # Round risk columns
    cols_to_round = ['avg_risk_score', 'avg_age_risk',
                     'avg_floor_risk', 'avg_wall_risk', 'avg_epc_risk', 'avg_imd_risk']
    agg_df[cols_to_round] = agg_df[cols_to_round].round(2)

    # Calculate the 10th percentile of neighborhoods and use this number of properties as a significance filter
    # Including a 'safety net' of 20 properties though
    sig_threshold = agg_df['property_count'].quantile(0.10)
    sig_threshold = min(sig_threshold, 20)

    # Load geojson shapes from processed data
    print('--- Merging data with boundary shapes ---')
    geo_path = os.path.join(processed_data_path, 'project_aura_lsoas.geojson')
    gdf = gpd.read_file(geo_path)

    # Spatial join agg_df with gdf using lsoa21cd from agg_df and LSOA21CD from gdf
    combined_gdf = gdf.merge(agg_df, left_on='LSOA21CD',
                             right_on='lsoa21cd', how='inner')

    # Set data to GPS coordinates and get centred latitude and longtitude from combined_gdf
    combined_gdf = combined_gdf.to_crs(epsg=4326)
    gdf_bounds = combined_gdf.total_bounds
    center_lat = (gdf_bounds[1] + gdf_bounds[3]) / 2
    center_long = (gdf_bounds[0] + gdf_bounds[2]) / 2

    # Initialise folium map
    print(f'--- Setting map centre at: {center_lat}, {center_long} ---')
    m = folium.Map(
        location=[center_lat, center_long],
        zoom_start=11,
        tiles=None
    )

    # Add custom color grading for areas on map
    print('--- Setting colour grading for mapping ---')
    colours = ['#1a9850', '#fee08b', '#d73027']  # Green, Amber, Red

    colourmap = branca.colormap.StepColormap(
        colours,
        vmin=0,
        vmax=12,
        index=[0, 4, 7, 12],
        caption='Average Damp Propensity Score'
    ).add_to(m)

    # Custom function to help with custom style settings based on calculations
    def style_function(feature):
        score = feature['properties']['avg_risk_score']
        count = feature['properties']['property_count']

        # If area property count < sig_threshold set colour to gray
        if count < sig_threshold:
            fill_colour = '#d3d3d3'
        else:
            fill_colour = colourmap(score)

        return {
            'fillColor': fill_colour,
            'color': 'black',  # Border colour
            'weight': 0.5,  # border weight
            'fillOpacity': 0.6
        }

    # Custom tooltip settings to make mapping more readable
    print('--- Setting custom tooltips for the mapping ---')

    def tooltip_info():
        return folium.GeoJsonTooltip(
            fields=['LSOA21NM', 'avg_risk_score', 'property_count',
                    'avg_age_risk', 'avg_floor_risk', 'avg_wall_risk', 'avg_epc_risk'],
            aliases=['Neighborhood:', 'TOTAL RISK:', 'Props:',
                     'Age Risk:', 'Floor Risk:', 'Wall Risk', 'EPC Risk:'],
            style="""
                background-color: #2c3e50;
                color: white;
                font-family: sans-serif;
                font-size: 12px;
                padding: 10px;
                border: 2px solid #34495e;
                border-radius: 5px;
            """,
            localize=True
        )

    # Start setting up both visible and invisible layers on mapping to add filter and search functiuonality
    print('--- Creating layers in mapping for extra functionality ---')

    # Add faux-header for slicer
    folium.TileLayer('cartodbpositron',
                     name='Base Map (always active)').add_to(m)

    # Add search layer and 'header layer' to slicer
    search_layer = folium.FeatureGroup(
        name='Search Index', control=False).add_to(m)
    folium.FeatureGroup(name='-- Local Authority Filter --').add_to(m)

    # Start creating layers per local authority and adding data to mapping
    authorities = sorted(combined_gdf['LOCAL_AUTHORITY_NAME'].unique())

    for auth in authorities:
        fg = folium.FeatureGroup(
            name=auth, overlay=True, control=True).add_to(m)
        subset = combined_gdf[combined_gdf['LOCAL_AUTHORITY_NAME'] == auth].copy(
        )

        # If local authority has no data continue
        if subset.empty:
            continue

        # Add data layers which are visible
        folium.GeoJson(
            subset.__geo_interface__,
            style_function=style_function,
            tooltip=tooltip_info(),
            highlight_function=lambda x: {
                'weight': 4, 'color': 'red', 'dashArray': '5:5'}
        ).add_to(fg)

        # Add search layer which will not be visible
        folium.GeoJson(
            subset.__geo_interface__,
            style_function=lambda x: {'fillOpacity': 0, 'weight': 0},
            tooltip=None
        ).add_to(search_layer)

    # Create search function
    Search(
        layer=search_layer,
        geom_type='Polygon',
        placeholder='Search Neighbourhood (eg. Middlesbrough 012C)...',
        collapsed=False,
        search_label='LSOA21NM',
        search_zoom=14
    ).add_to(m)

    # Set slicer filter to be in top right of map
    folium.LayerControl(collapsed=False, position='topright').add_to(m)

    # Saving the map
    map_output = os.path.join(processed_data_path, 'project_aura_map.html')
    print(f'--- Saving map output at; {map_output} ---')
    title_html = '''
             <h3 align="center" style="font-size:16px"><b>Project Aura: Damp Propensity Risk Map</b></h3>
             '''
    m.get_root().html.add_child(folium.Element(title_html))
    m.save(map_output)
