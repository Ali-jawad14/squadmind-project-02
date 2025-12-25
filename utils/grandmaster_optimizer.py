import pulp
import pandas as pd
import difflib

# Known Keepers
KEEPERS = ['AJ Healy', 'AE Jones', 'Richa Ghosh', 'Muneeba Ali', 'T Chetty', 'Yastika Bhatia', 'Alyssa Healy', 'Amy Jones', 'B Mooney', 'SJ McGlashan', 'TC Beaumont', 'N de Klerk']

def is_keeper(name):
    # Fuzzy match
    matches = difflib.get_close_matches(name, KEEPERS, n=1, cutoff=0.7)
    return 1 if matches else 0

def optimize_squad_v3(df, team_name, opponent, venue_pitch="Flat", match_format="T20", context="International"):
    """
    Expert ILP Optimizer (v3.0).
    Features: Format Awareness, Robust Fallback, Competition Context.
    """
    # 0. Filter Team
    pool = df[df['Country'] == team_name].copy()
    if pool.empty:
        return pd.DataFrame(), "No Data for Team", 0
        
    # 1. Format Awareness
    fmt = match_format
    if fmt not in ['T20', 'ODI', 'Test']: fmt = 'T20'
    
    bat_col = f'Bat_Avg_{fmt}'
    bowl_col = f'Bowl_Wkts_{fmt}'
    
    if bat_col not in pool.columns: bat_col = 'Bat_Avg_Overall'
    if bowl_col not in pool.columns: bowl_col = 'Bowl_Wkts_Overall'
    
    # 2. Scoring Algorithm
    squad_pool = []
    
    max_bat = pool[bat_col].max() if not pool.empty else 1
    max_bowl = pool[bowl_col].max() if not pool.empty else 1
    if max_bat == 0: max_bat = 1
    if max_bowl == 0: max_bowl = 1
    
    for _, row in pool.iterrows():
        name = row['Player']
        
        # Raw Stats
        val_bat = row.get(bat_col, 0)
        val_bowl = row.get(bowl_col, 0)
        
        # --- CONTEXT LOGIC ---
        if context == "Domestic League":
            # Weighted Short-Form Form
            league_avg = row.get('Avg_vs_League', 0)
            val_bat = (val_bat * 0.4) + (league_avg * 0.6)
        
        # Normalized Scores (0-100)
        s_bat = (val_bat / max_bat) * 100
        s_bowl = (val_bowl / max_bowl) * 100
        
        # Role Logic
        role = "Batter"
        if val_bowl > 5 or (val_bowl > 0 and val_bowl > max_bowl*0.2):
            role = "Bowler"
            if val_bat > 15: role = "All-Rounder"
            
        # Match Score
        score = max(s_bat, s_bowl)
        if role == "All-Rounder":
            score = (s_bat * 0.6) + (s_bowl * 0.6)
            
        # Modifiers
        if venue_pitch == "Green" and role in ["Bowler", "All-Rounder"]: score *= 1.25
        if venue_pitch == "Dusty" and role in ["Bowler", "All-Rounder"]: score *= 1.30
        
        opp_col = f'Avg_vs_{opponent}'
        if opp_col in row and row[opp_col] > 30:
            score *= 1.15
            
        squad_pool.append({
            'Player': name,
            'Score': score,
            'Role': role,
            'Is_WK': is_keeper(name),
            'Display_Bat': val_bat,
            'Display_Bowl': val_bowl
        })
        
    # 3. Optimization
    final_squad = []
    status_msg = "Optimal"
    
    try:
        prob = pulp.LpProblem("Squad_Selection", pulp.LpMaximize)
        x = pulp.LpVariable.dicts("x", [p['Player'] for p in squad_pool], cat=pulp.LpBinary)
        
        prob += pulp.lpSum([p['Score'] * x[p['Player']] for p in squad_pool])
        
        prob += pulp.lpSum([x[p['Player']] for p in squad_pool]) == 11
        prob += pulp.lpSum([x[p['Player']] for p in squad_pool if p['Role'] == 'Bowler']) >= 3
        prob += pulp.lpSum([x[p['Player']] for p in squad_pool if p['Is_WK'] == 1]) >= 1
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            for p in squad_pool:
                if x[p['Player']].varValue == 1:
                    final_squad.append(p)
        else:
            raise ValueError("Infeasible")
            
    except:
        status_msg = "Suboptimal (Fallback)"
        squad_pool.sort(key=lambda x: x['Score'], reverse=True)
        final_squad = squad_pool[:11]
        
    res_df = pd.DataFrame(final_squad).sort_values(by='Score', ascending=False)
    total_strength = res_df['Score'].sum()
    
    return res_df, status_msg, total_strength
