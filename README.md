# Born at Risk
## A Mississippi Maternal-Infant Health Priority Index

### Project Overview
Born at Risk is a SQL-based public health data system that identifies Mississippi counties where maternal and infant health risks overlap with social vulnerability, chronic disease burden, and healthcare access barriers.

The goal is to help public health leaders understand where limited maternal and infant health resources may be needed first.

### Main Question
Which Mississippi counties should be prioritized for maternal and infant health intervention?

### Why This Matters
Mississippi faces serious maternal and infant health challenges, including high preterm birth and infant mortality rates. These outcomes are connected to broader public health factors such as poverty, rural access barriers, chronic disease burden, transportation limitations, and healthcare access.

### Datasets Used
- CDC PLACES
- CDC/ATSDR Social Vulnerability Index
- U.S. Census data
- Maternal and infant health outcome data

### Database Design
The project organizes data into structured tables connected by county-level geographic identifiers such as FIPS/GEOID.

Main tables:
- counties
- svi
- places_health
- maternal_infant_outcomes
- priority_scores

### Methods
1. Collected public health and demographic datasets
2. Filtered data to Mississippi counties
3. Cleaned and standardized county names/FIPS codes
4. Loaded cleaned data into a SQL database
5. Ran SQL queries to compare counties and identify high-risk areas
6. Created a maternal-infant priority score
7. Built visualizations to communicate findings

### Priority Score
The priority score combines multiple risk domains:
- Infant outcome burden
- Social vulnerability
- Chronic disease burden
- Healthcare access barriers
- Transportation/rural access barriers

Each domain is normalized before scoring. The main model uses equal weighting to keep the index transparent and avoid unsupported assumptions.

### Key Findings
To be completed after analysis.

### Visualizations
To be completed after analysis.

### How to Run
To be completed after code is finalized.

### Project Structure
born-at-risk-ms/
│
├── data_raw/
├── data_clean/
├── sql/
├── notebooks/
├── visuals/
├── presentation/
├── README.md
└── main.py

### Limitations
This project is a public health decision-support prototype. It does not predict individual medical risk or replace professional public health judgment.

### Author
Mashrafee Aryan
