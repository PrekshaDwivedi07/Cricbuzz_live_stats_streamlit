
-- Q1. Players who represent India
SELECT DISTINCT 
    player_name, playing_role, batting_style, bowling_style
FROM cricket_data
WHERE country = 'India';

-- Q2. Matches in last 30 days
SELECT DISTINCT 
    match_desc, team1, team2, venue_name, venue_city, match_date
FROM cricket_data
WHERE STR_TO_DATE(match_date, '%d-%m-%Y') >= (CURDATE() - INTERVAL 30 DAY)
ORDER BY STR_TO_DATE(match_date, '%d-%m-%Y') DESC;

-- Q3. Top 10 highest ODI run scorers
SELECT 
    player_name, 
    SUM(runs_scored) AS total_runs, 
    (SUM(runs_scored) / COUNT(DISTINCT match_id)) AS batting_average,
    SUM(centuries) AS total_centuries
FROM cricket_data
WHERE match_type = 'ODI'
GROUP BY player_id, player_name
ORDER BY total_runs DESC
LIMIT 10;

-- Q4. Venues with capacity > 50,000
SELECT DISTINCT 
    venue_name, venue_city, venue_country, venue_capacity
FROM cricket_data
WHERE venue_capacity > 50000
ORDER BY venue_capacity DESC;

-- Q5. Matches each team has won
SELECT 
    winner_team AS team_name,
    COUNT(*) AS total_wins
FROM cricket_data
WHERE winner_team IS NOT NULL
GROUP BY winner_team
ORDER BY total_wins DESC;

-- Q6. Count of players by role
SELECT 
    playing_role, 
    COUNT(DISTINCT player_id) AS player_count
FROM cricket_data
GROUP BY playing_role;

-- Q7. Highest individual batting score in each format
SELECT 
    match_type,
    player_name,
    MAX(runs_scored) AS highest_score
FROM cricket_data
GROUP BY match_type;

-- Q8. Cricket series that started in 2024
SELECT DISTINCT 
    series_name, host_country, match_type, MIN(STR_TO_DATE(match_date, '%d-%m-%Y')) AS start_date,
    COUNT(DISTINCT match_id) AS total_matches
FROM cricket_data
WHERE YEAR(STR_TO_DATE(match_date, '%d-%m-%Y')) = 2024
GROUP BY series_id, series_name, host_country, match_type;

-- Q9. All-rounders with >1000 runs & >50 wickets
SELECT 
    player_name, 
    country,
    SUM(runs_scored) AS total_runs,
    SUM(wickets_taken) AS total_wickets,
    match_type
FROM cricket_data
WHERE playing_role = 'All-rounder'
GROUP BY player_id, player_name, match_type
HAVING total_runs > 1000 AND total_wickets > 50;

-- Q10. Last 20 completed matches
SELECT DISTINCT 
    match_desc, team1, team2, winner_team, victory_margin, victory_type, venue_name, match_date
FROM cricket_data
WHERE winner_team IS NOT NULL
ORDER BY STR_TO_DATE(match_date, '%d-%m-%Y') DESC
LIMIT 20;

-- Q11. Compare players across formats (≥2 formats)
SELECT 
    player_name,
    SUM(CASE WHEN match_type='Test' THEN runs_scored ELSE 0 END) AS total_test_runs,
    SUM(CASE WHEN match_type='ODI' THEN runs_scored ELSE 0 END) AS total_odi_runs,
    SUM(CASE WHEN match_type='T20I' THEN runs_scored ELSE 0 END) AS total_t20_runs,
    (SUM(runs_scored) / COUNT(DISTINCT match_id)) AS overall_batting_avg
FROM cricket_data
GROUP BY player_id, player_name
HAVING 
    (total_test_runs > 0 AND total_odi_runs > 0)
    OR (total_test_runs > 0 AND total_t20_runs > 0)
    OR (total_odi_runs > 0 AND total_t20_runs > 0);

-- Q12. Team performance at home vs away
SELECT 
    team.country AS team_name,
    SUM(CASE WHEN venue_country = team.country AND winner_team = team.country THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN venue_country != team.country AND winner_team = team.country THEN 1 ELSE 0 END) AS away_wins
FROM cricket_data team
WHERE winner_team IS NOT NULL
GROUP BY team.country;

-- Q13. Batting partnerships ≥100 runs
SELECT 
    t1.player_name AS batsman1,
    t2.player_name AS batsman2,
    (t1.runs_scored + t2.runs_scored) AS partnership_runs,
    t1.match_id,
    t1.match_desc
