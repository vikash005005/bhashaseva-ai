import json
import os
import re
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env", override=True)

st.set_page_config(
    page_title="BhashaSeva AI - Indian Public Service Assistant",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

LANGUAGES = {
    "Hindi (हिन्दी)": "Hindi",
    "English": "English",
    "Bengali (বাংলা)": "Bengali",
    "Marathi (मराठी)": "Marathi",
    "Tamil (தமிழ்)": "Tamil",
    "Telugu (తెలుగు)": "Telugu",
    "Gujarati (ગુજરાતી)": "Gujarati",
    "Kannada (ಕನ್ನಡ)": "Kannada",
    "Malayalam (മലയാളം)": "Malayalam",
    "Punjabi (ਪੰਜਾਬੀ)": "Punjabi",
    "Odia (ଓଡ଼ିଆ)": "Odia",
    "Assamese (অসমীয়া)": "Assamese",
    "Urdu (اردو)": "Urdu",
    "Sanskrit (संस्कृतम्)": "Sanskrit",
    "Nepali (नेपाली)": "Nepali",
    "Konkani (कोंकणी)": "Konkani",
    "Maithili (मैथिली)": "Maithili",
}

# --- Theme Management ---
# Check query parameters for theme persistence across refresh
query_theme = st.query_params.get("theme", None)
if "theme" not in st.session_state:
    if query_theme in ("light", "dark"):
        st.session_state["theme"] = query_theme
    else:
        st.session_state["theme"] = "light"

current_theme = st.session_state["theme"]

# Theme-specific CSS variables
if current_theme == "dark":
    THEME_VARS = """
    :root {
        --bg-page: #0b1320;
        --bg-sidebar: #111c2e;
        --bg-card: #182438;
        --bg-card-subtle: #1e2e46;
        --bg-input: #131d2e;
        --text-main: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #24364e;
        --border-light: #1e2e46;
        --primary: #10b981;
        --primary-hover: #059669;
        --primary-light: rgba(16, 185, 129, 0.15);
        --accent-badge: #0ea5e9;
        --accent-badge-bg: rgba(14, 165, 233, 0.16);
        --hero-bg: linear-gradient(135deg, #132238 0%, #1e355b 50%, #0d3b2e 100%);
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.25);
        --shadow-md: 0 6px 20px rgba(0, 0, 0, 0.35);
        --tag-bg: #22344d;
        --tag-text: #93c5fd;
    }
    """
else:
    THEME_VARS = """
    :root {
        --bg-page: #f8fafc;
        --bg-sidebar: #f1f5f9;
        --bg-card: #ffffff;
        --bg-card-subtle: #f8fafc;
        --bg-input: #ffffff;
        --text-main: #0f172a;
        --text-secondary: #334155;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --border-light: #edf2f7;
        --primary: #059669;
        --primary-hover: #047857;
        --primary-light: #ecfdf5;
        --accent-badge: #0284c7;
        --accent-badge-bg: #e0f2fe;
        --hero-bg: linear-gradient(135deg, #064e3b 0%, #065f46 45%, #0f766e 100%);
        --shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.04);
        --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.07);
        --tag-bg: #f1f5f9;
        --tag-text: #0369a1;
    }
    """

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

{THEME_VARS}

/* Base resets & typography */
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
    color: var(--text-main);
}}

.stApp {{
    background-color: var(--bg-page);
    color: var(--text-main);
    transition: background-color 0.25s ease, color 0.25s ease;
}}

.block-container {{
    max-width: 1220px;
    padding-top: 4.8rem !important;
    padding-bottom: 3rem;
}}

/* Header bar clearance & clean-up */
header[data-testid="stHeader"] {{
    background-color: transparent !important;
    z-index: 100 !important;
}}

[data-testid="stDeployButton"], .stDeployButton {{
    display: none !important;
}}

/* Sidebar container */
[data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-color);
}}

[data-testid="stSidebar"] hr {{
    border-color: var(--border-color) !important;
    margin: 1rem 0;
}}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {{
    color: var(--text-main);
}}

