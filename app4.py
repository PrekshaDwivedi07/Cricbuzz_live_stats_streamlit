import streamlit as st
import requests
import pandasql as ps
from pandasql import sqldf
import pandas as pd
import plotly.express as px
import os
from functools import lru_cache
import sqlite3

# ---------------------------
# CONFIG
# ---------------------------
API_BASE = "https://cricbuzz-cricket.p.rapidapi.com"
API_KEY = "b13690af39msh6d2ef05045317a0p1ac52djsn44df31c93c07"

HEADERS = {
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com",
    "x-rapidapi-key": API_KEY
}

# ---------------------------
# API HELPERS
# ---------------------------
def get_api(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None


@lru_cache(maxsize=10)
def fetch_live_matches():
    return get_api(f"{API_BASE}/matches/v1/live")


@lru_cache(maxsize=10)
def fetch_scorecard(match_id):
    return get_api(f"{API_BASE}/mcenter/v1/{match_id}/scard")


@lru_cache(maxsize=10)
@st.cache_data
def fetch_player_stats(player_name: str):
    try:
        # Search player by name
        search_url = f"{API_BASE}/stats/v1/player/search?plrN={player_name}"
        response = requests.get(search_url, headers=HEADERS)
        response.raise_for_status()
        search_data = response.json()

        if "player" not in search_data or not search_data["player"]:
            return None

        player_id = search_data["player"][0].get("id")

        # Fetch player stats by ID
        url = f"{API_BASE}/stats/v1/player/{player_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None


# ---------------------------
# LOAD DATA
# ---------------------------

@st.cache_data
def load_data():
    if not os.path.exists("cricket_data.csv"):
        st.error("⚠️ 'cricket_data.csv' not found.")
        st.stop()
    df = pd.read_csv("cricket_data.csv")
    return df

@st.cache_resource
def get_connection(df: pd.DataFrame):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("cricket_data", conn, index=False, if_exists="replace")
    return conn

# Load once
df = load_data()
conn = get_connection(df)


# ---------------------------
# PAGES
# ---------------------------
def page_home():
    st.header("🏏 Live / Recent Matches")

    matches = fetch_live_matches()
    match_options = []

    if matches and "typeMatches" in matches:
        for match_type in matches["typeMatches"]:
            for series in match_type.get("seriesMatches", []):
                series_name = series.get("seriesAdWrapper", {}).get("seriesName", "")
                matches_list = series.get("seriesAdWrapper", {}).get("matches", [])
                
                for m in matches_list:
                    match_info = m.get("matchInfo", {})
                    team1 = match_info.get("team1", {}).get("teamName", "")
                    team2 = match_info.get("team2", {}).get("teamName", "")
                    status = match_info.get("status", "")
                    match_id = match_info.get("matchId")

                    match_options.append({
                        "label": f"{series_name} | {team1} vs {team2} — {status}",
                        "id": match_id
                    })

    if not match_options:
        st.warning("⚠️ No match data available — check API.")
        return

    selected_match = st.selectbox(
        "Select a Match",
        match_options,
        format_func=lambda x: x["label"]
    )

    if selected_match:
        match_id = selected_match["id"]
        st.subheader(f"📊 Scorecard for Match ID: {match_id}")

        score_data = fetch_scorecard(match_id)

        if score_data and "scorecard" in score_data and score_data["scorecard"]:
            for inning in score_data["scorecard"]:
                st.markdown(f"### 🏏 {inning.get('batTeamDetails', {}).get('batTeamName', '')}")

                batting = inning.get("batsman", [])
                if batting:
                    bat_df = pd.DataFrame([{
                        "Batsman": b.get("batName", ""),
                        "Runs": b.get("runs", 0),
                        "Balls": b.get("balls", 0),
                        "4s": b.get("fours", 0),
                        "6s": b.get("sixes", 0),
                        "SR": b.get("strikeRate", 0)
                    } for b in batting])
                    st.dataframe(bat_df, use_container_width=True)

                bowling = inning.get("bowlers", [])
                if bowling:
                    bowl_df = pd.DataFrame([{
                        "Bowler": bw.get("bowlName", ""),
                        "Overs": bw.get("overs", 0),
                        "Runs": bw.get("runs", 0),
                        "Wickets": bw.get("wickets", 0),
                        "Econ": bw.get("economy", 0)
                    } for bw in bowling])
                    st.dataframe(bowl_df, use_container_width=True)
        else:
            st.info("⚠️ No scorecard data available yet. Match may not have started.")

        if st.button("🔄 Refresh API data"):
            fetch_live_matches.cache_clear()
            fetch_scorecard.cache_clear()
            st.rerun()


def page_players():
    st.header("⭐ Player Stats")
    player_name = st.text_input("Enter Player Name (e.g. Virat Kohli)")

    if player_name:
        data = fetch_player_stats(player_name)
        if data:
            # ✅ Use the profile card display instead of raw JSON
            show_player_profile(data)
        else:
            st.error("No data found for this player.")


def show_player_profile(player_data: dict):
    """Display a cricket player's profile card in Streamlit"""

    # Title
    st.title("🏏 Player Profile")

    # Layout with 2 columns
    col1, col2 = st.columns([1, 2])

    with col1:
        if "image" in player_data and player_data["image"]:
            st.image(player_data["image"], width=200, caption=player_data.get("name", "Unknown Player"))
        else:
            st.write("📸 No Image Available")

    with col2:
        st.subheader(player_data.get("name", "Unknown Player"))
        st.write(f"**Nickname:** {player_data.get('nickName', 'N/A')}")
        st.write(f"**Date of Birth:** {player_data.get('DoB', 'N/A')}")
        st.write(f"**Birth Place:** {player_data.get('birthPlace', 'N/A')}")
        st.write(f"**International Team:** {player_data.get('intlTeam', 'N/A')}")
        st.write(f"**Role:** {player_data.get('role', 'N/A')}")
        st.write(f"**Batting Style:** {player_data.get('bat', 'N/A')}")
        st.write(f"**Bowling Style:** {player_data.get('bowl', 'N/A')}")

    # Teams
    if "teams" in player_data:
        st.markdown("### 🏟️ Teams Played For")
        st.info(player_data["teams"])

    # Rankings
    if "ranking" in player_data:
        st.markdown("### 📊 Rankings")
        st.write(f"**Batting Rank:** {player_data['ranking'].get('bat', 'N/A')}")
        st.write(f"**Bowling Rank:** {player_data['ranking'].get('bowl', 'N/A')}")
        st.write(f"**All-rounder Rank:** {player_data['ranking'].get('all', 'N/A')}")

    # Profile URL
    if "profile_url" in player_data:
        st.markdown(f"[🔗 View Full Profile]({player_data['profile_url']})")


def page_dashboard():
    st.header("📊 Cricket Data Dashboard")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", df["player_id"].nunique())
    with col2:
        st.metric("Total Matches", df["match_id"].nunique())
    with col3:
        st.metric("Unique Venues", df["venue_name"].nunique())
    with col4:
        st.metric("Teams", pd.concat([df["team1"], df["team2"]]).nunique())

    # Tabs
    tab1, tab2 = st.tabs(["📊 SQL Queries", "🗃️ Data Explorer"])

    query_map = {
    "Q1. Players from India": """
        SELECT DISTINCT player_name, playing_role, batting_style, bowling_style, country
        FROM cricket_data
        WHERE country = 'India';
    """,

    "Q2. Recent Matches (last 30 days)": """
        SELECT DISTINCT match_desc, team1, team2, venue_name AS venue, venue_city AS city, match_date
        FROM cricket_data
        WHERE DATE(match_date) >= DATE('now', '-30 days')
        ORDER BY match_date DESC;
    """,

    "Q3. Top 10 ODI Run Scorers": """
        SELECT player_name, SUM(runs_scored) AS total_runs, 
               ROUND(SUM(runs_scored) * 1.0 / COUNT(DISTINCT match_id), 2) AS batting_average,
               COUNT(DISTINCT match_id) AS matches
        FROM cricket_data
        WHERE match_type = 'ODI'
        GROUP BY player_name
        ORDER BY total_runs DESC
        LIMIT 10;
    """,

    "Q4. Top 10 ODI Wicket Takers": """
        SELECT player_name, SUM(wickets_taken) AS total_wickets, 
               ROUND(SUM(wickets_taken) * 1.0 / COUNT(DISTINCT match_id), 2) AS bowling_average,
               COUNT(DISTINCT match_id) AS matches
        FROM cricket_data
        WHERE match_type = 'ODI'
        GROUP BY player_name
        ORDER BY total_wickets DESC
        LIMIT 10;
    """,

    "Q5. IPL Teams and Grounds": """
        SELECT DISTINCT team1 AS team_name, venue_name AS home_ground
        FROM cricket_data
        WHERE tournament LIKE 'IPL%';
    """,

    "Q6. Matches at Wankhede Stadium": """
        SELECT DISTINCT match_desc, team1, team2, match_date
        FROM cricket_data
        WHERE venue_name = 'Wankhede Stadium';
    """,

    "Q7. Players with SR > 150 in T20": """
        SELECT DISTINCT player_name, strike_rate, COUNT(DISTINCT match_id) AS matches
        FROM cricket_data
        WHERE match_type = 'T20' AND strike_rate > 150
        GROUP BY player_name, strike_rate;
    """,

    "Q8. Centuries in World Cup 2019": """
        SELECT DISTINCT player_name, runs_scored AS runs, match_desc
        FROM cricket_data
        WHERE tournament = 'World Cup 2019' AND runs_scored >= 100;
    """,

    "Q9. Virat Kohli Avg Runs": """
        SELECT player_name,
               ROUND(SUM(runs_scored) * 1.0 / COUNT(DISTINCT match_id), 2) AS avg_runs
        FROM cricket_data
        WHERE player_name = 'Virat Kohli'
        GROUP BY player_name;
    """,

    "Q10. All-rounders List": """
        SELECT DISTINCT player_name, country, batting_style, bowling_style
        FROM cricket_data
        WHERE playing_role = 'All-rounder';
    """,

    "Q11. India Wins in 2023": """
        SELECT DISTINCT match_desc, team1, team2, match_date, winner_team
        FROM cricket_data
        WHERE (team1 = 'India' OR team2 = 'India')
          AND winner_team = 'India'
          AND strftime('%Y', match_date) = '2023';
    """,

    "Q12. Most Sixes in IPL History": """
        SELECT player_name, SUM(sixes) AS total_sixes
        FROM cricket_data
        WHERE tournament LIKE 'IPL%'
        GROUP BY player_name
        ORDER BY total_sixes DESC
        LIMIT 1;
    """,

    "Q13. Best Economy in T20": """
        SELECT DISTINCT player_name, economy_rate, COUNT(DISTINCT match_id) AS matches
        FROM cricket_data
        WHERE match_type = 'T20'
        GROUP BY player_name, economy_rate
        ORDER BY economy_rate ASC
        LIMIT 5;
    """,

    "Q14. Highest ODI Team Total": """
        SELECT team1 AS team_name, MAX(team1_runs + team2_runs) AS highest_total
        FROM cricket_data
        WHERE match_type = 'ODI';
    """,

    "Q15. Most Test Catches": """
        SELECT player_name, SUM(catches) AS total_catches
        FROM cricket_data
        WHERE match_type = 'Test'
        GROUP BY player_name
        ORDER BY total_catches DESC
        LIMIT 1;
    """,

    "Q16. Players born after 2000": """
        SELECT DISTINCT player_name, country, dob
        FROM cricket_data
        WHERE dob > '2000-01-01';
    """,

    "Q17. Sachin Tendulkar WC Runs": """
        SELECT player_name, SUM(runs_scored) AS total_wc_runs
        FROM cricket_data
        WHERE player_name = 'Sachin Tendulkar' AND tournament LIKE 'World Cup%'
        GROUP BY player_name;
    """,

    "Q18. Matches at Eden Gardens by India": """
        SELECT DISTINCT match_desc, team1, team2, match_date
        FROM cricket_data
        WHERE venue_name = 'Eden Gardens'
          AND (team1 = 'India' OR team2 = 'India');
    """,

    "Q19. Top 5 Partnerships in ODI": """
        SELECT batsman1, batsman2, SUM(runs_scored) AS runs, match_desc
        FROM cricket_data
        WHERE match_type = 'ODI'
        GROUP BY batsman1, batsman2, match_desc
        ORDER BY runs DESC
        LIMIT 5;
    """,

    "Q20. Hat-tricks Bowled": """
        SELECT DISTINCT player_name, match_desc, wickets_taken
        FROM cricket_data
        WHERE hat_trick = 1;
    """,

    "Q21. IPL Teams with >2 Titles": """
        SELECT winner_team AS team_name, COUNT(*) AS trophies
        FROM cricket_data
        WHERE tournament LIKE 'IPL%'
        GROUP BY winner_team
        HAVING trophies > 2;
    """,

    "Q22. Most MoM Awards in ODI": """
        SELECT player_name, COUNT(*) AS mom_awards
        FROM cricket_data
        WHERE match_type = 'ODI' AND man_of_the_match = 1
        GROUP BY player_name
        ORDER BY mom_awards DESC
        LIMIT 1;
    """,

    "Q23. Matches in IPL 2022": """
        SELECT COUNT(DISTINCT match_id) AS total_matches
        FROM cricket_data
        WHERE tournament = 'IPL 2022';
    """,

    "Q24. Test Players Avg Batting > 50": """
        SELECT player_name, batting_average, COUNT(DISTINCT match_id) AS matches
        FROM cricket_data
        WHERE match_type = 'Test' AND batting_average > 50
        GROUP BY player_name, batting_average
        ORDER BY batting_average DESC;
    """,

    "Q25. Venues Hosting >10 Matches": """
        SELECT venue_name AS venue, COUNT(DISTINCT match_id) AS total_matches
        FROM cricket_data
        GROUP BY venue_name
        HAVING total_matches > 10
        ORDER BY total_matches DESC;
    """
}


    with tab1:
        st.subheader("🔍 SQL Query Interface")
        selected = st.selectbox("Select a Query", list(query_map.keys()))
        if selected:
            query = query_map[selected]
            try:
                df_result = pd.read_sql_query(query, conn)
                st.success(f"✅ Showing results for: {selected}")
                st.dataframe(df_result, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    with tab2:
        st.subheader("🧾 Full Dataset")
        st.dataframe(df, use_container_width=True)


# ---------------------------
# MAIN
# ---------------------------
st.set_page_config(page_title="Cricket Dashboard", layout="wide")

st.sidebar.title("📂 Navigation")
PAGES = {
    "Home (Live Matches)": page_home,
    "Player Stats": page_players,
    "Data Dashboard": page_dashboard
}

choice = st.sidebar.radio("Go to:", list(PAGES.keys()))
PAGES[choice]()
