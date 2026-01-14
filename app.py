import streamlit as st
import requests
import json
import pandas as pd
import statistics

# --- KONFIGURÁCIA ---
API_KEY = '3e42c726ab364fb9eeede03b0017964c'  # <--- VLOŽ SVOJ KĽÚČ !!!
SPORT_KEY = 'soccer_epl'           # Premier League
REGIONS = 'eu'
MARKETS = 'totals'
ODDS_FORMAT = 'decimal'

# --- DESIGN CODEGREEN ---
st.set_page_config(page_title="CodeGreen AI", page_icon="🟢", layout="wide")

# Vlastné CSS pre "Hacker/Terminal" vzhľad
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
    }
    h1, h2, h3 {
        color: #00ff41 !important;
        font-family: 'Courier New', Courier, monospace;
    }
    .stButton>button {
        background-color: #00ff41;
        color: black;
        border: none;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #00ff41;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PAMÄŤ (Caching) ---
# Na Streamlit Cloud používame @st.cache_data namiesto ukladania do súboru
@st.cache_data(ttl=3600) # Dáta sa uložia na 1 hodinu (šetrí API)
def fetch_odds():
    try:
        response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds',
            params={
                'api_key': API_KEY,
                'regions': REGIONS,
                'markets': MARKETS,
                'oddsFormat': ODDS_FORMAT,
            }
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def analyze_value(matches):
    analyzed_data = []
    if not matches: return []
    
    for match in matches:
        home = match['home_team']
        away = match['away_team']
        
        # Hľadáme Over 2.5
        best_odd = 0.0
        best_bookie = ""
        all_odds = []
        
        for bookmaker in match['bookmakers']:
            for market in bookmaker['markets']:
                if market['key'] == 'totals':
                    for outcome in market['outcomes']:
                        if outcome['point'] == 2.5 and outcome['name'] == 'Over':
                            odd = outcome['price']
                            all_odds.append(odd)
                            if odd > best_odd:
                                best_odd = odd
                                best_bookie = bookmaker['title']

        if all_odds:
            avg_odd = statistics.mean(all_odds)
            value_score = (best_odd - avg_odd) / avg_odd * 100
            
            # CodeGreen Logika
            status = "HOLD"
            if value_score > 5: status = "🟢 BUY (STRONG)"
            elif value_score > 2: status = "🟢 BUY"
            
            analyzed_data.append({
                "Zápas": f"{home} vs {away}",
                "Kurz": best_odd,
                "Bookmaker": best_bookie,
                "Signál": status,
                "Hodnota": f"+{value_score:.1f}%"
            })
            
    return analyzed_data

# --- HLAVNÉ ROZHRANIE ---
st.title("🟢 CODEGREEN_AI_V1.0")
st.markdown("`INITIALIZING SYSTEM... SCANNING MARKETS...`")

# Načítanie dát
data = fetch_odds()

if data:
    analyzed = analyze_value(data)
    df = pd.DataFrame(analyzed)
    
    # Metriky hore
    col1, col2, col3 = st.columns(3)
    col1.metric("SKENOVANÉ ZÁPASY", len(data))
    col2.metric("NÁJDENÉ PRÍLEŽITOSTI", len(df[df['Signál'].str.contains("BUY")]))
    col3.metric("TRHOVÁ NÁLADA", "BULLISH")
    
    st.markdown("---")
    
    # Filter len na dobré signály
    show_all = st.checkbox("ZOBRAZIŤ VŠETKY (vrátane nízkej hodnoty)", value=False)
    
    if not show_all:
        df_display = df[df['Signál'].str.contains("BUY")]
    else:
        df_display = df
        
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    if st.button("🔄 REFRESH DATA (SYSTEM)"):
        st.cache_data.clear()
        st.rerun()

else:
    st.error("❌ SYSTEM ERROR: UNABLE TO CONNECT TO ODDS API. CHECK API KEY.")