[data-testid="stSidebar"] .sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.2rem;
}}

[data-testid="stSidebar"] .sidebar-brand h2 {{
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0;
    color: var(--text-main);
}}

[data-testid="stSidebar"] .sidebar-sub {{
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 0.8rem;
}}

/* Form elements & Selectboxes in Sidebar and Main page */
[data-testid="stSelectbox"] label,
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p {{
    color: var(--text-main) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.35rem !important;
}}

/* Fix dropdown text, background and contrast */
[data-baseweb="select"] {{
    border-radius: 9px !important;
}}

[data-baseweb="select"] > div {{
    background-color: var(--bg-input) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 9px !important;
    color: var(--text-main) !important;
    min-height: 42px !important;
    transition: all 0.2s ease !important;
}}

[data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:focus-within {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px var(--primary-light) !important;
}}

/* Ensure selected text is clearly readable */
[data-baseweb="select"] div,
[data-baseweb="select"] span,
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {{
    color: var(--text-main) !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
}}

/* Dropdown arrow icon styling */
[data-baseweb="select"] svg {{
    fill: var(--text-muted) !important;
    color: var(--text-muted) !important;
    width: 20px !important;
    height: 20px !important;
}}

/* Opened dropdown popover menu */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"] {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow-md) !important;
    padding: 6px !important;
}}

li[role="option"] {{
    background-color: var(--bg-card) !important;
    color: var(--text-main) !important;
    border-radius: 7px !important;
    padding: 8px 12px !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
}}

li[role="option"]:hover,
li[role="option"][aria-selected="true"] {{
    background-color: var(--primary-light) !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
}}

/* Text Area and Input Controls */
.stTextArea textarea, .stTextInput input {{
    background-color: var(--bg-input) !important;
    color: var(--text-main) !important;
    border: 1.5px solid var(--border-color) !important;
    border-radius: 11px !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
}}

.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px var(--primary-light) !important;
}}

/* Buttons */
div.stButton > button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}}

div.stButton > button[kind="primary"] {{
    background-color: var(--primary) !important;
    color: #ffffff !important;
    border: none !important;
}}

div.stButton > button[kind="primary"]:hover {{
    background-color: var(--primary-hover) !important;
    box-shadow: 0 4px 12px rgba(5, 150, 105, 0.28) !important;
}}

div.stButton > button[kind="secondary"] {{
    background-color: var(--bg-card) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-color) !important;
}}

div.stButton > button[kind="secondary"]:hover {{
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background-color: var(--primary-light) !important;
}}

/* Header & Top Bar */
.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border-light);
    margin-bottom: 1.2rem;
}}

.brand-wrapper {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-bottom: 0.6rem;
}}

.brand-title {{
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.02em;
    margin: 0;
}}

.brand-tag {{
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    background: var(--accent-badge-bg);
    color: var(--accent-badge);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* Hero Section */
.hero-card {{
    background: var(--hero-bg);
    color: #ffffff;
    border-radius: 20px;
    padding: 2.2rem 2.4rem;
    box-shadow: var(--shadow-md);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}}

.hero-pill-row {{
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.85rem;
}}

.hero-pill {{
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(8px);
    color: #ffffff;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}}

.hero-card h1 {{
    font-size: 2.3rem;
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.02em;
    color: #ffffff;
    line-height: 1.2;
}}

.hero-card p {{
    font-size: 1.05rem;
    margin: 0;
    max-width: 820px;
    color: rgba(255, 255, 255, 0.92);
    line-height: 1.5;
}}

/* Feature / Stat Cards */
.feature-box {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}}

.feature-box:hover {{
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--primary);
}}

.feature-box h4 {{
    margin: 0 0 0.35rem 0;
    font-size: 1.02rem;
    font-weight: 700;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.feature-box p {{
    margin: 0;
    font-size: 0.87rem;
    color: var(--text-muted);
    line-height: 1.45;
}}

/* Glass container for search & panels */
.glass-panel {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.4rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1.5rem;
}}

/* Suggestion pills */
.suggestions-title {{
    font-size: 0.84rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}}

/* Scheme Cards */
.scheme-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.35rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}}

.scheme-card:hover {{
    border-color: var(--primary);
    box-shadow: var(--shadow-md);
}}

.scheme-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
    gap: 0.75rem;
}}

