-- Query 1: Top 10 counties by low birth weight
SELECT
    c.county_name,
    chr.low_birth_weight_pct,
    sv.svi_overall,
    ph.diabetes_pct,
    ph.obesity_pct,
    ph.uninsured_places_pct
FROM counties c
JOIN county_health_rankings chr
    ON c.county_fips = chr.county_fips
JOIN social_vulnerability sv
    ON c.county_fips = sv.county_fips
JOIN places_health ph
    ON c.county_fips = ph.county_fips
ORDER BY chr.low_birth_weight_pct DESC
LIMIT 10;