FROM cricket_data t1
JOIN cricket_data t2 
  ON t1.match_id = t2.match_id
  AND t1.batting_position = t2.batting_position - 1
WHERE (t1.runs_scored + t2.runs_scored) >= 100;

-- Q14. Bowling performance at venues (≥3 matches, ≥4 overs/match)
SELECT 
    player_name,
    venue_name,
    AVG(economy_rate) AS avg_economy,
    SUM(wickets_taken) AS total_wickets,
    COUNT(DISTINCT match_id) AS matches_played
FROM cricket_data
WHERE overs_bowled >= 4
GROUP BY player_id, player_name, venue_name
HAVING matches_played >= 3;

-- Q15. Players in close matches (<50 runs OR <5 wickets)
SELECT 
    player_name,
    AVG(runs_scored) AS avg_runs,
    COUNT(DISTINCT match_id) AS close_matches_played,
    SUM(CASE WHEN winner_team = country THEN 1 ELSE 0 END) AS matches_won
FROM cricket_data
WHERE (victory_type='runs' AND victory_margin < 50)
   OR (victory_type='wickets' AND victory_margin < 5)
GROUP BY player_id, player_name;

-- Q16. Player batting performance by year (≥5 matches in year since 2020)
SELECT 
    player_name,
    YEAR(STR_TO_DATE(match_date, '%d-%m-%Y')) AS year,
    AVG(runs_scored) AS avg_runs_per_match,
    (SUM(runs_scored) / SUM(balls_faced)) * 100 AS avg_strike_rate,
    COUNT(DISTINCT match_id) AS matches_played
FROM cricket_data
WHERE YEAR(STR_TO_DATE(match_date, '%d-%m-%Y')) >= 2020
GROUP BY player_id, player_name, year
HAVING matches_played >= 5;

