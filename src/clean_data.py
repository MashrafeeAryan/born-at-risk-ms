#Import the libraries
from pathlib import Path
import pandas as pd
"""
Purpose of this script:
    Take the 3 raw datasets
    Clean ONLY the useful columns
    Standardize FIPS 
    Create one master CSV
    
"""

#Finds main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

#Raw datasets path
RAW_DIR = BASE_DIR / "data_raw"

#Clean datasets path
CLEAN_DIR = BASE_DIR / "data_clean"

#Make the folder if it's not there
CLEAN_DIR.mkdir(exist_ok=True)

PLACES_FILE = RAW_DIR / "places_county_2024.csv"
SVI_FILE = RAW_DIR / "svi_mississippi_county.csv"
CHR_FILE = RAW_DIR / "county_health_ranking_ms_2025.csv"



def clean_fips(value):
    """
    Converts FIPS code to 5-digit text.
    Example: 28049 stays '28049'
    """
    if pd.isna(value):
        return None

    #Converts the value/FIPS number into text or string
    try:
        return str(int(float(value))).zfill(5)
    #If FIPS column doesn't have a specifc number, we just return five values
    except ValueError:
        return str(value).strip().zfill(5)


# Clean CDC PLACES Dataset
def clean_places():
    #Read the csv file. Also, reads the columns CountyFIPS as string.
    places = pd.read_csv(PLACES_FILE, dtype={"CountyFIPS": str})

    # Filter Mississippi only
    places_ms = places[places["StateAbbr"] == "MS"].copy()

    # Keep only useful columns
    #Converts the column name to something easily understandable
    #pct means percentage
    columns_to_keep = {
        "CountyFIPS": "county_fips",
        "CountyName": "county_name",
        "TotalPopulation": "population",
        "TotalPop18plus": "adult_population",

        # Healthcare access
        "ACCESS2_CrudePrev": "uninsured_places_pct",

        # Chronic disease / health burden
        "DIABETES_CrudePrev": "diabetes_pct",
        "OBESITY_CrudePrev": "obesity_pct",
        "BPHIGH_CrudePrev": "high_blood_pressure_pct",
        "CSMOKING_CrudePrev": "smoking_pct",
        "LPA_CrudePrev": "physical_inactivity_pct",
        "PHLTH_CrudePrev": "poor_physical_health_pct",
        "MHLTH_CrudePrev": "poor_mental_health_pct",
        "DEPRESSION_CrudePrev": "depression_pct",
    }

    #Rename columns
    places_clean = places_ms[list(columns_to_keep.keys())].rename(columns=columns_to_keep)

    #Apply the clean_fips function on FIPS column
    places_clean["county_fips"] = places_clean["county_fips"].apply(clean_fips)

    #Creates the csv file of palces_clean
    output_path = CLEAN_DIR / "places_clean.csv"
    places_clean.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"PLACES rows: {len(places_clean)}")

    return places_clean



# Clean CDC/ATSDR SVI Dataset
def clean_svi():
    # Read the SVI csv file. Also, reads the FIPS column as string.
    svi = pd.read_csv(SVI_FILE, dtype={"FIPS": str})

    # Keep only useful columns
    # Converts the column names to something easily understandable
    # pct means percentage
    columns_to_keep = {
        "FIPS": "county_fips",
        "COUNTY": "county_name",
        "E_TOTPOP": "svi_population",

        # Raw social vulnerability indicators
        # These are actual estimated percentages from the SVI dataset
        "EP_POV150": "poverty_150_pct",
        "EP_UNEMP": "unemployment_svi_pct",
        "EP_UNINSUR": "uninsured_svi_pct",
        "EP_DISABL": "disability_pct",
        "EP_SNGPNT": "single_parent_pct",
        "EP_NOVEH": "no_vehicle_pct",
        "EP_NOINT": "no_internet_pct",

        # SVI theme rankings
        # These are percentile/ranking scores from 0 to 1
        # Higher value means higher social vulnerability
        "RPL_THEME1": "svi_socioeconomic",
        "RPL_THEME2": "svi_household",
        "RPL_THEME3": "svi_minority_language",
        "RPL_THEME4": "svi_housing_transportation",
        "RPL_THEMES": "svi_overall",
    }

    # Rename columns and keep only the columns listed above
    svi_clean = svi[list(columns_to_keep.keys())].rename(columns=columns_to_keep)

    # Apply the clean_fips function on FIPS column
    svi_clean["county_fips"] = svi_clean["county_fips"].apply(clean_fips)

    # Creates the csv file of svi_clean
    output_path = CLEAN_DIR / "svi_clean.csv"
    svi_clean.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"SVI rows: {len(svi_clean)}")

    return svi_clean


