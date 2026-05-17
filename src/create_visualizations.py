# Import libraries
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


"""
Purpose of this script:
    Read data from SQLite database
    Create charts for the project
    Save the charts inside the visuals folder
"""


# Finds main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

# Database path
DB_PATH = BASE_DIR / "born_at_risk_ms.db"

# Visuals folder path
VISUALS_DIR = BASE_DIR / "visuals"

# Make the visuals folder if it is not there
VISUALS_DIR.mkdir(exist_ok=True)


# Load the data needed for visualizations
def load_data():
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)

    # SQL query gets priority scores and useful county indicators
    query = """
    SELECT
        p.county_fips,
        p.county_name,
        p.maternal_infant_outcome_score,
        p.chronic_disease_score,
        p.social_vulnerability_score,
        p.access_resource_barrier_score,
        p.final_priority_score,
        p.priority_level,

        m.low_birth_weight_pct,
        m.svi_overall,
        m.diabetes_pct,
        m.obesity_pct,
        m.uninsured_places_pct,
        m.children_in_poverty_pct,
        m.no_vehicle_pct
    FROM priority_scores p
    JOIN master_county_data m
        ON p.county_fips = m.county_fips
    ORDER BY p.final_priority_score DESC;
    """

    # Run the SQL query and store the result as a pandas dataframe
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    # Return the dataframe so other functions can use it
    return df


# Create bar chart of top 10 priority counties
def plot_top_10_priority_counties(df):
    # Select the top 10 counties because dataframe is already sorted by priority score
    top10 = df.head(10).copy()

    # Sort values so highest score appears at the top of the horizontal chart
    top10 = top10.sort_values("final_priority_score", ascending=True)

    # Create the chart size
    plt.figure(figsize=(10, 6))

    # Create horizontal bar chart
    plt.barh(top10["county_name"], top10["final_priority_score"])

    # Add chart title
    plt.title("Top 10 Mississippi Counties by Maternal-Infant Priority Score")

    # Add x-axis label
    plt.xlabel("Final Priority Score")

    # Add y-axis label
    plt.ylabel("County")

    # Make chart layout cleaner
    plt.tight_layout()

    # Create output file path
    output_path = VISUALS_DIR / "top_10_priority_counties.png"

    # Save the chart as a PNG image
    plt.savefig(output_path, dpi=300)

    # Close the plot so it does not mix with the next chart
    plt.close()

    # Print confirmation
    print(f"Saved: {output_path}")


# Create grouped bar chart for top 5 counties and their domain scores
def plot_domain_scores_top_5(df):
    # Select top 5 counties by final priority score
    top5 = df.head(5).copy()

    # Keep only county name and domain score columns
    domain_df = top5[
        [
            "county_name",
            "maternal_infant_outcome_score",
            "chronic_disease_score",
            "social_vulnerability_score",
            "access_resource_barrier_score",
        ]
    ].copy()

    # Set county name as the index so county names appear on the x-axis
    domain_df = domain_df.set_index("county_name")

    # Create grouped bar chart
    domain_df.plot(kind="bar", figsize=(12, 6))

    # Add chart title
    plt.title("Risk Domain Scores for Top 5 Priority Counties")

    # Add x-axis label
    plt.xlabel("County")

    # Add y-axis label
    plt.ylabel("Score")

    # Rotate county labels so they are easier to read
    plt.xticks(rotation=45, ha="right")

    # Add legend and move it outside the chart
    plt.legend(title="Risk Domain", bbox_to_anchor=(1.05, 1), loc="upper left")

    # Make chart layout cleaner
    plt.tight_layout()

    # Create output file path
    output_path = VISUALS_DIR / "top_5_domain_scores.png"

    # Save the chart as a PNG image
    plt.savefig(output_path, dpi=300)

    # Close the plot
    plt.close()

    # Print confirmation
    print(f"Saved: {output_path}")