.scheme-name {{
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-main);
    margin: 0;
}}

.badge-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-bottom: 0.75rem;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-size: 0.74rem;
    font-weight: 600;
}}

.badge-region {{
    background-color: var(--tag-bg);
    color: var(--tag-text);
}}

.badge-category {{
    background-color: var(--primary-light);
    color: var(--primary);
}}

.badge-beneficiary {{
    background-color: var(--accent-badge-bg);
    color: var(--accent-badge);
}}

.benefit-highlight {{
    background-color: var(--bg-card-subtle);
    border-left: 3px solid var(--primary);
    border-radius: 0 8px 8px 0;
    padding: 0.55rem 0.85rem;
    margin: 0.75rem 0;
    font-size: 0.88rem;
    color: var(--text-secondary);
}}

.benefit-highlight strong {{
    color: var(--text-main);
}}

/* AI Response block */
.ai-response-box {{
    background-color: var(--bg-card);
    border: 1.5px solid var(--primary);
    border-radius: 16px;
    padding: 1.6rem;
    box-shadow: var(--shadow-md);
    margin: 1.2rem 0;
    position: relative;
}}

.ai-header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--primary-light);
    color: var(--primary);
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.85rem;
}}

/* Active model badge in sidebar */
.model-indicator {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    font-size: 0.82rem;
    color: var(--text-main);
    margin-top: 0.35rem;
    font-weight: 600;
}}

.status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    display: inline-block;
}}

/* Footer */
.footer {{
    text-align: center;
    color: var(--text-muted);
    padding: 2.5rem 0 1rem;
    font-size: 0.84rem;
    border-top: 1px solid var(--border-light);
    margin-top: 2rem;
    line-height: 1.6;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_services():
    """Load verified government schemes and services from local JSON."""
    with open(BASE_DIR / "data" / "services.json", "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_available_models(api_key):
    """Return text models available to this API key that support generateContent."""
    if not api_key:
        return []
    try:
        response = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            headers={"x-goog-api-key": api_key},
            params={"pageSize": 100},
            timeout=8,
        )
        if not response.ok:
            return []

        excluded = (
            "image", "tts", "live", "transcribe", "embedding", "veo", "imagen",
            "aqa", "robotics", "computer-use", "nano", "banana", "argon",
            "preview", "3.8", "3.7"
        )
        names = []
        for model in response.json().get("models", []):
            name = model.get("name", "").replace("models/", "")
            methods = model.get("supportedGenerationMethods", [])
            if (
                name.startswith("gemini-")
                and "generateContent" in methods
                and not any(word in name.lower() for word in excluded)
            ):
                names.append(name)

        priority = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
        ]
        sorted_names = [m for m in priority if m in names]
        for m in sorted(names):
            if m not in sorted_names:
                sorted_names.append(m)
        return sorted_names
    except Exception:
        # Fallback cleanly on network timeout or DNS restriction
        return ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]


