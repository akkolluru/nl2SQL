# streamlit_app.py
import time
import json
import requests
import pandas as pd
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="NL to SQL — Multilingual", layout="wide")

st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
    .stTextInput>div>div>input {font-size: 16px; height: 46px;}
    .small-muted {color:#6b7280; font-size:13px;}
    .section-title {font-weight:600; font-size: 18px; margin-top: 1rem;}
    .codebox {border:1px solid #e5e7eb; border-radius:6px; padding:10px; background:#fafafa;}
    .hr {border-top:1px solid #e5e7eb; margin: 20px 0;}
    .lang-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-left: 8px;
    }
    .lang-en { background:#dbeafe; color:#1d4ed8; }
    .lang-hi { background:#fef3c7; color:#92400e; }
    .lang-te { background:#d1fae5; color:#065f46; }
    </style>
""", unsafe_allow_html=True)

# ---------- Language config ----------
LANGUAGE_OPTIONS = {
    "English": "en",
    "हिंदी (Hindi)": "hi",
    "తెలుగు (Telugu)": "te",
}
LANG_BADGE_CLASS = {"en": "lang-en", "hi": "lang-hi", "te": "lang-te"}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API base URL", value="http://127.0.0.1:8000")

    st.markdown("---")
    st.subheader("Language")
    selected_lang_label = st.radio(
        "Input language",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=0,
        help="Choose the language your question is written in.",
    )
    selected_lang_code = LANGUAGE_OPTIONS[selected_lang_label]

    st.markdown("---")
    show_sql = st.checkbox("Show generated SQL", value=True)
    enable_csv = st.checkbox("Enable CSV download", value=True)
    st.markdown(
        "<div class='small-muted'>Run backend: "
        "<code>uvicorn app.main:app --reload</code></div>",
        unsafe_allow_html=True,
    )

# ---------- Session state ----------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Header ----------
st.title("Natural Language → SQL")
st.markdown(
    "<div class='small-muted'>Type a question in English, Hindi, or Telugu. "
    "The system will generate SQL, validate it, and run it on a read-only MySQL database.</div>",
    unsafe_allow_html=True,
)

# ---------- Input ----------
col_q, col_btn = st.columns([4, 1])

PLACEHOLDERS = {
    "en": "e.g., Show total orders per city",
    "hi": "e.g., शहर के अनुसार कुल ऑर्डर दिखाओ",
    "te": "e.g., నగరం వారీగా మొత్తం ఆర్డర్లు చూపించు",
}

with col_q:
    question = st.text_input(
        "Question",
        value="",
        placeholder=PLACEHOLDERS[selected_lang_code],
    )
with col_btn:
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    run_clicked = st.button("Run ▶", type="primary", use_container_width=True)


# ---------- Backend call ----------
def call_backend(api: str, q: str, lang: str):
    t0 = time.perf_counter()
    url = api.rstrip("/") + "/query"
    try:
        r = requests.post(
            url,
            json={"question": q.strip(), "language": lang},
            timeout=60,
        )
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            data = r.json()
            cols = data.get("columns", [])
            rows = data.get("rows", [])
            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
            return True, data.get("sql", ""), df, elapsed_ms, None, data.get("language", lang)
        else:
            try:
                detail = r.json().get("detail")
            except Exception:
                detail = r.text
            return False, "", pd.DataFrame(), elapsed_ms, detail, lang
    except requests.exceptions.RequestException as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return False, "", pd.DataFrame(), elapsed_ms, str(e), lang


# ---------- Execute ----------
if run_clicked and question.strip():
    with st.spinner("Generating SQL…"):
        ok, sql, df, ms, err, lang_used = call_backend(api_url, question, selected_lang_code)

    st.session_state.history.insert(0, {
        "question": question,
        "sql": sql,
        "df": df,
        "ms": ms,
        "ok": ok,
        "error": err,
        "language": lang_used,
    })

elif run_clicked and not question.strip():
    st.warning("Please enter a question first.")


# ---------- Helper: language badge ----------
def lang_badge(lang_code: str) -> str:
    cls = LANG_BADGE_CLASS.get(lang_code, "lang-en")
    labels = {"en": "EN", "hi": "हि", "te": "తె"}
    return f"<span class='lang-badge {cls}'>{labels.get(lang_code, lang_code.upper())}</span>"


# ---------- Latest result ----------
if st.session_state.history:
    latest = st.session_state.history[0]

    st.subheader("Result")
    badge = lang_badge(latest["language"])

    if latest["ok"]:
        st.markdown(
            f"<div class='small-muted'>Completed in {latest['ms']} ms {badge}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='small-muted'>Request finished in {latest['ms']} ms {badge}</div>",
            unsafe_allow_html=True,
        )

    if latest["ok"] and show_sql:
        st.markdown("<div class='section-title'>Generated SQL</div>", unsafe_allow_html=True)
        st.code(latest["sql"], language="sql")

    if latest["ok"]:
        if latest["df"].empty:
            st.info("No rows returned.")
        else:
            st.dataframe(latest["df"], use_container_width=True, height=420)
            if enable_csv:
                csv = latest["df"].to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Download CSV", data=csv, file_name="result.csv", mime="text/csv")
    else:
        st.error("The request did not succeed.")
        st.markdown("<div class='section-title'>Details</div>", unsafe_allow_html=True)
        if isinstance(latest["error"], (dict, list)):
            st.code(json.dumps(latest["error"], indent=2))
        else:
            st.code(str(latest["error"]))

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)


# ---------- History ----------
st.subheader("History")
if not st.session_state.history:
    st.markdown(
        "<div class='small-muted'>Your recent queries will appear here.</div>",
        unsafe_allow_html=True,
    )
else:
    for i, item in enumerate(st.session_state.history):
        badge = lang_badge(item["language"])
        label = f"{i+1}. {item['question']}  •  {item['ms']} ms"
        with st.expander(label):
            st.markdown(badge, unsafe_allow_html=True)
            if item["ok"] and show_sql:
                st.markdown("<div class='section-title'>Generated SQL</div>", unsafe_allow_html=True)
                st.code(item["sql"], language="sql")
            if item["ok"] and not item["df"].empty:
                st.dataframe(item["df"], use_container_width=True, height=260)
            if not item["ok"]:
                st.markdown("<div class='section-title'>Error</div>", unsafe_allow_html=True)
                if isinstance(item["error"], (dict, list)):
                    st.code(json.dumps(item["error"], indent=2))
                else:
                    st.code(str(item["error"]))