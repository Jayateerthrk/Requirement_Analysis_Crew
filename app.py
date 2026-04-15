"""
app.py — Streamlit UI for the TPM Requirements Crew.
Run locally : streamlit run app.py
Deploy      : push to GitHub → connect to streamlit.io
"""

import os
import json
import tempfile
import time
from datetime import datetime

import streamlit as st

from schema import Story
from crew import run_requirements_crew
from pdf_parser import parse_stories_from_pdf, stories_to_preview_text
from html_reporter import generate_story_card, generate_sprint_summary_table


# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TPM Requirements Crew",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── API key — works locally (.env) and on Streamlit Cloud (secrets) ──────────

def load_api_key():
    # Streamlit Cloud stores secrets in st.secrets
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
        return True

    # Check for Hugging Face
    if "HUGGINGFACE_API_KEY" in st.secrets:
        os.environ["HUGGINGFACE_API_KEY"] = st.secrets["HUGGINGFACE_API_KEY"]
        keys_found.append("Hugging Face")
    elif os.getenv("HUGGINGFACE_API_KEY"):
        keys_found.append("Hugging Face")
        
    # Local — loaded from .env by crew.py via dotenv
    if os.getenv("GROQ_API_KEY"):
        return True
    return False


# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  .main { padding-top: 1rem; }
  .stAlert { border-radius: 8px; }
  div[data-testid="stExpander"] {
    border: 1px solid #dde3ec;
    border-radius: 8px;
    margin-bottom: 12px;
  }
  .metric-row {
    display: flex; gap: 12px; flex-wrap: wrap; margin: 8px 0;
  }
  .metric-pill {
    padding: 4px 12px; border-radius: 6px;
    font-size: 13px; font-weight: 600;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("TPM Requirements Crew")
    st.caption("AI-powered sprint readiness analysis")
    st.caption("**Developer: Jayateerth Katti**")

    st.divider()

    st.markdown("**How it works**")
    st.markdown("""
1. Upload a PDF of user stories  
   **or** paste stories as text
2. Preview parsed stories
3. Click **Run Analysis**
4. Review report per story
5. Download JSON or HTML
    """)

    st.divider()
    st.markdown("**Agents inside the crew**")
    st.markdown("""
- Ambiguity analyst  
- Risk assessor  
- DoR evaluator  
- Manager (synthesiser)
    """)

    st.divider()
    st.markdown("**Stack**")
    st.caption("CrewAI · Groq · Llama 3.3 70B · Python 3.13")


# ── Main ──────────────────────────────────────────────────────────────────────

st.title("📋 TPM Requirements Crew")
st.markdown(
    "Analyse user stories for **ambiguity**, **risk**, and "
    "**Definition of Ready** before sprint planning."
)

# API key check
if not load_api_key():
    st.error(
        "Groq API key not found. "
        "Add GROQ_API_KEY to your .env file (local) "
        "or Streamlit secrets (cloud)."
    )
    st.stop()

st.divider()


# ── Input tabs ────────────────────────────────────────────────────────────────

tab_pdf, tab_paste = st.tabs(["Upload PDF", "Paste Text"])

stories: list[Story] = []

# --- PDF upload tab ---
with tab_pdf:
    st.markdown("Upload a PDF containing one or more user stories.")
    st.markdown(
        "Stories can be in labelled format (Story ID / Title / Description / AC) "
        "or separated by blank lines. "
        "[See sample format](#) in the instructions."
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="PDF should contain user stories. Max ~50 stories per run."
    )

    if uploaded_file:
        with st.spinner("Reading PDF..."):
            try:
                # Save to temp file — pdfplumber needs a file path or seekable stream
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                pdf_stories = parse_stories_from_pdf(tmp_path)
                os.unlink(tmp_path)

                if pdf_stories:
                    st.success(f"Parsed {len(pdf_stories)} story/stories from PDF.")
                    with st.expander("Preview parsed stories", expanded=False):
                        st.text(stories_to_preview_text(pdf_stories))
                    stories = pdf_stories
                else:
                    st.warning(
                        "No stories could be parsed from this PDF. "
                        "Try the Paste Text tab instead."
                    )
            except Exception as e:
                st.error(f"Could not read PDF: {e}")

# --- Paste text tab ---
with tab_paste:
    st.markdown(
        "Paste one or more stories. Use this format — "
        "one story per block, separate multiple stories with `---`"
    )

    sample = """Story ID    : PROJ-101
Title       : User login with social auth
Description : As a user I want to quickly login using my social media
              account so that I can easily access the platform.
AC          : Login should work fast
AC          : User should see their profile after login
Points      : 3
Sprint      : Sprint 1"""

    paste_input = st.text_area(
        "Paste stories here",
        height=280,
        placeholder=sample,
    )

    if paste_input.strip():
        # Parse pasted text as stories — reuse block splitter
        from pdf_parser import _split_into_blocks, _parse_block
        blocks = _split_into_blocks(paste_input)
        paste_stories = [
            _parse_block(b, i)
            for i, b in enumerate(blocks)
            if len(b.strip()) > 20
        ]
        if paste_stories:
            st.success(f"Parsed {len(paste_stories)} story/stories.")
            with st.expander("Preview parsed stories", expanded=False):
                st.text(stories_to_preview_text(paste_stories))
            stories = paste_stories


# ── Run analysis ──────────────────────────────────────────────────────────────

st.divider()

if not stories:
    st.info("Upload a PDF or paste stories above to begin.")
    st.stop()

sprint_name = st.text_input(
    "Sprint name (used for report filenames)",
    value="sprint",
    max_chars=40,
)

col1, col2 = st.columns([2, 5])
with col1:
    run_button = st.button(
        "Run Analysis",
        type="primary",
        use_container_width=True,
        disabled=len(stories) == 0,
    )

with col2:
    st.caption(
        f"{len(stories)} story/stories ready · "
        f"~{len(stories) * 45} seconds estimated"
    )

if not run_button:
    st.stop()


# ── Run crew ──────────────────────────────────────────────────────────────────

reports = []
progress = st.progress(0, text="Starting crew...")
status   = st.empty()

for i, story in enumerate(stories):
    status.markdown(
        f"Analysing **{story.story_id}** — {story.title} "
        f"({i+1}/{len(stories)})"
    )
    try:
        report = run_requirements_crew(story)
        reports.append(report)
    except Exception as e:
        st.error(f"Failed on {story.story_id}: {e}")

    progress.progress(
        (i + 1) / len(stories),
        text=f"Completed {i+1} of {len(stories)}"
    )
    time.sleep(15)  # Delay to avoid rate limiting

progress.empty()
status.empty()

if not reports:
    st.error("All stories failed to analyse. Check your API key and try again.")
    st.stop()

st.success(f"Analysis complete — {len(reports)} story/stories analysed.")
st.divider()


# ── Results ───────────────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "READY":               "✅",
    "CONDITIONALLY_READY": "⚠️",
    "NOT_READY":           "❌",
}