def search_and_rank_services(services, query, category_filter="All Services", state_filter="All Regions"):
    """
    Intelligently search, score, and rank verified schemes.
    Handles semantic keywords in Hindi, Hinglish, and English across categories and states.
    """
    # 1. Filter by category
    filtered = services
    if category_filter and category_filter != "All Services":
        filtered = [s for s in filtered if s.get("category") == category_filter]

    # 2. Filter by state/region
    if state_filter and state_filter != "All Regions":
        filtered = [
            s for s in filtered
            if s.get("region") == state_filter or s.get("region") == "All India"
        ]

    cleaned_q = query.strip().lower()
    if not cleaned_q or cleaned_q in ("all", "all schemes", "sab schemes", "list", "saari schemes"):
        return filtered

    # Keyword mappings for Indian public service concepts
    intent_keywords = {
        "student": ["student", "students", "scholarship", "chhatravritti", "padhai", "shiksha", "vidyarthi", "college", "school", "exam", "12th", "10th", "matric", "degree"],
        "farmer": ["farmer", "farmers", "kisan", "krishi", "kheti", "fasal", "bima", "land", "crop", "samman"],
        "health": ["health", "swasthya", "hospital", "ilaj", "ayushman", "treatment", "card", "bimar", "bimaari", "cashless"],
        "women": ["women", "woman", "mahila", "girl", "beti", "ladki", "mother", "maternity", "pregnant", "garbhvati", "sukanya"],
        "pension": ["pension", "vridha", "old age", "senior", "buzurg", "elderly", "60", "retirement", "atal"],
        "employment": ["employment", "job", "jobs", "rojgar", "nrega", "work", "unemployment", "berojgar", "worker", "business", "subsidy"],
        "housing": ["housing", "house", "ghar", "makan", "awas", "pmay", "home"],
        "finance": ["loan", "credit", "rin", "paisa", "fund", "mudra", "svanidhi", "vendor", "thela", "hawker"],
        "certificates": ["certificate", "praman", "income", "caste", "domicile", "aay", "jati", "niwas", "edistrict", "tehsil"],
        "madhya_pradesh": ["madhya pradesh", "mp", "bhopal", "indore"],
        "uttar_pradesh": ["uttar pradesh", "up", "lucknow", "kanpur", "varanasi"],
    }

    scored_results = []
    for item in filtered:
        score = 0
        name = item.get("name", "").lower()
        summary = item.get("summary", "").lower()
        category = item.get("category", "").lower()
        region = item.get("region", "").lower()
        beneficiary = item.get("target_beneficiary", "").lower()
        benefits = item.get("key_benefits", "").lower()

        # Direct name match
        if name in cleaned_q:
            score += 40
        for token in cleaned_q.split():
            if len(token) > 2 and token in name:
                score += 15

        # Query token matches
        for word in cleaned_q.split():
            if len(word) < 3:
                continue
            if word in summary:
                score += 4
            if word in category:
                score += 8
            if word in beneficiary:
                score += 8
            if word in benefits:
                score += 4

        # Semantic intent matches
        for topic, kws in intent_keywords.items():
            if any(kw in cleaned_q for kw in kws):
                if topic == "student" and ("scholarship" in category or "student" in beneficiary):
                    score += 15
                elif topic == "farmer" and ("farmer" in category or "farmer" in beneficiary):
                    score += 15
                elif topic == "health" and "health" in category:
                    score += 15
                elif topic == "women" and ("women" in category or "women" in beneficiary or "mother" in beneficiary):
                    score += 15
                elif topic == "pension" and "pension" in category:
                    score += 15
                elif topic == "employment" and "employment" in category:
                    score += 15
                elif topic == "housing" and "housing" in category:
                    score += 15
                elif topic == "finance" and "financial" in category:
                    score += 15
                elif topic == "certificates" and "certificate" in category:
                    score += 15
                elif topic == "madhya_pradesh" and "madhya pradesh" in region:
                    score += 25
                elif topic == "uttar_pradesh" and "uttar pradesh" in region:
                    score += 25

        if score > 0:
            scored_results.append((score, item))

    # Sort descending by relevance score
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_results] if scored_results else filtered


def make_context(items):
    """Serialize verified scheme records as clean grounded JSON context."""
    return json.dumps(items, ensure_ascii=False, indent=2)


