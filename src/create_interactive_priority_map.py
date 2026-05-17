# Import libraries
from pathlib import Path
import base64
import mimetypes
import pandas as pd
import geopandas as gpd
import plotly.express as px


"""
Purpose of this script:
    Read the priority score csv
    Read the county shapefile
    Merge both using county FIPS
    Create an interactive Mississippi county map
    Add a click popup with county details
    Use a real cartoon doctor image beside the popup
    Save the map as a custom HTML file
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

# Path to merged county base csv
BASE_FILE = CLEAN_DIR / "county_health_priority_base.csv"

# Path to county shapefile
MAP_FILE = RAW_DIR / "tl_2024_us_county" / "tl_2024_us_county.shp"

# Path to doctor image
DOCTOR_IMAGE_FILE = VISUALS_DIR / "doctor_cartoon.png"


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


# Convert image to base64 so the HTML works even after moving the file
def image_to_data_uri(image_path):
    # Return empty string if the image is missing
    if not image_path.exists():
        print(f"Warning: doctor image not found at {image_path}")
        return ""

    # Guess image type
    mime_type, _ = mimetypes.guess_type(image_path)

    # Use png as default image type
    if mime_type is None:
        mime_type = "image/png"

    # Read image bytes
    image_bytes = image_path.read_bytes()

    # Convert image bytes to base64 text
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    # Return image data URI
    return f"data:{mime_type};base64,{encoded}"


# Create interactive Mississippi county priority map
def create_interactive_priority_map():
    # Convert doctor image into HTML-safe image source
    doctor_image_src = image_to_data_uri(DOCTOR_IMAGE_FILE)

    # Read priority score csv file
    priority_df = pd.read_csv(PRIORITY_FILE, dtype={"county_fips": str})

    # Clean county_fips column in priority file
    priority_df["county_fips"] = priority_df["county_fips"].apply(clean_fips)

    # Read merged county base csv file
    base_df = pd.read_csv(BASE_FILE, dtype={"county_fips": str})

    # Clean county_fips column in base file
    base_df["county_fips"] = base_df["county_fips"].apply(clean_fips)

    # Keep useful extra detail columns from the base file
    detail_columns = [
        "county_fips",
        "low_birth_weight_pct",
        "diabetes_pct",
        "obesity_pct",
        "uninsured_places_pct",
        "children_in_poverty_pct",
        "no_vehicle_pct",
        "severe_housing_problems_pct",
        "broadband_access_pct",
        "food_environment_index",
    ]

    # Add missing columns as empty if they do not exist
    for col in detail_columns:
        if col not in base_df.columns:
            base_df[col] = pd.NA

    # Keep only the detail columns we need
    base_small = base_df[detail_columns].copy()

    # Merge priority data with extra county details
    priority_df = priority_df.merge(
        base_small,
        on="county_fips",
        how="left"
    )

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

    # Add missing expected columns if needed
    expected_columns = [
        "county_name",
        "final_priority_score",
        "priority_level",
        "maternal_infant_outcome_score",
        "chronic_disease_score",
        "social_vulnerability_score",
        "access_resource_barrier_score",
        "low_birth_weight_pct",
        "diabetes_pct",
        "obesity_pct",
        "uninsured_places_pct",
        "children_in_poverty_pct",
        "no_vehicle_pct",
        "severe_housing_problems_pct",
        "broadband_access_pct",
        "food_environment_index",
    ]

    # Add empty columns for anything missing
    for col in expected_columns:
        if col not in map_df.columns:
            map_df[col] = pd.NA

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
            "priority_level",
            "maternal_infant_outcome_score",
            "chronic_disease_score",
            "social_vulnerability_score",
            "access_resource_barrier_score",
            "low_birth_weight_pct",
            "diabetes_pct",
            "obesity_pct",
            "uninsured_places_pct",
            "children_in_poverty_pct",
            "no_vehicle_pct",
            "severe_housing_problems_pct",
            "broadband_access_pct",
            "food_environment_index",
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

    # Make the plot bigger on the webpage
    fig.update_layout(
        height=850,
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        title_x=0.5,
        coloraxis_colorbar=dict(title="Priority Score")
    )

    # Convert figure to HTML div
    # include_plotlyjs=True makes the HTML work offline during presentation
    plot_div = fig.to_html(
        full_html=False,
        include_plotlyjs=True,
        div_id="priorityMap"
    )

    # Create full custom HTML page
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mississippi Maternal-Infant Priority Map</title>

    <style>
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #fffaf8;
        }}

        .map-wrapper {{
            width: 98vw;
            max-width: 1550px;
            margin: 0 auto;
            padding: 5px 10px 10px 10px;
        }}

        #priorityMap {{
            width: 100% !important;
            min-height: 850px;
        }}

        .modal-overlay {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(35, 25, 25, 0.48);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .modal-content-wrap {{
            display: flex;
            align-items: center;
            gap: 24px;
            max-width: 1120px;
            width: 100%;
            justify-content: center;
        }}

        .county-card {{
            background: linear-gradient(180deg, #fff9f6 0%, #fff2ec 100%);
            width: 650px;
            max-width: 100%;
            max-height: 88vh;
            overflow-y: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
            border-radius: 24px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.24);
            border: 3px solid #ffd7c9;
            padding: 24px 24px 18px 24px;
            position: relative;
        }}

        .county-card::-webkit-scrollbar {{
            display: none;
        }}

        .county-title {{
            font-size: 30px;
            font-weight: 800;
            color: #7a2f1f;
            margin-bottom: 6px;
        }}

        .county-subtitle {{
            font-size: 15px;
            color: #8f5a4b;
            margin-bottom: 16px;
        }}

        .close-btn {{
            position: absolute;
            top: 14px;
            right: 16px;
            border: none;
            background: #ffdfd3;
            color: #7a2f1f;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }}

        .badge-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 18px;
        }}

        .badge {{
            background: #fff;
            border: 2px solid #ffd8ca;
            border-radius: 999px;
            padding: 10px 14px;
            font-size: 14px;
            color: #6d4337;
            font-weight: 700;
        }}

        .badge-critical {{
            background: #ffe1dc;
            border-color: #ff8a7a;
            color: #8a1f12;
        }}

        .badge-high {{
            background: #fff0d6;
            border-color: #ffbe63;
            color: #8a5200;
        }}

        .badge-moderate {{
            background: #fff9d8;
            border-color: #e8d45c;
            color: #6b5d00;
        }}

        .badge-lower {{
            background: #e7f7ec;
            border-color: #8ed9a6;
            color: #1f6b3a;
        }}

        .section-title {{
            font-size: 17px;
            font-weight: 800;
            color: #7a2f1f;
            margin-top: 12px;
            margin-bottom: 10px;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }}

        .mini-card {{
            background: #ffffff;
            border: 2px solid #ffe2d7;
            border-radius: 18px;
            padding: 12px 14px;
        }}

        .mini-label {{
            font-size: 13px;
            color: #8c655a;
            margin-bottom: 4px;
            font-weight: 600;
        }}

        .mini-value {{
            font-size: 22px;
            font-weight: 800;
            color: #5a2a1e;
        }}

        .interpretation-box {{
            margin-top: 16px;
            background: #fff;
            border: 2px dashed #ffc8b8;
            border-radius: 18px;
            padding: 14px 16px;
            color: #6d4337;
            font-size: 15px;
            line-height: 1.45;
        }}

        .interpretation-title {{
            font-weight: 800;
            color: #7a2f1f;
            margin-bottom: 6px;
        }}

        .doctor-wrap {{
            width: 255px;
            min-width: 255px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .doctor-img {{
            width: 245px;
            max-height: 420px;
            object-fit: contain;
            filter: drop-shadow(0 12px 18px rgba(0, 0, 0, 0.18));
        }}

        .doctor-note {{
            margin-top: 8px;
            text-align: center;
            color: #7a2f1f;
            font-weight: 800;
            font-size: 14px;
            background: #fff6f2;
            border: 2px solid #ffd7c9;
            border-radius: 14px;
            padding: 9px 11px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.10);
        }}

        @media (max-width: 950px) {{
            .modal-content-wrap {{
                flex-direction: column;
            }}

            .doctor-wrap {{
                width: 185px;
                min-width: 185px;
            }}

            .doctor-img {{
                width: 180px;
                max-height: 300px;
            }}
        }}

        @media (max-width: 700px) {{
            .card-grid {{
                grid-template-columns: 1fr;
            }}

            .county-title {{
                font-size: 24px;
            }}
        }}
    </style>
</head>

<body>

    <div class="map-wrapper">
        {plot_div}
    </div>

    <div class="modal-overlay" id="countyModal">
        <div class="modal-content-wrap">

            <div class="county-card">
                <button class="close-btn" id="closeModalBtn">×</button>

                <div class="county-title" id="modalCountyName">County Name</div>
                <div class="county-subtitle">Maternal-Infant Priority Profile</div>

                <div class="badge-row">
                    <div class="badge" id="modalFinalPriority">Final Priority: --</div>
                    <div class="badge" id="modalPriorityLevel">Priority Level: --</div>
                </div>

                <div class="section-title">Domain Scores</div>

                <div class="card-grid">
                    <div class="mini-card">
                        <div class="mini-label">Maternal/Infant Outcome Score</div>
                        <div class="mini-value" id="modalMaternalScore">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Chronic Disease Score</div>
                        <div class="mini-value" id="modalChronicScore">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Social Vulnerability Score</div>
                        <div class="mini-value" id="modalSocialScore">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Access/Resource Barrier Score</div>
                        <div class="mini-value" id="modalAccessScore">--</div>
                    </div>
                </div>

                <div class="section-title">Additional County Indicators</div>

                <div class="card-grid">
                    <div class="mini-card">
                        <div class="mini-label">Low Birth Weight</div>
                        <div class="mini-value" id="modalLBW">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Diabetes</div>
                        <div class="mini-value" id="modalDiabetes">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Obesity</div>
                        <div class="mini-value" id="modalObesity">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Uninsured</div>
                        <div class="mini-value" id="modalUninsured">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Children in Poverty</div>
                        <div class="mini-value" id="modalChildPoverty">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">No Vehicle</div>
                        <div class="mini-value" id="modalNoVehicle">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Severe Housing Problems</div>
                        <div class="mini-value" id="modalHousing">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Broadband Access</div>
                        <div class="mini-value" id="modalBroadband">--</div>
                    </div>

                    <div class="mini-card">
                        <div class="mini-label">Food Environment Index</div>
                        <div class="mini-value" id="modalFoodEnv">--</div>
                    </div>
                </div>

                <div class="interpretation-box">
                    <div class="interpretation-title">County Interpretation</div>
                    <div id="modalInterpretation">
                        Click a county to see how overlapping risks shape its priority score.
                    </div>
                </div>
            </div>

            <div class="doctor-wrap">
                <div>
                    <img class="doctor-img" src="{doctor_image_src}" alt="Cartoon doctor">

                    <div class="doctor-note" id="doctorNote">Let’s look at this county!</div>
                </div>
            </div>

        </div>
    </div>

    <script>
        const modal = document.getElementById("countyModal");
        const closeBtn = document.getElementById("closeModalBtn");

        function formatNumber(value, digits = 2) {{
            if (value === null || value === undefined || value === "" || value === "nan") {{
                return "N/A";
            }}

            const num = Number(value);

            if (isNaN(num)) {{
                return value;
            }}

            return num.toFixed(digits);
        }}

        function formatPercent(value, digits = 1) {{
            if (value === null || value === undefined || value === "" || value === "nan") {{
                return "N/A";
            }}

            const num = Number(value);

            if (isNaN(num)) {{
                return value;
            }}

            return num.toFixed(digits) + "%";
        }}

        function fillModal(customData) {{
            const countyName = customData[0];
            const finalPriority = customData[1];
            const priorityLevel = customData[2];
            const maternalScore = customData[3];
            const chronicScore = customData[4];
            const socialScore = customData[5];
            const accessScore = customData[6];
            const lowBirthWeight = customData[7];
            const diabetes = customData[8];
            const obesity = customData[9];
            const uninsured = customData[10];
            const childPoverty = customData[11];
            const noVehicle = customData[12];
            const housing = customData[13];
            const broadband = customData[14];
            const foodEnv = customData[15];

            const score = Number(finalPriority);

            document.getElementById("modalCountyName").textContent = countyName || "Unknown County";
            document.getElementById("modalFinalPriority").textContent = "Final Priority: " + formatNumber(finalPriority, 2);

            const priorityBadge = document.getElementById("modalPriorityLevel");
            priorityBadge.textContent = "Priority Level: " + (priorityLevel || "N/A");

            priorityBadge.classList.remove(
                "badge-critical",
                "badge-high",
                "badge-moderate",
                "badge-lower"
            );

            if (priorityLevel === "Critical Priority") {{
                priorityBadge.classList.add("badge-critical");
            }} else if (priorityLevel === "High Priority") {{
                priorityBadge.classList.add("badge-high");
            }} else if (priorityLevel === "Moderate Priority") {{
                priorityBadge.classList.add("badge-moderate");
            }} else {{
                priorityBadge.classList.add("badge-lower");
            }}

            document.getElementById("modalMaternalScore").textContent = formatNumber(maternalScore, 2);
            document.getElementById("modalChronicScore").textContent = formatNumber(chronicScore, 2);
            document.getElementById("modalSocialScore").textContent = formatNumber(socialScore, 2);
            document.getElementById("modalAccessScore").textContent = formatNumber(accessScore, 2);

            document.getElementById("modalLBW").textContent = formatPercent(lowBirthWeight, 1);
            document.getElementById("modalDiabetes").textContent = formatPercent(diabetes, 1);
            document.getElementById("modalObesity").textContent = formatPercent(obesity, 1);
            document.getElementById("modalUninsured").textContent = formatPercent(uninsured, 1);
            document.getElementById("modalChildPoverty").textContent = formatPercent(childPoverty, 1);
            document.getElementById("modalNoVehicle").textContent = formatPercent(noVehicle, 1);
            document.getElementById("modalHousing").textContent = formatPercent(housing, 1);
            document.getElementById("modalBroadband").textContent = formatPercent(broadband, 1);
            document.getElementById("modalFoodEnv").textContent = formatNumber(foodEnv, 2);

            let interpretation = "";
            let doctorMessage = "";

            if (!isNaN(score) && score >= 80) {{
                interpretation =
                    countyName + " is classified as Critical Priority because multiple risk domains are high at the same time. " +
                    "This suggests that maternal-infant health concerns overlap with broader chronic disease, social vulnerability, " +
                    "and access/resource barriers. This county may need urgent attention for outreach, prevention, and support planning.";

                doctorMessage = "This county needs attention first.";
            }} else if (!isNaN(score) && score >= 60) {{
                interpretation =
                    countyName + " is classified as High Priority. The county shows important overlapping risks, " +
                    "meaning public health teams may want to monitor it closely and consider targeted support.";

                doctorMessage = "Several warning signs here.";
            }} else if (!isNaN(score) && score >= 40) {{
                interpretation =
                    countyName + " is classified as Moderate Priority. Some risk factors are present, but the overall overlapping burden " +
                    "is lower than the highest-priority counties.";

                doctorMessage = "Worth watching closely.";
            }} else {{
                interpretation =
                    countyName + " is classified as Lower Priority based on this index. This does not mean there are no health concerns, " +
                    "but the county has a lower combined burden compared with other Mississippi counties in this dataset.";

                doctorMessage = "Lower combined risk here.";
            }}

            document.getElementById("modalInterpretation").textContent = interpretation;
            document.getElementById("doctorNote").textContent = doctorMessage;
        }}

        document.getElementById("priorityMap").on("plotly_click", function(data) {{
            if (!data || !data.points || data.points.length === 0) {{
                return;
            }}

            const customData = data.points[0].customdata;

            fillModal(customData);

            modal.style.display = "flex";
        }});

        closeBtn.addEventListener("click", function() {{
            modal.style.display = "none";
        }});

        modal.addEventListener("click", function(event) {{
            if (event.target === modal) {{
                modal.style.display = "none";
            }}
        }});

        document.addEventListener("keydown", function(event) {{
            if (event.key === "Escape") {{
                modal.style.display = "none";
            }}
        }});
    </script>

</body>
</html>
"""

    # Create output file path
    output_path = VISUALS_DIR / "mississippi_priority_map_interactive.html"

    # Save custom HTML file
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    # Print confirmation
    print(f"Saved interactive map: {output_path}")


# Run the function only when the file is run directly
if __name__ == "__main__":
    create_interactive_priority_map()