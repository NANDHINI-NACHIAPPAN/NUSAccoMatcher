# 🏠 NUSAccoMatcher
**Finding your perfect stay at NUS, simplified.**

## 🚀 Problem Statement
NUS has 15+ types of housing. International freshmen and exchange students struggle to find a match based on their faculty, budget, and cultural "vibe."

## ✨ Key Features
- **Weighted Scoring Engine:** Prioritizes Vibe (40%) and Proximity (25%).
- **Interview Tracker:** Identifies halls that require essays or interviews.
- **Interactive Filtering:** Live match percentage updates as you toggle preferences.

## 🛠️ Tech Stack
- Python (Streamlit, Pandas)
- Deployed on Streamlit Community Cloud
- How the Scoring Works
The app uses a weighted point system to determine the "Match %":

Faculty Proximity: Up to +20 pts for being near your department.

Budget Fit: +10 pts if within budget (with partial credit for close matches).

Vibe Alignment: +5 pts per matching interest.

Essentials: Bonus points for Air-Con, Meals, and specific Room types.