# Clean County Health Rankings Dataset
def clean_county_health_rankings():
    # Read the County Health Rankings csv file.
    # This file is tab-separated, so we use sep="\t".
    # Also, reads the FIPS column as string.
    chr_data = pd.read_csv(CHR_FILE, sep="\t", dtype={"FIPS": str})

    # Clean column names by removing extra spaces
    # Example: " FIPS " becomes "FIPS"
    chr_data.columns = chr_data.columns.astype(str).str.strip()

    # Sometimes there may be blank rows.
    # This removes rows where FIPS is missing.
    chr_data = chr_data.dropna(subset=["FIPS"])

    # Apply the clean_fips function on FIPS column
    chr_data["FIPS"] = chr_data["FIPS"].apply(clean_fips)

    # Keep only Mississippi county rows.
    # Mississippi FIPS codes start with 28.
    chr_data = chr_data[chr_data["FIPS"].str.startswith("28")].copy()

    # Keep only useful columns
    # Converts the column names to something easily understandable
    # pct means percentage
    columns_to_keep = {
        "FIPS": "county_fips",
        "County": "county_name",

        # Maternal/infant outcome indicator
        # This is useful because low birth weight is directly related to infant health
        "% Low Birth Weight": "low_birth_weight_pct",

        # Healthcare access indicators
        "# Uninsured": "uninsured_count",
        "% Uninsured": "uninsured_chr_pct",
        "# Primary Care Physicians": "primary_care_physicians_count",
        "Primary Care Physicians Rate": "primary_care_physicians_rate",
        "Primary Care Physicians Ratio": "primary_care_physicians_ratio",
        "# Mental Health Providers": "mental_health_providers_count",
        "Mental Health Provider Rate": "mental_health_providers_rate",
        "Mental Health Provider Ratio": "mental_health_providers_ratio",

        # Community resource / barrier indicators
        "% Severe Housing Problems": "severe_housing_problems_pct",
        "Severe Housing Cost Burden": "severe_housing_cost_burden_pct",
        "% Children in Poverty": "children_in_poverty_pct",
        "Food Environment Index": "food_environment_index",
        "% Households with Broadband Access": "broadband_access_pct",
        "# Households with Broadband Access": "broadband_access_count",
        "% Household Income Required for Child Care Expenses": "child_care_cost_burden_pct",
    }

    # Rename columns and keep only the columns listed above
    chr_clean = chr_data[list(columns_to_keep.keys())].rename(columns=columns_to_keep)

    # Creates the csv file of chr_clean
    output_path = CLEAN_DIR / "chr_clean.csv"
    chr_clean.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"County Health Rankings rows: {len(chr_clean)}")
    print("Columns kept from County Health Rankings:")
    print(chr_clean.columns.tolist())

    return chr_clean


# Create one master table by joining the cleaned datasets
def create_master_table(places_clean, svi_clean, chr_clean):
    print("Creating master joined table...")

    # Join CDC PLACES with SVI using county_fips
    # county_name is dropped from SVI because PLACES already has county_name
    master = places_clean.merge(
        svi_clean.drop(columns=["county_name"], errors="ignore"),
        on="county_fips",
        how="left"
    )

    # Join the result with County Health Rankings using county_fips
    # county_name is dropped from CHR because PLACES already has county_name
    master = master.merge(
        chr_clean.drop(columns=["county_name"], errors="ignore"),
        on="county_fips",
        how="left"
    )

    # Check if any counties did not match during the joins
    missing_svi = master["svi_overall"].isna().sum()
    missing_chr = master["low_birth_weight_pct"].isna().sum()

    print(f"Counties missing SVI data: {missing_svi}")
    print(f"Counties missing County Health Rankings data: {missing_chr}")

    # Save the final joined table as a CSV file
    output_path = CLEAN_DIR / "county_health_priority_base.csv"
    master.to_csv(output_path, index=False)

    print(f"Saved: {output_path}")
    print(f"Master table rows: {len(master)}")
    print(f"Master table columns: {len(master.columns)}")

    return master


# -----------------------------
# Main program
# -----------------------------
if __name__ == "__main__":
    places_clean = clean_places()
    svi_clean = clean_svi()
    chr_clean = clean_county_health_rankings()

    master = create_master_table(places_clean, svi_clean, chr_clean)

    print("\nCleaning complete.")
    print("Files created in data_clean/:")
    print("- places_clean.csv")
    print("- svi_clean.csv")
    print("- chr_clean.csv")
    print("- county_health_priority_base.csv")

    print("\nPreview of master table:")
    print(master.head())