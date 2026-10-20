import json
import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env", override=True)

st.set_page_config(
    page_title="BhashaSeva AI",
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

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #fffaf3 0%, #f7fbff 48%, #f4fff8 100%); }
.block-container { max-width: 1180px; padding-top: 1.8rem; padding-bottom: 3rem; }
.hero { padding: 2.1rem; border-radius: 24px; background: linear-gradient(120deg,#ff7a18,#ffb347 42%,#159957); color:white; box-shadow:0 18px 50px rgba(35,60,70,.16); margin-bottom:1.4rem; }
.hero h1 { font-size: 2.65rem; margin:0; font-weight:800; }
.hero p { font-size:1.08rem; margin:.65rem 0 0; max-width:760px; opacity:.96; }
.glass { padding:1.15rem 1.25rem; background:rgba(255,255,255,.82); border:1px solid rgba(15,60,80,.09); border-radius:18px; box-shadow:0 8px 28px rgba(20,55,70,.08); }
.feature { min-height:130px; padding:1.1rem; border-radius:17px; background:white; border:1px solid #e9eef2; box-shadow:0 6px 18px rgba(30,60,80,.06); }
.feature h3 { margin:.15rem 0 .35rem; font-size:1.03rem; }
.feature p { color:#526170; font-size:.91rem; }
.answer { padding:1.35rem; border-radius:18px; background:#fff; border-left:6px solid #159957; box-shadow:0 7px 24px rgba(30,60,80,.08); }
.pill { display:inline-block; padding:.28rem .65rem; border-radius:999px; background:#eaf8f0; color:#08743b; font-size:.78rem; font-weight:700; margin-right:.3rem; }
.footer { text-align:center; color:#6b7580; padding:2rem 0 .5rem; font-size:.85rem; }
div.stButton > button { border-radius:12px; min-height:46px; font-weight:700; }
[data-testid="stSidebar"] { background:#102f3b; }
[data-testid="stSidebar"] * { color:#f7fbff; }
[data-testid="stSidebar"] .stSelectbox label { color:#f7fbff !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

@st.cache_data
def load_services():
    with open(BASE_DIR / "data" / "services.json", "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_available_models(api_key):
    """Return text models available to this API key that support generateContent."""
    if not api_key:
        return []
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": api_key},
        params={"pageSize": 1000},
        timeout=25,
    )
    if not response.ok:
        return []

    excluded = (
        "image", "tts", "live", "transcribe", "embedding", "veo", "imagen",
        "aqa", "robotics", "computer-use", "nano", "banana", "argon",
        "preview", "3.8", "3.7", "2.5"
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

    priority = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-flash-lite"]
    sorted_names = [m for m in priority if m in names]
    for m in sorted(names):
        if m not in sorted_names:
            sorted_names.append(m)
    return sorted_names


def matching_services(services, category):
    if category == "All services":
        return services
    return [item for item in services if item["category"] == category]


def make_context(items):
    return json.dumps(items, ensure_ascii=False, indent=2)


def ask_gemini(question, language, category, matched, model):
    if model in ("gemini-3.8-flash", "gemini-3.7-flash"):
        model = "gemini-3.5-flash"

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")

    prompt = f"""
You are BhashaSeva AI, a responsible assistant for an Indian college minor project.
Answer the citizen's public-service question using ONLY the supplied local reference data.

Selected category: {category}
Required answer language: {language}
Citizen question: {question}

REFERENCE DATA:
{make_context(matched)}

Rules:
- Reply entirely in {language}, except unavoidable official names or URLs.
- Use very simple, respectful language and short headings.
- Include: direct answer, likely eligibility, documents, application steps, and official source.
- Never claim final eligibility, approval, or legal certainty.
- Do not invent dates, money amounts, rules, or URLs.
- If the reference does not contain the answer, say that the available project data is insufficient.
- End with a clear note to verify the latest details on the official portal.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200},
            },
            timeout=60,
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"The request timed out while waiting for model '{model}'. "
            "This model may be under heavy load or unavailable. "
            "Please select a faster model such as 'gemini-3.5-flash' or 'gemini-3.5-flash-lite' from the sidebar."
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error connecting to Gemini API: {exc}")

    if not response.ok:
        detail = response.json().get("error", {}).get("message", response.text)
        raise RuntimeError(f"Gemini API error: {detail}")

    payload = response.json()
    candidates = payload.get("candidates", [])
    if not candidates:
        raise RuntimeError("The API returned no answer. Please try a different question.")
    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "\n".join(part.get("text", "") for part in parts).strip()
    if not answer:
        raise RuntimeError("The API returned an empty answer.")
    return answer


services = load_services()
categories = ["All services"] + sorted({item["category"] for item in services})
api_key = os.getenv("GEMINI_API_KEY", "").strip()
available_models = fetch_available_models(api_key)
configured_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
if configured_model in ("gemini-3.8-flash", "gemini-3.7-flash"):
    configured_model = "gemini-3.5-flash"

if not available_models:
    available_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]
if configured_model in available_models:
    available_models.remove(configured_model)
available_models.insert(0, configured_model)
available_models = list(dict.fromkeys(available_models))

with st.sidebar:
    st.markdown("## 🇮🇳 BhashaSeva AI")
    st.caption("Indian Language Public Service Assistant")
    st.divider()
    selected_language = st.selectbox("Response language", list(LANGUAGES.keys()))
    selected_model = st.selectbox(
        "Gemini model",
        available_models,
        index=0,
        help="Models are fetched from the Gemini Models API for your API key."
    )
    if selected_model in ("gemini-3.8-flash", "gemini-3.7-flash"):
        selected_model = "gemini-3.5-flash"
    if api_key and len(available_models) > 1:
        st.caption(f"{len(available_models)} compatible text models detected")
    elif not api_key:
        st.caption("Add your API key to load models dynamically")
    selected_category = st.selectbox("Service category", categories)
    st.divider()
    st.markdown("**Available services**")
    for service in services:
        st.caption(f"• {service['name']}")
    st.divider()
    st.caption("Minor Project • Python • Streamlit • Gemini API")

st.markdown("""
<div class="hero">
  <span class="pill">GENAI</span><span class="pill">INDIAN LANGUAGES</span>
  <h1>BhashaSeva AI</h1>
  <p>Ask a public-service question and receive simple guidance in your preferred Indian language, grounded in a small verified project knowledge base.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="feature"><h3>🌐 Multilingual</h3><p>Generate simple responses in Hindi, English and selected Indian languages.</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="feature"><h3>🗂️ Grounded</h3><p>The AI receives local service data instead of answering only from general memory.</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="feature"><h3>🔐 Responsible</h3><p>No login, Aadhaar collection or storage of sensitive personal documents.</p></div>', unsafe_allow_html=True)

st.write("")
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Ask your question")
    examples = {
        "Scholarship": "What documents are normally required for a scholarship application?",
        "Certificates": "How can I apply for an income certificate?",
        "Pension": "What are the usual requirements for an old-age pension?",
        "Farmer Support": "What information is needed for PM-KISAN registration?",
        "All services": "Which public services are available in this project?",
    }
    question = st.text_area(
        "Public-service question",
        value=examples.get(selected_category, ""),
        height=145,
        placeholder="Example: Scholarship ke liye kaun se documents chahiye?",
    )
    generate = st.button("✨ Generate guidance", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Project scope")
    st.markdown("""
- Scholarship guidance
- Income and caste certificates
- Old-age pension guidance
- PM-KISAN basic guidance
- Simple multilingual explanations
    """)
    st.warning("Do not enter Aadhaar numbers, bank details, passwords, or other sensitive personal data.")
    st.markdown('</div>', unsafe_allow_html=True)

if generate:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        matched = matching_services(services, selected_category)
        try:
            with st.spinner("Preparing grounded multilingual guidance..."):
                answer = ask_gemini(
                    question.strip(),
                    LANGUAGES[selected_language],
                    selected_category,
                    matched,
                    selected_model,
                )
            st.session_state["last_answer"] = answer
            st.session_state["last_question"] = question.strip()
        except Exception as exc:
            st.error(str(exc))

if st.session_state.get("last_answer"):
    st.write("")
    st.subheader("AI guidance")
    with st.container(border=True):
        st.markdown(st.session_state["last_answer"])
    st.download_button(
        "⬇️ Download answer",
        data=(f"Question: {st.session_state.get('last_question', '')}\n\n"
              f"Answer:\n{st.session_state['last_answer']}\n\n"
              "Disclaimer: Verify the latest information on the official government portal."),
        file_name="bhashaseva_guidance.txt",
        mime="text/plain",
    )

st.markdown('<div class="footer">BhashaSeva AI • Educational minor project • Information must be verified on official government portals</div>', unsafe_allow_html=True)

