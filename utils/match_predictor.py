import pandas as pd
from utils.grandmaster_optimizer import optimize_squad_v3

def get_team_strength(team_name, opponent, df, fmt, context):
    squad, status, strength = optimize_squad_v3(df, team_name, opponent, "Flat", fmt, context)
    return strength, squad

def predict_match_outcome(team_A, team_B, df, match_format="T20", context="International"):
    """
    Elo-based Win Probability (Context Aware).
    """
    str_A, squad_A = get_team_strength(team_A, team_B, df, match_format, context)
    str_B, squad_B = get_team_strength(team_B, team_A, df, match_format, context)
    
    if str_A == 0 or str_B == 0: return None
    
    diff = str_B - str_A
    prob_A = 1 / (1 + 10 ** (diff / 400))
    
    return {
        'team_A': team_A, 'team_B': team_B,
        'strength_A': str_A, 'strength_B': str_B,
        'prob_A': prob_A * 100,
        'squad_A': squad_A,
        'squad_B': squad_B
    }

def get_key_battles(team_A, team_B, battles_json, squad_A, squad_B):
    if not battles_json: return []
    
    battles = []
    
    # Top 3 A (Bat) vs Top 3 B (Bowl)
    key_bats_A = squad_A.iloc[:5]['Player'].tolist()
    key_bowls_B = squad_B[squad_B['Role'].isin(['Bowler', 'All-Rounder'])].head(5)['Player'].tolist()
    
    for bat in key_bats_A:
        if bat in battles_json:
            opp_dict = battles_json[bat]
            for bowl in key_bowls_B:
                if bowl in opp_dict:
                    count = opp_dict[bowl]
                    if count >= 1:
                        battles.append(f"<b>{bat}</b> vs <b>{bowl}</b><br><span style='color:red'>{count} Dismissals</span>")
                        
    # Top 3 B (Bat) vs Top 3 A (Bowl)
    key_bats_B = squad_B.iloc[:5]['Player'].tolist()
    key_bowls_A = squad_A[squad_A['Role'].isin(['Bowler', 'All-Rounder'])].head(5)['Player'].tolist()
    
    for bat in key_bats_B:
        if bat in battles_json:
            opp_dict = battles_json[bat]
            for bowl in key_bowls_A:
                if bowl in opp_dict:
                    count = opp_dict[bowl]
                    if count >= 1:
                        battles.append(f"<b>{bat}</b> vs <b>{bowl}</b><br><span style='color:red'>{count} Dismissals</span>")
                        
    return battles[:5]
