# Import libraries
from pathlib import Path
import sqlite3
import pandas as pd


"""
Purpose of this script:
    Take the cleaned CSV files
    Create a SQLite database
    Create database tables
    Load the cleaned data into the database
"""


# Finds the main project folder
BASE_DIR = Path(__file__).resolve().parents[1]

# Finds the data_clean folder inside the main project folder
CLEAN_DIR = BASE_DIR / "data_clean"

# Creates the path where the SQLite database will be saved
DB_PATH = BASE_DIR / "born_at_risk_ms.db"


# These are the cleaned CSV files created from clean_data.py
PLACES_CLEAN_FILE = CLEAN_DIR / "places_clean.csv"
SVI_CLEAN_FILE = CLEAN_DIR / "svi_clean.csv"
CHR_CLEAN_FILE = CLEAN_DIR / "chr_clean.csv"
MASTER_FILE = CLEAN_DIR / "county_health_priority_base.csv"


# Build the SQLite database
def build_database():

    # Connect to the SQLite database
    # If the database file does not exist, SQLite creates it automatically
    conn = sqlite3.connect(DB_PATH)

    # Read the cleaned PLACES csv file
    # county_fips is read as string because FIPS is an ID, not a number
    places = pd.read_csv(PLACES_CLEAN_FILE, dtype={"county_fips": str})

    # Read the cleaned SVI csv file
    # county_fips is read as string so it can join correctly with other tables
    svi = pd.read_csv(SVI_CLEAN_FILE, dtype={"county_fips": str})

    # Read the cleaned County Health Rankings csv file
    # county_fips is read as string for consistent joining
    chr_data = pd.read_csv(CHR_CLEAN_FILE, dtype={"county_fips": str})

    # Read the master joined csv file
    # This file has all 3 datasets joined together
    master = pd.read_csv(MASTER_FILE, dtype={"county_fips": str})

    # Create a counties table from the master dataset
    # This table stores the basic county information only
    counties = master[["county_fips", "county_name", "population", "adult_population"]].copy()

    # Save the PLACES dataframe as a SQL table named places_health
    places.to_sql("places_health", conn, if_exists="replace", index=False)

    # Save the SVI dataframe as a SQL table named social_vulnerability
    svi.to_sql("social_vulnerability", conn, if_exists="replace", index=False)

    # Save the County Health Rankings dataframe as a SQL table named county_health_rankings
    chr_data.to_sql("county_health_rankings", conn, if_exists="replace", index=False)

    # Save the basic county information as a SQL table named counties
    counties.to_sql("counties", conn, if_exists="replace", index=False)

    # Save the full joined master dataset as a SQL table named master_county_data
    master.to_sql("master_county_data", conn, if_exists="replace", index=False)

    # Save all database changes
    conn.commit()

    # Print success message
    print("Database created successfully.")

    # Print where the database was saved
    print(f"Database saved at: {DB_PATH}")

    # List of tables we created
    tables = [
        "counties",
        "places_health",
        "social_vulnerability",
        "county_health_rankings",
        "master_county_data",
    ]

    # Loop through each table
    for table in tables:

        # Run a SQL query that counts how many rows are in the table
        count = pd.read_sql_query(f"SELECT COUNT(*) AS row_count FROM {table}", conn)

        # Print the table name and number of rows
        print(f"{table}: {count['row_count'][0]} rows")

    # Close the database connection
    conn.close()


# This makes sure build_database() only runs when this file is run directly
if __name__ == "__main__":

    # Run the function that builds the database
    build_database()