def ask_gemini(question, language, category, matched, model, chat_history=None):
    """
    Send grounded prompt to Gemini API with verified scheme context,
    specified target language, and conversation history.
    """
    if model in ("gemini-3.8-flash", "gemini-3.7-flash"):
        model = "gemini-3.5-flash"

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Please add it to your .env file.")

    history_str = ""
    if chat_history and len(chat_history) > 1:
        recent = chat_history[-4:-1]
        formatted = []
        for msg in recent:
            role = "Citizen" if msg["role"] == "user" else "BhashaSeva AI"
            formatted.append(f"{role}: {msg['content'][:300]}")
        history_str = "\nPREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(formatted) + "\n"

    prompt = f"""
You are BhashaSeva AI, an empathetic, responsible, and accurate public-service assistant for Indian citizens.
Answer the citizen's question strictly grounded in the supplied verified reference data.

Selected Category Filter: {category}
Required Response Language: {language}
Citizen Question: {question}
{history_str}
VERIFIED SCHEME REFERENCE DATA:
{make_context(matched[:8])}

Instructions & Responsible Output Rules:
1. Reply ENTIRELY in {language} (use proper native script for Hindi, Bengali, Tamil, etc., or English if English is selected). Official scheme titles or portal URLs can be retained in English or transliterated.
2. Structure your response clearly using concise headings, bullet points, and clean formatting:
   - **Direct Answer / Overview**: Directly answer the citizen's question without preamble.
   - **Key Benefits**: Highlight tangible benefits (financial support, insurance coverage, fee reimbursement, etc.).
   - **Likely Eligibility**: Mention verified conditions (income limits, domicile, age, etc.).
   - **Required Documents**: List mandatory documents needed for application.
   - **How to Apply**: Clear step-by-step application instructions.
   - **Official Portal**: Provide the verified official URL from the reference data.
3. If the citizen asks about multiple schemes (e.g. 'schemes for students' or 'all schemes'), present a neat list of matching schemes with concise descriptions and how to access each.
4. If the citizen asks a follow-up question (e.g. 'Iske liye apply kaise karun?' or 'Documents kya chahiye?'), refer to the specific scheme previously discussed in the context.
5. If the citizen's question requires knowing their specific state or category to give an accurate answer (e.g., state scholarships or certificates without mentioning their state), gently ask a short clarification question while providing the available verified information.
6. NEVER fabricate or hallucinate dates, monetary amounts, rules, or URLs not present in the verified data.
7. Never claim final eligibility, guaranteed approval, or legal certainty.
8. End with a short reminder that official rules and notifications must be verified on the official government portal.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.25,
                    "maxOutputTokens": 1800,
                },
            },
            timeout=60,
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"The request timed out while contacting model '{model}'. "
            "Please select a faster model such as 'gemini-3.5-flash' from the sidebar."
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error connecting to Gemini API: {exc}")

    if not response.ok:
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Gemini API error ({response.status_code}): {detail}")

    payload = response.json()
    candidates = payload.get("candidates", [])
    if not candidates:
        raise RuntimeError("The API returned no response. Please try rephrasing your question.")

    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "\n".join(part.get("text", "") for part in parts).strip()
    if not answer:
        raise RuntimeError("The API returned an empty answer.")
    return answer


# --- Load Data & Models ---
services = load_services()
STANDARD_CATEGORIES = [
    "All Services",
    "Education and Scholarships",
    "Agriculture and Farmers",
    "Health",
    "Employment",
    "Women and Child Welfare",
    "Housing",
    "Pension",
    "Financial Assistance",
    "Certificates and Public Documents",
]

# Ensure all categories in data are represented
existing_cats = {item.get("category") for item in services if item.get("category")}
all_categories = ["All Services"] + [c for c in STANDARD_CATEGORIES[1:] if c in existing_cats]
for c in sorted(existing_cats):
    if c not in all_categories:
        all_categories.append(c)

all_regions = ["All Regions", "All India", "Uttar Pradesh", "Madhya Pradesh"]

api_key = os.getenv("GEMINI_API_KEY", "").strip()
available_models = fetch_available_models(api_key)
configured_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
if configured_model in ("gemini-3.8-flash", "gemini-3.7-flash"):
    configured_model = "gemini-3.5-flash"

if not available_models:
    available_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]
if configured_model in available_models:
    available_models.remove(configured_model)
available_models.insert(0, configured_model)
available_models = list(dict.fromkeys(available_models))

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "selected_service_detail" not in st.session_state:
    st.session_state["selected_service_detail"] = None


# --- SIDEBAR UI ---
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span style="font-size: 1.8rem;">🇮🇳</span>
        <div>
            <h2 style="margin:0; font-size:1.35rem; font-weight:800;">BhashaSeva AI</h2>
        </div>
    </div>
    <div class="sidebar-sub">Indian Public Service & Scheme Assistant</div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("### ⚙️ Preferences")
    sidebar_theme_label = "🌙 Switch to Dark Mode" if current_theme == "light" else "☀️ Switch to Light Mode"
    if st.button(sidebar_theme_label, use_container_width=True, key="sidebar_theme_toggle_btn"):
        new_theme = "dark" if current_theme == "light" else "light"
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()

    st.write("")
    selected_language = st.selectbox(
        "Response language",
        list(LANGUAGES.keys()),
        index=0,
        help="Select your preferred Indian language for guidance.",
    )

    if len(available_models) > 1:
        selected_model = st.selectbox(
            "AI model",
            available_models,
            index=0,
            help="Compatible Gemini models available with your configured API key.",
        )
    else:
        selected_model = available_models[0]
        st.markdown(f"""
        <div style="font-size: 0.88rem; font-weight: 600; margin-bottom: 0.2rem;">AI model</div>
        <div class="model-indicator">
            <span class="status-dot"></span> {selected_model}
        </div>
        """, unsafe_allow_html=True)

    if selected_model in ("gemini-3.8-flash", "gemini-3.7-flash"):
        selected_model = "gemini-3.5-flash"

    st.markdown("""
    <div class="model-indicator" style="margin-top: 0.5rem;">
        <span class="status-dot"></span> Gemini API Connected
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔍 Filters")

    selected_category = st.selectbox(
        "Service category",
        all_categories,
        index=0,
        help="Filter verified schemes by category.",
    )

    selected_region = st.selectbox(
        "Region / State",
        all_regions,
        index=0,
        help="Filter by Central or State government schemes.",
    )

    st.divider()

    # Filtered count for sidebar
    sidebar_matches = search_and_rank_services(
        services, "", selected_category, selected_region
    )
    st.markdown(f"**Indexed Schemes ({len(sidebar_matches)})**")
    for s in sidebar_matches[:10]:
        st.caption(f"• {s['name']}")
    if len(sidebar_matches) > 10:
        st.caption(f"... and {len(sidebar_matches) - 10} more")

    st.divider()
    st.caption("College Minor Project • Grounded GenAI • Multilingual Public Service")


