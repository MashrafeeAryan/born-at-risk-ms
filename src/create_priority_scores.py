# Import libraries
from pathlib import Path
import sqlite3
import pandas as pd


"""
Purpose of this script:
    Use the cleaned master county dataset
    Create domain scores for each county
    Create one final maternal-infant support priority score
    Save the score as a CSV
    Add the score table to the SQLite database
"""


# Finds main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

# Clean datasets path
CLEAN_DIR = BASE_DIR / "data_clean"

# Master cleaned dataset path
MASTER_FILE = CLEAN_DIR / "county_health_priority_base.csv"

# Priority score output path
PRIORITY_FILE = CLEAN_DIR / "priority_scores.csv"

# SQLite database path
DB_PATH = BASE_DIR / "born_at_risk_ms.db"


# Converts a column to numeric values
# If a value cannot be converted, it becomes NaN
def make_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# Converts a column into a 0-100 percentile score
# Higher original value = higher risk score
def percentile_score(series):
    return series.rank(pct=True) * 100


# Converts a column into a 0-100 inverse percentile score
# Used when higher original value is GOOD, not bad
# Example: higher broadband access is good, so lower broadband should get higher risk score
def inverse_percentile_score(series):
    return 100 - percentile_score(series)


# Creates a score by averaging several columns
def average_score(df, columns):
    existing_columns = [col for col in columns if col in df.columns]

    if len(existing_columns) == 0:
        raise ValueError("None of the selected columns exist in the dataframe.")

    return df[existing_columns].mean(axis=1)


# Creates priority level from final score
def assign_priority_level(score):
    if score >= 80:
        return "Critical Priority"
    elif score >= 60:
        return "High Priority"
    elif score >= 40:
        return "Moderate Priority"
    else:
        return "Lower Priority"


