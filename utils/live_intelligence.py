import requests
import pandas as pd

API_KEY = "c436f68a17a8fb062c860be6e7920e2a" # Free tier key

def get_live_weather(venue_name):
    """
    Robust weather fetcher.
    Splits 'The Sevens, Dubai' -> 'Dubai' for better API hits.
    Returns: (Description, Temp_Celsius, Status_Msg)
    """
    clean_city = venue_name
    
    # Logic: Use the LAST part of a comma-separated string
    if "," in venue_name:
        parts = venue_name.split(",")
        clean_city = parts[-1].strip()
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={clean_city}&appid={API_KEY}"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            weather_desc = data['weather'][0]['main']
            temp_k = data['main']['temp']
            temp_c = temp_k - 273.15
            return weather_desc, round(temp_c, 1), "Live"
        else:
            return "Clear", 25.0, "API Error"
            
    except Exception as e:
        return "Clear", 25.0, "Network Error"

def get_venue_context(venue_name, venues_df):
    """
    Returns pitch condition (Green/Dusty/Flat) from venue DB.
    """
    if venues_df is None: return "Flat"
    
    row = venues_df[venues_df['Venue'] == venue_name]
    if not row.empty:
        return row.iloc[0]['Typical_Pitch_Condition']
    return "Flat" # Default conservative
