import streamlit as st
import pandas as pd
import time

# --- MODULAR IMPORTS ---
from utils import data_manager, live_intelligence, grandmaster_optimizer, match_predictor

# --- CONSTANTS ---
INTL_TEAMS = [
    "Australia", "England", "India", "New Zealand", "South Africa", 
    "Pakistan", "West Indies", "Sri Lanka", "Bangladesh", "Ireland"
]

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SquadMind v2.0",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL UI CSS ---
st.markdown("""
<style>
    /* Force Light Theme */
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }
    
    /* SIDEBAR NAVIGATION PILLS */
    /* Hide specific radio circles for the Navigation widget */
    div[class*="stRadio"] > label > div:first-child {
        display: none !important;
    }
    /* Target the radio options */
    div[role="radiogroup"] > label {
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        transition: all 0.3s ease;
        cursor: pointer;
        display: flex; /* Better alignment */
        align-items: center;
    }
    /* Remove dot */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* HOVER State */
    div[role="radiogroup"] > label:hover {
        background-color: #f8f9fa;
        border-color: #007bff;
        transform: translateX(5px);
    }
    
    /* ACTIVE State */
    div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #007bff !important;
        border-color: #007bff !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,123,255,0.2);
    }
    div[role="radiogroup"] > label[data-checked="true"] * {
        color: white !important;
    }

    /* GENERAL METRICS */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: black;
    }
    
    /* Typography */
    h1, h2, h3 { color: #1f1f1f !important; }
    
    /* Buttons */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border: none;
        width: 100%;
        height: 3em;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #0056b3; }
</style>
""", unsafe_allow_html=True)

def get_filtered_teams(df, context):
    """
    Filters team list based on context (International vs League).
    """
    all_teams = sorted(df['Country'].unique().tolist())
    
    if context == "International":
        return [t for t in all_teams if t in INTL_TEAMS]
    elif context == "Domestic League":
        # Any team NOT in the international list
        return [t for t in all_teams if t not in INTL_TEAMS]
    
    return all_teams

def main():
    # 1. LOAD DATA
    players_df, venues_df, key_battles = data_manager.load_grandmaster_data()
    
    if players_df is None:
        st.error("Data missing. Run `python build_grandmaster_data.py`")
        st.stop()
        
    # 2. SIDEBAR
    with st.sidebar:
        st.title("🏏 SquadMind v2.2")
        st.caption("Grandmaster Edition")
        
        # NAVIGATION (Styled as Pills via CSS)
        page = st.radio("Navigation", [
            "Squad Grandmaster", 
            "Match Predictor", 
            "Venue Intelligence", 
            "ML Lab"
        ])
        
        st.divider()
        st.header("⚙️ Settings")
        
        match_format = st.selectbox("Format", ["T20", "ODI", "Test"])
        context = st.radio("Context", ["International", "Domestic League"], horizontal=True) # Horizontal for toggle effect
        
        st.info(f"Mode: **{match_format}** ({context})")

    # 3. ROUTING
    if page == "Squad Grandmaster":
        render_grandmaster_page(players_df, venues_df, match_format, context)
    elif page == "Match Predictor":
        render_predictor_page(players_df, key_battles, match_format, context)
    elif page == "Venue Intelligence":
        render_venue_page(venues_df)
    elif page == "ML Lab":
        render_ml_page(players_df)


def render_grandmaster_page(df, venues_df, fmt, context):
    st.title(f"🚀 Squad Grandmaster")
    st.caption(f"Optimizing for **{fmt}** in **{context}** environment")
    
    c1, c2, c3 = st.columns(3)
    
    # FILTER TEAMS
    teams = get_filtered_teams(df, context)
    if not teams:
        st.error(f"No teams found for {context} context.")
        return

    my_team = c1.selectbox("My Team", teams)
    opp_list = [t for t in teams if t != my_team]
    opponent = c2.selectbox("Opponent", opp_list if opp_list else teams)
    
    # Venue
    v_list = venues_df['Venue'].unique() if venues_df is not None else ["London"]
    venue = c3.selectbox("Venue", v_list)
    
    pitch_type = live_intelligence.get_venue_context(venue, venues_df)
    
    if st.button("RUN OPTIMIZATION"):
        with st.spinner("Calculating..."):
            w_desc, w_temp, _ = live_intelligence.get_live_weather(venue)
            
            res_df, status, strength = grandmaster_optimizer.optimize_squad_v3(
                df, my_team, opponent, pitch_type, fmt, context
            )
            
            if not res_df.empty:
                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Weather", f"{w_temp}°C", w_desc)
                m2.metric("Pitch", pitch_type)
                m3.metric("Strength", f"{strength:.0f}")
                m4.metric("Status", status)
                
                if status != "Optimal": st.warning("⚠️ Constraints Relaxed")
                
                st.dataframe(
                    res_df[['Player', 'Role', 'Score', 'Is_WK', f'Display_Bat', f'Display_Bowl']],
                    column_config={
                        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=120, format="%.0f"),
                        "Is_WK": st.column_config.CheckboxColumn("WK?"),
                        "Display_Bat": st.column_config.NumberColumn(f"Bat Avg", format="%.1f"),
                        "Display_Bowl": st.column_config.NumberColumn(f"Wkts", format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.error("Optimization Failed")

def render_predictor_page(df, key_battles, fmt, context):
    st.title(f"🔮 Match Predictor")
    
    teams = get_filtered_teams(df, context)
    if not teams:
        st.warning("No teams available")
        return
        
    c1, c2 = st.columns(2)
    idx2 = 1 if len(teams) > 1 else 0
    t1 = c1.selectbox("Home Team", teams, index=0)
    t2 = c1.selectbox("Away Team", teams, index=idx2)
    
    if st.button("PREDICT MATCH"):
        res = match_predictor.predict_match_outcome(t1, t2, df, fmt, context)
        
        if res:
            p = res['prob_A']
            win = t1 if p > 50 else t2
            pct = p if p > 50 else (100 - p)
            
            st.success(f"### {win} Wins ({pct:.1f}%)")
            st.bar_chart({t1: res['strength_A'], t2: res['strength_B']})
            
            st.subheader("Key Battles")
            battles = match_predictor.get_key_battles(t1, t2, key_battles, res['squad_A'], res['squad_B'])
            
            if battles:
                cols = st.columns(3)
                for i, b in enumerate(battles):
                    with cols[i%3]:
                        st.markdown(f'<div class="metric-card">{b}</div>', unsafe_allow_html=True)
            else:
                st.info("No significant matchups found")

def render_venue_page(df):
    st.title("Venue Intel")
    if df is not None: st.dataframe(df, use_container_width=True)

def render_ml_page(df):
    st.title("Player Database")
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()