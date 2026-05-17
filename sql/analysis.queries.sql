-- Query 1: Top 10 counties by final priority score
SELECT
    county_name,
    maternal_infant_outcome_score,
    chronic_disease_score,
    social_vulnerability_score,
    access_resource_barrier_score,
    final_priority_score,
    priority_level
FROM priority_scores
ORDER BY final_priority_score DESC
LIMIT 10;