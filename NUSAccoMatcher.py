import streamlit as st
import pandas as pd
import re
import textwrap

# 1. Page Config
st.set_page_config(page_title="NUS HomeMatch", page_icon="🏠", layout="wide")

# 2. Styling (NUS Branding)
st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    .main h1, .main h2, .main h3 { color: #003D7C !important; }
    [data-testid="stSidebar"] { background-color: #003D7C; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p { color: white !important; }
    .result-box {
        border: 2px solid #efefef;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
        color: black;
    }
    .rank-badge { background-color: #003D7C; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; }
    .match-tag { color: #EF7C00; font-weight: bold; font-size: 1.2em; float: right; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_clean_data():
    try:
        df_raw = pd.read_csv("housing_data.csv", encoding='latin-1', header=None)
        header_row_index = 0
        for i, row in df_raw.iterrows():
            if "Name" in row.values:
                header_row_index = i
                break
        df = pd.read_csv("housing_data.csv", skiprows=header_row_index, encoding='latin-1')
        def extract_fee(f):
            try:
                nums = re.findall(r'\d+', str(f).replace(',', ''))
                return int(nums[0]) if nums else 165 # Default to min price if empty
            except: return 165
        df['Weekly_Fee_Num'] = df['Fee_Weekly'].apply(extract_fee)
        return df
    except Exception as e:
        st.error(f"Error: {e}"); return pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Search Filters")
    if st.button("🔄 Reset All Filters"):
        st.session_state.budget = 300
        st.session_state.vibe = []
        st.session_state.major = "Select Faculty..."
        st.session_state.ac = False
        st.session_state.meals = False
        st.session_state.mods = False
        st.session_state.room = "Any"
        st.rerun()

    budget = st.slider("Weekly Budget (S$)", 100, 300, value=300, key="budget")
    user_vibe = st.multiselect("Desired Vibe", ["Sports", "Performing Arts", "Social", "Academic", "Relaxed", "Independent", "Balanced"], key="vibe")
    major = st.selectbox("Your Faculty", ["Select Faculty...", "SoC(Computing)", "FASS(Arts)", "Business", "FoS(Science)", "CDE (Engineering)", "SDE (Design)", "Law", "Medicine"], key="major")
    needs_ac = st.checkbox("Requires Air-Con", key="ac")
    needs_meals = st.checkbox("Requires Meal Plan", key="meals") 
    wants_mods = st.checkbox("Wants Academic Modules", key="mods")
    pref_room = st.selectbox("Room Preference", ["Any", "Single", "Double", "Apt"], key="room")

def calculate_score(row):
    # START WITH BASE SCORE (Prevents 0% match)
    score = 10 
    feedback = ["Base Experience (+10)"]
    
    # 1. Faculty Proximity
    if major != "Select Faculty...":
        fac_kw = major.split('(')[0].strip()
        if fac_kw in str(row['1st Nearest Faculty']): score += 20; feedback.append("Prime Location (+20)")
        elif fac_kw in str(row['2nd Nearest Faculty']): score += 15; feedback.append("Convenient Location (+15)")
    
    # 2. Vibe Match
    if user_vibe:
        matches = sum(1 for v in user_vibe if v.lower() in str(row['Vibes']).lower())
        if matches > 0:
            vibe_pts = min(10, matches * 5)
            score += vibe_pts
            feedback.append(f"Vibe Match (+{vibe_pts})")

    # 3. BUDGET SCORING (Comparative Logic)
    # If price is within budget, full 10 points.
    # If price is over budget, give points based on how close it is (Ratio).
    if row['Weekly_Fee_Num'] <= budget:
        score += 10
        feedback.append("Within Budget (+10)")
    else:
        # Comparative scoring: Lower price = more points even if over budget
        proximity_pts = round(10 * (budget / row['Weekly_Fee_Num']), 1)
        score += proximity_pts
        feedback.append(f"Price Fit (+{proximity_pts})")

    # 4. Facilities
    if needs_ac and "Air-con" in str(row['AirCon']): score += 8; feedback.append("Air-Con (+8)")
    if needs_meals and "Yes" in str(row['MealPlan']): score += 6; feedback.append("Meals (+6)")
    if wants_mods and "Yes" in str(row['Modules']): score += 6; feedback.append("Modules (+6)")

    return score, " • ".join(feedback)

# --- MAIN DISPLAY ---
st.image("https://nus.edu.sg/images/default-source/identity-images/NUS_logo_full-horizontal.jpg", width=300)
data = load_clean_data()

if not data.empty:
    filters_active = any([
        major != "Select Faculty...", 
        user_vibe != [], 
        budget < 300, 
        needs_ac, 
        needs_meals, 
        wants_mods, 
        pref_room != "Any"
    ])
    
    results = data.apply(calculate_score, axis=1)
    data['Total_Score'], data['Feedback'] = [r[0] for r in results], [r[1] for r in results]
    
    # Max Score for % calculation is approx 75
    MAX_POSSIBLE = 75
    
    if filters_active:
        st.subheader("🏠 Recommended NUS Accommodations")
        # Prioritize Score, then prioritize lower costs
        display_data = data.sort_values(by=['Total_Score', 'Weekly_Fee_Num'], ascending=[False, True]).head(10)
        
        if budget < 160:
            st.info(f"💡 Budget Tip: Most NUS hostels start at ~$165. We've highlighted the most affordable options matching your vibes.")
    else:
        st.subheader("📋 All NUS Accommodations")
        display_data = data

    for i, (idx, row) in enumerate(display_data.iterrows()):
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            st.image(row['Image URL'] if pd.notna(row['Image URL']) else "https://via.placeholder.com/400x300", use_container_width=True)
        
        with col_txt:
            # Percentage will never be 0 because of the Base Score
            match_pct = min(100, int((row["Total_Score"] / MAX_POSSIBLE) * 100))
            score_html = f'<span class="match-tag">{match_pct}% Match</span>' if filters_active else ""
            
            html_content = textwrap.dedent(f"""
                <div class="result-box">
                {score_html}
                <span class="rank-badge">#{i+1}</span>
                <h2 style="display:inline; margin-left:10px; color:#003D7C;">{row['Name']}</h2>
                <p style="margin-top:10px;"><b>{row['Type']}</b> | Weekly Fee: {row['Fee_Weekly']}</p>
                <p style="font-size:0.9em; color:#555;"><i>{row['Feedback'] if row['Feedback'] else "Explore this option"}</i></p>
                </div>
            """).strip()
            
            st.markdown(html_content, unsafe_allow_html=True)
            
            with st.expander("🔍 View Details & Facilities"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"📍 **Location:** {row['1st Nearest Faculty']}")
                    st.write(f"🍱 **Meals:** {row['MealPlan']}")
                    st.write(f"🛌 **Room Type:** {row['Room_Types']}")
                with c2:
                    st.write(f"✨ **Vibes:** {row['Vibes']}")
                    if pd.notna(row['Virtual_Tour']): st.link_button("🌐 Virtual Tour", str(row['Virtual_Tour']))
        st.divider()
else:
    st.error("Data file not found. Please ensure 'housing_data.csv' is in the folder.")