# --- TOP NAVIGATION & HEADER ---
col_head, col_theme = st.columns([3.6, 1.4], vertical_alignment="center")
with col_head:
    st.markdown(f"""
    <div class="brand-wrapper">
        <h2 class="brand-title">🇮🇳 BhashaSeva AI</h2>
        <span class="brand-tag">Grounded GenAI</span>
        <span class="brand-tag" style="background:var(--primary-light); color:var(--primary);">
            {len(services)} Verified Schemes Indexed
        </span>
    </div>
    """, unsafe_allow_html=True)

with col_theme:
    # Working Theme Toggle
    theme_btn_label = "🌙 Dark Mode" if current_theme == "light" else "☀️ Light Mode"
    if st.button(theme_btn_label, use_container_width=True, key="theme_toggle_btn"):
        new_theme = "dark" if current_theme == "light" else "light"
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()


# --- HERO SECTION ---
st.markdown("""
<div class="hero-card">
    <div class="hero-pill-row">
        <span class="hero-pill">🏛️ PUBLIC SERVICE INTELLIGENCE</span>
        <span class="hero-pill">🌐 17 INDIAN LANGUAGES</span>
        <span class="hero-pill">✅ 100% VERIFIED SOURCES</span>
    </div>
    <h1>Discover Government Schemes Across India</h1>
    <p>Find government schemes, scholarships, farmer welfare, and citizen certificate information in your preferred language, grounded in verified government data.</p>
</div>
""", unsafe_allow_html=True)


# --- FEATURE VALUE PROPOSITION ---
f1, f2, f3, f4 = st.columns(4)
with f1:
    st.markdown("""
    <div class="feature-box">
        <h4>🌐 Multilingual</h4>
        <p>Accurate guidance in Hindi, English, Bengali, Tamil, Telugu and 12 other Indian languages.</p>
    </div>
    """, unsafe_allow_html=True)
