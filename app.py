import streamlit as st
import requests
import json
import pandas as pd
import statistics

# --- 1. KONFIGURÁCIA (HESLÁ) ---
ODDS_API_KEY = '3e42c726ab364fb9eeede03b0017964c'   # <--- SEM VLOŽ ODDS API KĽÚČ
WHOP_API_KEY = 'apik_ZS6uQjWdBopkg_C4202856_C_10a5c981f1ca77611e77643b2f444b9bbcfe610f04a17148d8bca28af428fd'             # <--- SEM VLOŽ TEN NOVÝ WHOP KĽÚČ (začína sk_live_)
WHOP_PRODUCT_ID = None

# --- 2. DIZAJN CODEGREEN ---
st.set_page_config(page_title="CodeGreen AI", page_icon="🟢", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #00ff41; }
    .stTextInput > div > div > input { color: #00ff41; background-color: #1c2025; }
    h1, h2, h3 { color: #00ff41 !important; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #00ff41; color: black; border: none; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. OVERENIE LICENCIE (VYHADZOVAČ) ---
def check_license(key):
    # Ak nie je zadaný kľúč, rovno zamietni
    if not key: return False
    
    # Overenie cez Whop API
    url = f"https://api.whop.com/api/v2/memberships/{key}/validate_license"
    headers = {
        "Authorization": f"Bearer {WHOP_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('valid', False)
        return False
    except:
        return False

# --- 4. LOGIN OBRAZOVKA ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 ACCESS RESTRICTED")
    st.markdown("### Zabezpečený systém CodeGreen")
    st.write("Zadaj svoj licenčný kľúč pre vstup.")
    
    license_key = st.text_input("License Key", type="password")
    
    if st.button("UNLOCK SYSTEM"):
        if check_license(license_key):
            st.session_state.authenticated = True
            st.success("ACCESS GRANTED")
            st.rerun()
        else:
            # Backdoor pre teba (aby si sa tam dostal aj ty)
            if license_key == "ADMIN123": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ NEPLATNÝ KĽÚČ")
    
    st.stop() 

# --- 5. HLAVNÁ APLIKÁCIA (BEŽÍ AŽ PO PRIHLÁSENÍ) ---
SPORT_KEY = 'soccer_epl'
REGIONS = 'eu'
MARKETS = 'totals'
ODDS_FORMAT = 'decimal'

@st.cache_data(ttl=3600)
def fetch_odds():
    try:
        response = requests.get(
            f'https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds',
            params={
                'api_key': ODDS_API_KEY,
                'regions': REGIONS,
                'markets': MARKETS,
                'oddsFormat': ODDS_FORMAT,
            }
        )
        if response.status_code == 200: return response.json()
        return None
    except: return None

def analyze_value(matches):
    analyzed_data = []
    if not matches: return []
    for match in matches:
        home = match['home_team']
        away = match['away_team']
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

st.title("🟢 CODEGREEN_AI_V1.0")
st.markdown("`SYSTEM UNLOCKED. SCANNING MARKETS...`")

data = fetch_odds()
if data:
    analyzed = analyze_value(data)
    df = pd.DataFrame(analyzed)
    st.dataframe(df, use_container_width=True)
    if st.button("🔄 REFRESH"):
        st.cache_data.clear()
        st.rerun()
else:
    st.error("Chyba spojenia s Odds API. Skontroluj kľúč.")