RISK_COLOUR = {
    "HIGH":   "🔴",
    "MEDIUM": "🟡",
    "LOW":    "🟢",
}

# Sprint summary (batch)
if len(reports) > 1:
    st.subheader("Sprint Summary")
    total     = len(reports)
    ready     = sum(1 for r in reports if r.get("dor_status") == "READY")
    not_ready = sum(1 for r in reports if r.get("dor_status") == "NOT_READY")
    cond      = total - ready - not_ready

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Stories",  total)
    m2.metric("Ready",          ready,     delta=None)
    m3.metric("Conditional",    cond,      delta=None)
    m4.metric("Not Ready",      not_ready, delta=None)

    st.divider()

# Individual story results
st.subheader("Story Reports")

for report in reports:
    story_id  = report.get("story_id", "Unknown")
    title     = report.get("title", "")
    status    = report.get("dor_status", "UNKNOWN")
    readiness = report.get("readiness_score", 0)
    risk      = report.get("overall_risk_level", "UNKNOWN")
    ambiguity = report.get("ambiguity_score", 0)

    status_emoji = STATUS_EMOJI.get(status, "❓")
    risk_emoji   = RISK_COLOUR.get(risk, "⚪")

    expander_label = (
        f"{status_emoji} {story_id} — {title} "
        f"| Readiness: {readiness}/100 "
        f"| Risk: {risk_emoji} {risk}"
    )

    with st.expander(expander_label, expanded=(status != "READY")):

        # Score metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DoR Status",      status)
        c2.metric("Readiness Score", f"{readiness}/100")
        c3.metric("Risk Level",      risk)
        c4.metric("Ambiguity Score", f"{ambiguity}/100")

        # Key blockers
        blockers = report.get("key_blockers", [])
        if blockers:
            st.markdown("**Key Blockers**")
            for b in blockers:
                st.error(f"✗ {b}", icon=None)

        # Key risks
        risks = report.get("key_risks", [])
        if risks:
            st.markdown("**Key Risks**")
            for r in risks:
                st.warning(f"⚠ {r}", icon=None)

        # Immediate actions
        actions = report.get("immediate_actions", [])
        if actions:
            st.markdown("**Immediate Actions**")
            for a in actions:
                st.info(f"→ {a}", icon=None)

        # TPM summary
        summary = report.get("tpm_summary", "")
        if summary:
            st.markdown("**TPM Summary**")
            st.markdown(
                f'<div style="background:#f7f9fc;padding:14px;'
                f'border-radius:8px;border:1px solid #dde3ec;'
                f'line-height:1.6;">{summary}</div>',
                unsafe_allow_html=True,
            )


# ── Downloads ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Download Reports")

timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
json_bytes = json.dumps(reports, indent=2).encode("utf-8")

# Build HTML content for download
from html_reporter import save_html_report
import io

os.makedirs("output", exist_ok=True)
html_path = save_html_report(reports, sprint_name, timestamp)
with open(html_path, "r", encoding="utf-8") as f:
    html_bytes = f.read().encode("utf-8")

dl1, dl2 = st.columns(2)

with dl1:
    st.download_button(
        label="Download JSON",
        data=json_bytes,
        file_name=f"{sprint_name}_{timestamp}.json",
        mime="application/json",
        use_container_width=True,
    )

with dl2:
    st.download_button(
        label="Download HTML Report",
        data=html_bytes,
        file_name=f"{sprint_name}_{timestamp}.html",
        mime="text/html",
        use_container_width=True,
    )

st.caption(
    "HTML report can be opened in any browser. "
    "JSON can be used as input for the next crew."
)