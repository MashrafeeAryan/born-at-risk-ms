# Import libraries
from pathlib import Path
import pandas as pd
import geopandas as gpd
import plotly.express as px


"""
Purpose of this script:
    Read the priority score csv
    Read the county shapefile
    Merge both using county FIPS
    Create a clean interactive Mississippi county map
    Save the map as an HTML file
"""


# Finds main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

# Raw data folder path
RAW_DIR = BASE_DIR / "data_raw"

# Clean data folder path
CLEAN_DIR = BASE_DIR / "data_clean"

# Visuals folder path
VISUALS_DIR = BASE_DIR / "visuals"

# Make visuals folder if it does not exist
VISUALS_DIR.mkdir(exist_ok=True)

# Path to priority score csv
PRIORITY_FILE = CLEAN_DIR / "priority_scores.csv"

# Path to county shapefile
MAP_FILE = RAW_DIR / "tl_2024_us_county" / "tl_2024_us_county.shp"


# Clean FIPS code and make it 5-digit text
def clean_fips(value):
    # Return nothing if value is missing
    if pd.isna(value):
        return None

    # Try converting number-like values to 5-digit text
    try:
        return str(int(float(value))).zfill(5)

    # If that fails, clean the value as text and pad to 5 digits
    except ValueError:
        return str(value).strip().zfill(5)


# Create interactive Mississippi county priority map
def create_interactive_priority_map():
    # Read priority score csv file
    priority_df = pd.read_csv(PRIORITY_FILE, dtype={"county_fips": str})

    # Clean county_fips column
    priority_df["county_fips"] = priority_df["county_fips"].apply(clean_fips)

    # Read shapefile
    counties_gdf = gpd.read_file(MAP_FILE)

    # Clean column names
    counties_gdf.columns = counties_gdf.columns.astype(str).str.strip()

    # Keep only Mississippi counties
    # Mississippi state FIPS is 28
    if "STATEFP" in counties_gdf.columns:
        counties_gdf = counties_gdf[counties_gdf["STATEFP"] == "28"].copy()

    # Make sure the shapefile has GEOID
    if "GEOID" not in counties_gdf.columns:
        raise ValueError("The shapefile does not contain a GEOID column.")

    # Clean GEOID column
    counties_gdf["GEOID"] = counties_gdf["GEOID"].apply(clean_fips)

    # Merge shapefile with priority scores
    map_df = counties_gdf.merge(
        priority_df,
        left_on="GEOID",
        right_on="county_fips",
        how="left"
    )

    # Convert geopandas dataframe to geojson format
    geojson_data = map_df.__geo_interface__

    # Create interactive choropleth map
    fig = px.choropleth(
        map_df,
        geojson=geojson_data,
        locations="GEOID",
        featureidkey="properties.GEOID",
        color="final_priority_score",
        color_continuous_scale="OrRd",
        title="Mississippi Maternal-Infant Priority Map",
        custom_data=[
            "county_name",
            "final_priority_score",
            "priority_level"
        ]
    )

    # Make the hover cleaner using custom labels
    fig.update_traces(
        hovertemplate=
        "<b>%{customdata[0]}</b><br>" +
        "Final Priority: %{customdata[1]:.2f}<br>" +
        "Priority Level: %{customdata[2]}" +
        "<extra></extra>"
    )

    # Fit the map to Mississippi
    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    # Clean up the layout
    fig.update_layout(
        margin={"r": 0, "t": 55, "l": 0, "b": 0},
        title_x=0.5,
        coloraxis_colorbar=dict(
            title="Priority Score"
        )
    )

    # Create output file path
    output_path = VISUALS_DIR / "mississippi_priority_map_interactive.html"

    # Save interactive map as HTML
    fig.write_html(output_path)

    # Print confirmation
    print(f"Saved interactive map: {output_path}")


# Run the function only when the file is run directly
if __name__ == "__main__":
    create_interactive_priority_map()