-- Q17. Toss advantage analysis
SELECT 
    toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN winner_team = toss_winner THEN 1 ELSE 0 END) AS toss_win_matches,
    (SUM(CASE WHEN winner_team = toss_winner THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS win_percentage
FROM cricket_data
WHERE toss_winner IS NOT NULL
GROUP BY toss_decision;

-- Q18. Most economical bowlers in ODIs & T20Is
SELECT 
    player_name,
    match_type,
    AVG(economy_rate) AS avg_economy,
    SUM(wickets_taken) AS total_wickets,
    COUNT(DISTINCT match_id) AS matches_played,
    (SUM(overs_bowled) / COUNT(DISTINCT match_id)) AS avg_overs_per_match
FROM cricket_data
WHERE match_type IN ('ODI', 'T20I')
GROUP BY player_id, player_name, match_type
HAVING matches_played >= 10 AND avg_overs_per_match >= 2
ORDER BY avg_economy ASC;

-- Q19. Consistent batsmen since 2022 (≥10 balls per innings)
SELECT 
    player_name,
    AVG(runs_scored) AS avg_runs,
    STDDEV(runs_scored) AS run_stddev,
    COUNT(*) AS innings_played
FROM cricket_data
WHERE YEAR(STR_TO_DATE(match_date, '%d-%m-%Y')) >= 2022
  AND balls_faced >= 10
GROUP BY player_id, player_name
HAVING innings_played >= 5
ORDER BY run_stddev ASC;

-- Q20. Matches played & batting averages by format (≥20 matches total)
SELECT 
    player_name,
    COUNT(DISTINCT CASE WHEN match_type='Test' THEN match_id END) AS test_matches,
    COUNT(DISTINCT CASE WHEN match_type='ODI' THEN match_id END) AS odi_matches,
    COUNT(DISTINCT CASE WHEN match_type='T20I' THEN match_id END) AS t20_matches,
    AVG(CASE WHEN match_type='Test' THEN runs_scored END) AS avg_test_runs,
    AVG(CASE WHEN match_type='ODI' THEN runs_scored END) AS avg_odi_runs,
    AVG(CASE WHEN match_type='T20I' THEN runs_scored END) AS avg_t20_runs
FROM cricket_data
GROUP BY player_id, player_name
HAVING (test_matches + odi_matches + t20_matches) >= 20;

-- Q21. Player performance ranking system
SELECT 
    player_name,
    match_type,
    (SUM(runs_scored) * 0.01 + AVG(runs_scored) * 0.5 + (SUM(runs_scored)/NULLIF(SUM(balls_faced),0)*100) * 0.3) AS batting_points,
    (SUM(wickets_taken) * 2 + (50 - AVG(CASE WHEN wickets_taken > 0 THEN runs_scored/wickets_taken END)) * 0.5 + ((6 - AVG(economy_rate)) * 2)) AS bowling_points,
    (SUM(catches) * 3 + SUM(stumpings) * 5) AS fielding_points,
    ((SUM(runs_scored) * 0.01 + AVG(runs_scored) * 0.5 + (SUM(runs_scored)/NULLIF(SUM(balls_faced),0)*100) * 0.3) +
     (SUM(wickets_taken) * 2 + (50 - AVG(CASE WHEN wickets_taken > 0 THEN runs_scored/wickets_taken END)) * 0.5 + ((6 - AVG(economy_rate)) * 2)) +
     (SUM(catches) * 3 + SUM(stumpings) * 5)) AS total_score
FROM cricket_data
GROUP BY player_id, player_name, match_type
ORDER BY total_score DESC;

-- Q22. Head-to-head team analysis (≥5 matches, last 3 years)
SELECT 
    team1, team2,
    COUNT(DISTINCT match_id) AS total_matches,
    SUM(CASE WHEN winner_team = team1 THEN 1 ELSE 0 END) AS team1_wins,
    SUM(CASE WHEN winner_team = team2 THEN 1 ELSE 0 END) AS team2_wins,
    AVG(CASE WHEN winner_team = team1 THEN victory_margin END) AS avg_margin_team1,
    AVG(CASE WHEN winner_team = team2 THEN victory_margin END) AS avg_margin_team2,
    (SUM(CASE WHEN winner_team = team1 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS team1_win_pct,
    (SUM(CASE WHEN winner_team = team2 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS team2_win_pct
FROM cricket_data
WHERE STR_TO_DATE(match_date, '%d-%m-%Y') >= (CURDATE() - INTERVAL 3 YEAR)
GROUP BY team1, team2
HAVING total_matches >= 5;

-- Q23. Recent player form (last 10 matches)
WITH recent_matches AS (
    SELECT player_id, player_name, match_date, runs_scored,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY STR_TO_DATE(match_date, '%d-%m-%Y') DESC) AS rn
    FROM cricket_data
)
SELECT 
    player_name,
    AVG(CASE WHEN rn <= 5 THEN runs_scored END) AS avg_last5,
    AVG(CASE WHEN rn <= 10 THEN runs_scored END) AS avg_last10,
    SUM(CASE WHEN rn <= 10 AND runs_scored >= 50 THEN 1 ELSE 0 END) AS fifties_last10,
    STDDEV(CASE WHEN rn <= 10 THEN runs_scored END) AS consistency_score,
    CASE 
        WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 50 THEN 'Excellent Form'
        WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 35 THEN 'Good Form'
        WHEN AVG(CASE WHEN rn <= 5 THEN runs_scored END) >= 20 THEN 'Average Form'
        ELSE 'Poor Form'
    END AS form_status
FROM recent_matches
WHERE rn <= 10
GROUP BY player_id, player_name;

-- Q24. Best batting partnerships (≥5 partnerships)
SELECT 
    t1.player_name AS batsman1,
    t2.player_name AS batsman2,
    AVG(t1.runs_scored + t2.runs_scored) AS avg_partnership,
    SUM(CASE WHEN (t1.runs_scored + t2.runs_scored) >= 50 THEN 1 ELSE 0 END) AS fifty_plus_partnerships,
    MAX(t1.runs_scored + t2.runs_scored) AS highest_partnership,
    COUNT(*) AS total_partnerships,
    (SUM(CASE WHEN (t1.runs_scored + t2.runs_scored) >= 50 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS success_rate
FROM cricket_data t1
JOIN cricket_data t2 
  ON t1.match_id = t2.match_id
  AND t1.batting_position = t2.batting_position - 1
GROUP BY t1.player_name, t2.player_name
HAVING total_partnerships >= 5
ORDER BY success_rate DESC;

-- Q25. Player performance evolution (quarterly)
SELECT 
    player_name,
    CONCAT(YEAR(STR_TO_DATE(match_date, '%d-%m-%Y')), '-Q', QUARTER(STR_TO_DATE(match_date, '%d-%m-%Y'))) AS quarter,
    AVG(runs_scored) AS avg_runs,
    (SUM(runs_scored)/SUM(balls_faced))*100 AS avg_strike_rate
FROM cricket_data
GROUP BY player_id, player_name, quarter
ORDER BY player_name, quarter;
