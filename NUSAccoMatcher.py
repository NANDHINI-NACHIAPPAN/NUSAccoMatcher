import streamlit as st
import pandas as pd
import re
import textwrap
import random
import time

# 1. Page Config
st.set_page_config(page_title="NUSAccoMatcher", page_icon="🏠", layout="wide")

# -------------------- Styling (NUS Branding) --------------------
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

# -------------------- Data Loading --------------------
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
            nums = re.findall(r'\d+', str(f).replace(',', ''))
            return int(nums[0]) if nums else 165

        df['Weekly_Fee_Num'] = df['Fee_Weekly'].apply(extract_fee)

        # -------- Generate realistic vibe / CCA data --------
        VIBE_OPTIONS = [
            "Sports", "Performing Arts", "Academic", "Social",
            "Entrepreneurship", "Volunteering", "Research",
            "Wellness", "Cultural", "Tech"
        ]

        def generate_vibes():
            return ", ".join(random.sample(VIBE_OPTIONS, random.randint(3, 6)))

        if 'Vibes' not in df.columns or df['Vibes'].isna().all():
            df['Vibes'] = df.apply(lambda _: generate_vibes(), axis=1)

        return df

    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# -------------------- Sidebar --------------------
with st.sidebar:
    st.header("Search Filters")

    if st.button("🔄 Reset All Filters"):
        st.session_state.clear()
        st.rerun()

    budget = st.slider("Weekly Budget (S$)", 100, 300, value=300, key="budget")

    user_vibe = st.multiselect(
        "Desired Vibe / CCA",
        ["Sports", "Performing Arts", "Academic", "Social", "Entrepreneurship",
         "Volunteering", "Research", "Wellness", "Cultural", "Tech"],
        key="vibe"
    )

    major = st.selectbox(
        "Your Faculty",
        ["Select Faculty...", "SoC(Computing)", "FASS(Arts)", "Business",
         "FoS(Science)", "CDE (Engineering)", "SDE (Design)", "Law", "Medicine"],
        key="major"
    )

    needs_ac = st.checkbox("Requires Air-Con", key="ac")
    needs_meals = st.checkbox("Requires Meal Plan", key="meals")
    wants_mods = st.checkbox("Wants Academic Modules", key="mods")

    st.markdown("---")

    if st.button("🔎 Find My Matches", use_container_width=True):
        st.session_state.search_clicked = True

# -------------------- Scoring Logic --------------------
def calculate_score(row):
    score = 10
    feedback = ["Base Experience (+10)"]

    # Faculty proximity
    if major != "Select Faculty...":
        fac_kw = major.split('(')[0].strip()
        if fac_kw in str(row['1st Nearest Faculty']):
            score += 20; feedback.append("Prime Location (+20)")
        elif fac_kw in str(row['2nd Nearest Faculty']):
            score += 15; feedback.append("Convenient Location (+15)")

    # -------- Weighted Vibe Similarity (Jaccard) --------
    if user_vibe:
        row_vibes = set(v.strip().lower() for v in str(row['Vibes']).split(","))
        user_vibes = set(v.lower() for v in user_vibe)

        overlap = row_vibes.intersection(user_vibes)
        union = row_vibes.union(user_vibes)

        similarity = len(overlap) / len(union) if union else 0
        vibe_pts = round(similarity * 20, 2)

        score += vibe_pts
        if vibe_pts > 0:
            feedback.append(f"Vibe Alignment (+{vibe_pts})")

    # Budget scoring
    if row['Weekly_Fee_Num'] <= budget:
        score += 10; feedback.append("Within Budget (+10)")
    else:
        proximity_pts = round(10 * (budget / row['Weekly_Fee_Num']), 2)
        score += proximity_pts
        feedback.append(f"Price Fit (+{proximity_pts})")

    # Facilities
    if needs_ac and "Air-con" in str(row['AirCon']):
        score += 8; feedback.append("Air-Con (+8)")
    if needs_meals and "Yes" in str(row['MealPlan']):
        score += 6; feedback.append("Meals (+6)")
    if wants_mods and "Yes" in str(row['Modules']):
        score += 6; feedback.append("Modules (+6)")

    # Tiny noise to avoid identical % matches
    score += random.uniform(0, 0.5)

    return score, " • ".join(feedback)

# -------------------- Header --------------------
logo_col, title_col = st.columns([1, 4])

with logo_col:
    st.image(
        "https://nus.edu.sg/images/default-source/identity-images/NUS_logo_full-horizontal.jpg",
        width=150
    )

with title_col:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='color:#003D7C;'>NUSAccoMatcher</h1>", unsafe_allow_html=True)

# -------------------- Main Logic --------------------
data = load_clean_data()

if not st.session_state.get("search_clicked", False):
    st.info("👈 Adjust your preferences and click **Find My Matches**")
    st.stop()

with st.spinner("🔍 Finding the best accommodation matches for you..."):
    time.sleep(1.5)

    results = data.apply(calculate_score, axis=1)
    data['Total_Score'], data['Feedback'] = zip(*results)

    MAX_POSSIBLE = 75
    display_data = data.sort_values(
        by=['Total_Score', 'Weekly_Fee_Num'],
        ascending=[False, True]
    ).head(10)

st.subheader("🏠 Recommended NUS Accommodations")

for i, (_, row) in enumerate(display_data.iterrows()):
    col_img, col_txt = st.columns([1, 2])

    with col_img:
        st.image(
            row['Image URL'] if pd.notna(row['Image URL']) else "https://via.placeholder.com/400x300",
            use_container_width=True
        )

    with col_txt:
        match_pct = min(100, int((row['Total_Score'] / MAX_POSSIBLE) * 100))

        html_content = textwrap.dedent(f"""
            <div class="result-box">
            <span class="match-tag">{match_pct}% Match</span>
            <span class="rank-badge">#{i+1}</span>
            <h2 style="display:inline; margin-left:10px; color:#003D7C;">{row['Name']}</h2>
            <p><b>{row['Type']}</b> | Weekly Fee: {row['Fee_Weekly']}</p>
            <p style="font-size:0.9em; color:#555;"><i>{row['Feedback']}</i></p>
            </div>
        """)

        st.markdown(html_content, unsafe_allow_html=True)

        with st.expander("🔍 View Details & Facilities"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"📍 **Location:** {row['1st Nearest Faculty']}")
                st.write(f"🍱 **Meals:** {row['MealPlan']}")
                st.write(f"🛌 **Room Type:** {row['Room_Types']}")
            with c2:
                st.write(f"✨ **Vibes:** {row['Vibes']}")
                if pd.notna(row['Virtual_Tour']):
                    st.link_button("🌐 Virtual Tour", row['Virtual_Tour'])

    st.divider()
