# Import libraries
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


"""
Purpose of this script:
    Read the priority score csv
    Read the county shapefile
    Merge both using county FIPS
    Create a Mississippi county priority map
    Save the map inside visuals folder
"""


# Finds main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

# Raw data folder path
RAW_DIR = BASE_DIR / "data_raw"

# Clean data folder path
CLEAN_DIR = BASE_DIR / "data_clean"

# Visuals folder path
VISUALS_DIR = BASE_DIR / "visuals"

# Makes visuals folder if it does not exist
VISUALS_DIR.mkdir(exist_ok=True)

# Path to priority score csv
PRIORITY_FILE = CLEAN_DIR / "priority_scores.csv"

# Path to shapefile
# Make sure your shapefile folder name matches this
MAP_FILE = RAW_DIR / "tl_2024_us_county" / "tl_2024_us_county.shp"


# Clean FIPS code and convert it to 5-digit text
def clean_fips(value):
    # Return nothing if value is missing
    if pd.isna(value):
        return None

    # Try converting number-like values to 5-digit string
    try:
        return str(int(float(value))).zfill(5)

    # If that fails, clean as text and make it 5 digits
    except ValueError:
        return str(value).strip().zfill(5)


# Create Mississippi priority map
def create_priority_map():
    # Read priority score csv
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

    # Make sure GEOID exists because that is what we use to join
    if "GEOID" not in counties_gdf.columns:
        raise ValueError("The shapefile does not contain a GEOID column.")

    # Clean GEOID column
    counties_gdf["GEOID"] = counties_gdf["GEOID"].apply(clean_fips)

    # Merge county boundaries with priority scores
    map_df = counties_gdf.merge(
        priority_df,
        left_on="GEOID",
        right_on="county_fips",
        how="left"
    )

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 12))

    # Plot counties colored by final priority score
    map_df.plot(
        column="final_priority_score",
        cmap="OrRd",
        linewidth=0.8,
        edgecolor="black",
        legend=True,
        ax=ax,
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "black",
            "label": "No data"
        }
    )

    # Add title
    ax.set_title("Mississippi County Maternal-Infant Priority Map", fontsize=16)

    # Remove axes
    ax.axis("off")

    # Label top 5 highest-priority counties
    top5 = map_df.sort_values("final_priority_score", ascending=False).head(5)

    # Loop through top 5 counties
    for _, row in top5.iterrows():
        # Skip if geometry is missing
        if row.geometry is None:
            continue

        # Get the center point of the county
        point = row.geometry.centroid

        # Add county name label
        ax.text(
            point.x,
            point.y,
            row["county_name"],
            fontsize=8,
            ha="center"
        )

    # Make layout cleaner
    plt.tight_layout()

    # Create output file path
    output_path = VISUALS_DIR / "mississippi_priority_map.png"

    # Save the map
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    # Close plot
    plt.close()

    # Print confirmation
    print(f"Saved: {output_path}")


# Run function only when file is run directly
if __name__ == "__main__":
    create_priority_map()