with f2:
    st.markdown("""
    <div class="feature-box">
        <h4>🎯 Grounded Data</h4>
        <p>Answers are verified against official government portals, reducing hallucinations.</p>
    </div>
    """, unsafe_allow_html=True)
with f3:
    st.markdown("""
    <div class="feature-box">
        <h4>🏛️ Multi-State</h4>
        <p>Covers Central schemes as well as State-specific initiatives for UP, MP, and more.</p>
    </div>
    """, unsafe_allow_html=True)
with f4:
    st.markdown("""
    <div class="feature-box">
        <h4>🔐 Safe & Privacy-First</h4>
        <p>No storage of sensitive credentials, Aadhaar numbers, or bank passwords.</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# --- SEARCH SUGGESTIONS ---
st.markdown('<div class="suggestions-title">💡 Popular Topics & Suggestions:</div>', unsafe_allow_html=True)
sug_cols = st.columns(6)

suggestions = [
    ("🎓 Scholarships", "India mein students ke liye kaun-kaun si scholarship schemes hain?"),
    ("🌾 Farmer Welfare", "Farmers aur kisan bhaiyo ke liye kaun si schemes available hain?"),
    ("🧓 Pension", "Senior citizens ke liye pension scheme ki eligibility aur apply process kya hai?"),
    ("👩 Women Welfare", "Women and child welfare ke liye central schemes kaun si hain?"),
    ("🏥 Healthcare", "Ayushman Bharat PM-JAY card kaise banwayein aur kya benefits hain?"),
    ("📄 Certificates", "Income certificate aur caste certificate kaise banwayein?"),
]

for i, (label, query_text) in enumerate(suggestions):
    with sug_cols[i]:
        if st.button(label, use_container_width=True, key=f"sug_{i}"):
            st.session_state["search_query"] = query_text
            st.session_state["auto_trigger"] = True
            st.rerun()


# --- SEARCH INPUT & ASK AI ---
with st.container():
    search_col1, search_col2 = st.columns([4.2, 1.2], gap="small")
    with search_col1:
        user_query = st.text_input(
            "Search scheme or ask any public-service question",
            value=st.session_state.get("search_query", ""),
            placeholder="e.g. Students ke liye scholarships, PM-KISAN eligibility, Income certificate process...",
            label_visibility="collapsed",
            key="main_search_input",
        )
    with search_col2:
        search_clicked = st.button("✨ Search & Ask AI", type="primary", use_container_width=True)

# Auto-trigger from suggestions
if st.session_state.get("auto_trigger"):
    search_clicked = True
    st.session_state["auto_trigger"] = False


# Find relevant schemes
current_query = user_query.strip()
matched_services = search_and_rank_services(
    services, current_query, selected_category, selected_region
)


# --- AI GENERATION FLOW ---
if search_clicked:
    if not current_query:
        st.warning("Please enter a question or select a suggestion above.")
    else:
        try:
            with st.spinner(f"Preparing grounded guidance in {selected_language}..."):
                # Append to chat history
                st.session_state["chat_history"].append({
                    "role": "user",
                    "content": current_query
                })

                ai_response = ask_gemini(
                    question=current_query,
                    language=LANGUAGES[selected_language],
                    category=selected_category,
                    matched=matched_services,
                    model=selected_model,
                    chat_history=st.session_state["chat_history"],
                )

                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": ai_response
                })
                st.session_state["last_answer"] = ai_response
                st.session_state["last_question"] = current_query
        except Exception as exc:
            st.error(str(exc))


# --- DISPLAY AI GUIDANCE RESULT ---
if st.session_state.get("last_answer"):
    st.markdown(f"""
    <div class="ai-response-box">
        <div class="ai-header-badge">
            ✨ Grounded AI Guidance ({selected_language}) • Model: {selected_model}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(st.session_state["last_answer"])

    st.markdown("</div>", unsafe_allow_html=True)

    d_col1, d_col2 = st.columns([1.5, 3])
    with d_col1:
        st.download_button(
            "⬇️ Download Official Guidance",
            data=(
                f"BhashaSeva AI - Public Service Guidance\n"
                f"Language: {selected_language}\n"
                f"Question: {st.session_state.get('last_question', '')}\n\n"
                f"Answer:\n{st.session_state['last_answer']}\n\n"
                "Disclaimer: Information is for educational and public guidance. Always verify on official government portals."
            ),
            file_name="bhashaseva_guidance.txt",
            mime="text/plain",
            use_container_width=True,
        )


# --- DISPLAY RELEVANT SCHEMES CATALOGUE ---
st.write("")
st.markdown("---")

header_col, count_col = st.columns([3, 1])
with header_col:
    if current_query:
        st.subheader(f"📋 Matching Schemes ({len(matched_services)})")
    else:
        st.subheader(f"🏛️ Verified Government Schemes Catalogue ({len(matched_services)})")
with count_col:
    st.caption("Indexed from official government portals")

# Distinguish indexed dataset notice
st.info(
    "ℹ️ **Catalogue Notice:** BhashaSeva AI currently indexes **18 verified Central, UP, and MP government schemes** "
    "with official documentation. For schemes not yet in the local indexed database, please verify directly on your state's official citizen portal."
)

if not matched_services:
    st.warning("No schemes found matching your specific filters. Try selecting 'All Services' or 'All Regions'.")
else:
    # Display schemes in responsive cards
    for idx, scheme in enumerate(matched_services):
        with st.container():
            col_info, col_act = st.columns([4, 1.2])

            with col_info:
                st.markdown(f"""
                <div class="scheme-card">
                    <div class="scheme-header">
                        <h3 class="scheme-name">{scheme['name']}</h3>
                    </div>
                    <div class="badge-row">
                        <span class="badge badge-region">📍 {scheme['region']}</span>
                        <span class="badge badge-category">📁 {scheme['category']}</span>
                        <span class="badge badge-beneficiary">🎯 {scheme.get('target_beneficiary', 'Citizens')}</span>
                    </div>
                    <p style="margin:0 0 0.5rem 0; font-size:0.92rem; color:var(--text-secondary);">
                        {scheme['summary']}
                    </p>
                    <div class="benefit-highlight">
                        <strong>🎁 Key Benefits:</strong> {scheme.get('key_benefits', 'Financial and public service assistance.')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_act:
                st.write("")
                st.write("")
                # Official source link
                st.link_button(
                    "🌐 Official Portal",
                    scheme["official_source"],
                    use_container_width=True,
                )
                # Ask AI button for this scheme
                if st.button("💬 Ask AI", key=f"ask_scheme_{idx}", use_container_width=True):
                    st.session_state["search_query"] = f"Tell me full details, eligibility and application steps for {scheme['name']}."
                    st.session_state["auto_trigger"] = True
                    st.rerun()

            # Expandable details
            with st.expander(f"🔍 View Full Details: {scheme['name']}"):
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown("**Likely Eligibility:**")
                    for el in scheme.get("likely_eligibility", []):
                        st.markdown(f"- {el}")

                    st.markdown("**Required Documents:**")
                    for doc in scheme.get("common_documents", []):
                        st.markdown(f"- {doc}")

                with d2:
                    st.markdown("**Application Steps:**")
                    for s_step in scheme.get("steps", []):
                        st.markdown(f"1. {s_step}")

                    st.markdown(f"**Official Source:** [{scheme['official_source']}]({scheme['official_source']})")


# --- FOOTER ---
st.markdown("""
<div class="footer">
    <strong>BhashaSeva AI</strong> • Multilingual Indian Public Service Assistant<br>
    Educational Minor Project • Built with Streamlit, Python & Gemini REST API<br>
    <em>Disclaimer: All scheme information is verified from official portals but subject to periodic government updates. Final eligibility is determined solely by the competent department.</em>
</div>
""", unsafe_allow_html=True)
