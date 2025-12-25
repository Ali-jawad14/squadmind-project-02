import pandas as pd
import json
import streamlit as st
import os

@st.cache_data
def load_grandmaster_data():
    """
    Centralized data loader for SquadMind v2.0.
    Handles caching and critical NaN filling.
    """
    # 1. Load Grandmaster Stats
    if os.path.exists('active_players_grandmaster.csv'):
        players_df = pd.read_csv('active_players_grandmaster.csv')
    else:
        # Fallback for dev environment or if step 1 wasn't run
        return None, None, None
        
    # 2. Load Venue Intel
    venues_df = None
    if os.path.exists('venue_intelligence.csv'):
        venues_df = pd.read_csv('venue_intelligence.csv')
        
    # 3. Load Key Battles
    key_battles = {}
    if os.path.exists('key_battles.json'):
        with open('key_battles.json', 'r') as f:
            key_battles = json.load(f)
            
    # CRITICAL: Fill NaNs to prevent Streamlit crashes
    # Fill numeric columns with 0
    numeric_cols = players_df.select_dtypes(include=['number']).columns
    players_df[numeric_cols] = players_df[numeric_cols].fillna(0)
    
    # Fill string columns with "Unknown"
    object_cols = players_df.select_dtypes(include=['object']).columns
    players_df[object_cols] = players_df[object_cols].fillna("Unknown")
    
    return players_df, venues_df, key_battles