# Create priority score table
def create_priority_scores():

    # Read the master joined dataset
    # county_fips is read as string because FIPS is an ID
    master = pd.read_csv(MASTER_FILE, dtype={"county_fips": str})

    # List of columns that should be numeric
    numeric_columns = [
        "low_birth_weight_pct",

        "diabetes_pct",
        "obesity_pct",
        "high_blood_pressure_pct",
        "smoking_pct",
        "physical_inactivity_pct",
        "poor_physical_health_pct",
        "poor_mental_health_pct",
        "depression_pct",

        "svi_overall",
        "svi_socioeconomic",
        "svi_household",
        "svi_minority_language",
        "svi_housing_transportation",

        "uninsured_places_pct",
        "uninsured_chr_pct",
        "no_vehicle_pct",
        "children_in_poverty_pct",
        "severe_housing_problems_pct",
        "child_care_cost_burden_pct",
        "food_environment_index",
        "broadband_access_pct",
        "primary_care_physicians_rate",
        "mental_health_providers_rate",
    ]

    # Convert selected columns to numbers
    master = make_numeric(master, numeric_columns)

    # Maternal/infant outcome score
    # Right now we use low birth weight because it is the county-level infant health outcome we have
    master["maternal_infant_outcome_score"] = percentile_score(master["low_birth_weight_pct"])

    # Chronic disease burden score
    # These come mainly from CDC PLACES
    master["diabetes_score"] = percentile_score(master["diabetes_pct"])
    master["obesity_score"] = percentile_score(master["obesity_pct"])
    master["high_blood_pressure_score"] = percentile_score(master["high_blood_pressure_pct"])
    master["smoking_score"] = percentile_score(master["smoking_pct"])
    master["physical_inactivity_score"] = percentile_score(master["physical_inactivity_pct"])
    master["poor_physical_health_score"] = percentile_score(master["poor_physical_health_pct"])
    master["poor_mental_health_score"] = percentile_score(master["poor_mental_health_pct"])
    master["depression_score"] = percentile_score(master["depression_pct"])

    master["chronic_disease_score"] = average_score(
        master,
        [
            "diabetes_score",
            "obesity_score",
            "high_blood_pressure_score",
            "smoking_score",
            "physical_inactivity_score",
            "poor_physical_health_score",
            "poor_mental_health_score",
            "depression_score",
        ]
    )

    # Social vulnerability score
    # SVI overall is already a 0-1 percentile/rank, so multiply by 100
    master["social_vulnerability_score"] = master["svi_overall"] * 100

    # Access and resource barrier score
    # Higher uninsured, no vehicle, poverty, housing problems = worse
    master["uninsured_score"] = percentile_score(master["uninsured_chr_pct"])
    master["no_vehicle_score"] = percentile_score(master["no_vehicle_pct"])
    master["children_in_poverty_score"] = percentile_score(master["children_in_poverty_pct"])
    master["severe_housing_score"] = percentile_score(master["severe_housing_problems_pct"])
    master["child_care_cost_score"] = percentile_score(master["child_care_cost_burden_pct"])

    # Higher food environment index is better, so invert it
    master["food_environment_barrier_score"] = inverse_percentile_score(master["food_environment_index"])

    # Higher broadband access is better, so invert it
    master["broadband_barrier_score"] = inverse_percentile_score(master["broadband_access_pct"])

    # Higher provider rate is better, so invert it
    master["primary_care_barrier_score"] = inverse_percentile_score(master["primary_care_physicians_rate"])
    master["mental_health_barrier_score"] = inverse_percentile_score(master["mental_health_providers_rate"])

    master["access_resource_barrier_score"] = average_score(
        master,
        [
            "uninsured_score",
            "no_vehicle_score",
            "children_in_poverty_score",
            "severe_housing_score",
            "child_care_cost_score",
            "food_environment_barrier_score",
            "broadband_barrier_score",
            "primary_care_barrier_score",
            "mental_health_barrier_score",
        ]
    )

    # Final priority score
    # Equal weighting keeps the score transparent and easier to defend
    master["final_priority_score"] = average_score(
        master,
        [
            "maternal_infant_outcome_score",
            "chronic_disease_score",
            "social_vulnerability_score",
            "access_resource_barrier_score",
        ]
    )

    # Round final scores to 2 decimal places
    master["final_priority_score"] = master["final_priority_score"].round(2)

    # Create priority level label
    master["priority_level"] = master["final_priority_score"].apply(assign_priority_level)

    # Keep only the final useful priority score columns
    priority_scores = master[
        [
            "county_fips",
            "county_name",
            "maternal_infant_outcome_score",
            "chronic_disease_score",
            "social_vulnerability_score",
            "access_resource_barrier_score",
            "final_priority_score",
            "priority_level",
        ]
    ].copy()

    # Round domain scores
    score_columns = [
        "maternal_infant_outcome_score",
        "chronic_disease_score",
        "social_vulnerability_score",
        "access_resource_barrier_score",
    ]

    priority_scores[score_columns] = priority_scores[score_columns].round(2)

    # Sort counties from highest priority to lowest priority
    priority_scores = priority_scores.sort_values(
        by="final_priority_score",
        ascending=False
    )

    # Save priority score CSV
    priority_scores.to_csv(PRIORITY_FILE, index=False)

    # Connect to existing SQLite database
    conn = sqlite3.connect(DB_PATH)

    # Add priority_scores table to database
    priority_scores.to_sql("priority_scores", conn, if_exists="replace", index=False)

    # Save database changes
    conn.commit()

    # Print confirmation
    print(f"Saved priority scores to: {PRIORITY_FILE}")
    print("Added priority_scores table to database.")
    print("\nTop 10 priority counties:")

    # Print top 10 counties
    print(priority_scores.head(10).to_string(index=False))

    # Close database connection
    conn.close()

    return priority_scores


# Runs the script only when this file is run directly
if __name__ == "__main__":
    create_priority_scores()