# Create scatterplot of social vulnerability vs low birth weight
def plot_svi_vs_low_birth_weight(df):
    # Create the chart size
    plt.figure(figsize=(8, 6))

    # Create scatterplot
    plt.scatter(df["svi_overall"], df["low_birth_weight_pct"])

    # Add chart title
    plt.title("Social Vulnerability vs. Low Birth Weight in Mississippi Counties")

    # Add x-axis label
    plt.xlabel("Overall Social Vulnerability Index")

    # Add y-axis label
    plt.ylabel("% Low Birth Weight")

    # Make chart layout cleaner
    plt.tight_layout()

    # Create output file path
    output_path = VISUALS_DIR / "svi_vs_low_birth_weight.png"

    # Save the chart as a PNG image
    plt.savefig(output_path, dpi=300)

    # Close the plot
    plt.close()

    # Print confirmation
    print(f"Saved: {output_path}")


# Create scatterplot of chronic disease burden vs priority score
def plot_chronic_disease_vs_priority(df):
    # Create a simple chronic disease average using diabetes and obesity
    df["chronic_disease_average"] = df[
        ["diabetes_pct", "obesity_pct"]
    ].mean(axis=1)

    # Create the chart size
    plt.figure(figsize=(8, 6))

    # Create scatterplot
    plt.scatter(df["chronic_disease_average"], df["final_priority_score"])

    # Add chart title
    plt.title("Chronic Disease Burden vs. Final Priority Score")

    # Add x-axis label
    plt.xlabel("Average of Diabetes % and Obesity %")

    # Add y-axis label
    plt.ylabel("Final Priority Score")

    # Make chart layout cleaner
    plt.tight_layout()

    # Create output file path
    output_path = VISUALS_DIR / "chronic_disease_vs_priority_score.png"

    # Save the chart as a PNG image
    plt.savefig(output_path, dpi=300)

    # Close the plot
    plt.close()

    # Print confirmation
    print(f"Saved: {output_path}")


# Create a simple report card for the highest-priority county
def create_county_report_card(df):
    # Select the first row because it is the highest-priority county
    county = df.iloc[0]

    # Create report card text using the highest-priority county data
    report_text = f"""
Born at Risk: County Report Card

County: {county['county_name']}

Priority Level: {county['priority_level']}
Final Priority Score: {county['final_priority_score']}

Domain Scores:
Maternal/Infant Outcome Score: {county['maternal_infant_outcome_score']}
Chronic Disease Score: {county['chronic_disease_score']}
Social Vulnerability Score: {county['social_vulnerability_score']}
Access/Resource Barrier Score: {county['access_resource_barrier_score']}

Selected Indicators:
Low Birth Weight %: {county['low_birth_weight_pct']}
SVI Overall: {county['svi_overall']}
Diabetes %: {county['diabetes_pct']}
Obesity %: {county['obesity_pct']}
Uninsured %: {county['uninsured_places_pct']}
Children in Poverty %: {county['children_in_poverty_pct']}
No Vehicle %: {county['no_vehicle_pct']}

Interpretation:
This county ranks as a high-priority location because multiple risk domains overlap.
The score does not predict individual medical risk. It identifies county-level public health burden
and helps guide where maternal and infant health support may be needed first.
"""

    # Create output file path
    output_path = VISUALS_DIR / "highest_priority_county_report_card.txt"

    # Open the text file and write the report card
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report_text)

    # Print confirmation
    print(f"Saved: {output_path}")


# Main function that runs everything
def main():
    # Load the data from the database
    df = load_data()

    # Create top 10 priority counties chart
    plot_top_10_priority_counties(df)

    # Create top 5 domain score chart
    plot_domain_scores_top_5(df)

    # Create SVI vs low birth weight scatterplot
    plot_svi_vs_low_birth_weight(df)

    # Create chronic disease vs priority score scatterplot
    plot_chronic_disease_vs_priority(df)

    # Create county report card
    create_county_report_card(df)

    # Print final message
    print("\nVisualizations complete.")


# Run main only when this file is run directly
if __name__ == "__main__":
    main()