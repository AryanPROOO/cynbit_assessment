"""
BitElevate Skill Gap Analyzer - Streamlit Application
Author: Cynbit AI Team
Description: Modern, interactive frontend interface for Cynbit Studio's BitElevate
             automated career mapping and skill gap assessment platform.
"""

import os
import sys
import json
import io
import requests
import streamlit as st
from pathlib import Path

# Add backend to path for direct engine fallback
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "backend") not in sys.path:
    sys.path.insert(0, str(root_dir / "backend"))

try:
    from backend.nlp_engine import NLPEngine
    LOCAL_ENGINE_AVAILABLE = True
except Exception:
    LOCAL_ENGINE_AVAILABLE = False

# Backend API Configuration
DEFAULT_API_URL = os.getenv("BITELEVATE_API_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Cynbit Studio - BitElevate Skill Gap Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System (CSS)
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Gradient Header */
    .brand-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #312E81 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    }
    
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF 0%, #E0E7FF 40%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .brand-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Metric Cards */
    .metric-card {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        font-weight: 600;
    }

    /* Pill Badges */
    .skill-pill {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.88rem;
        font-weight: 600;
        margin: 4px 4px 4px 0;
        transition: all 0.15s ease-in-out;
    }
    .skill-pill-matched {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .skill-pill-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .skill-pill-additional {
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }

    /* Roadmap Card */
    .roadmap-card {
        background: #0F172A;
        border-left: 4px solid #6366F1;
        border-top: 1px solid rgba(255,255,255,0.06);
        border-right: 1px solid rgba(255,255,255,0.06);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .roadmap-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .roadmap-badge {
        display: inline-block;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-advanced { background: #7C2D12; color: #FDBA74; }
    .badge-intermediate { background: #1E3A8A; color: #93C5FD; }
    .badge-beginner { background: #064E3B; color: #6EE7B7; }

    .cynbit-course-tag {
        color: #A5B4FC;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)


# Helper Functions
@st.cache_resource
def get_local_engine():
    """Initializes local NLP engine for standalone mode."""
    if LOCAL_ENGINE_AVAILABLE:
        db_path = str(root_dir / "backend" / "role_database.json")
        return NLPEngine(db_path)
    return None


def check_api_status(api_url: str) -> bool:
    """Checks if FastAPI backend server is reachable."""
    try:
        r = requests.get(f"{api_url}/", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def fetch_roles_from_api(api_url: str) -> list:
    """Fetches role list from backend or falls back to local engine."""
    try:
        r = requests.get(f"{api_url}/roles", timeout=2.0)
        if r.status_code == 200:
            return r.json().get("roles", [])
    except Exception:
        pass

    engine = get_local_engine()
    if engine:
        return engine.get_available_roles()
    return []


def analyze_via_api(api_url: str, file_bytes: bytes, filename: str, target_role: str) -> dict:
    """Sends file to FastAPI backend /analyze-gap endpoint."""
    files = {"file": (filename, file_bytes, "application/pdf")}
    data = {"target_role": target_role}
    response = requests.post(f"{api_url}/analyze-gap", files=files, data=data, timeout=15.0)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error ({response.status_code}): {response.text}")


def analyze_locally(file_bytes: bytes, filename: str, target_role: str) -> dict:
    """Direct analysis using in-process NLPEngine."""
    engine = get_local_engine()
    if not engine:
        raise Exception("NLP Engine could not be loaded locally.")
    text = engine.extract_text_from_pdf(file_bytes)
    if not text:
        raise Exception("Could not extract text from document.")
    result = engine.analyze_skill_gap(text, target_role)
    result["filename"] = filename
    return result


# Top Branding Header
st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 class="brand-title">Cynbit Studio - BitElevate Skill Gap Analyzer</h1>
            <p class="brand-subtitle">AI-Powered Autonomous Resume Assessment, Role Benchmark & Upskilling Roadmap</p>
        </div>
        <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 10px; padding: 10px 16px; text-align: right;">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Platform</div>
            <div style="font-size: 1.1rem; color: #FFFFFF; font-weight: 700;">BitElevate AI</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Sidebar Configuration
st.sidebar.markdown("### ⚙️ System Controls")

api_url = st.sidebar.text_input("FastAPI Backend URL", value=DEFAULT_API_URL)
api_connected = check_api_status(api_url)

if api_connected:
    st.sidebar.success("🟢 FastAPI Backend: Connected")
else:
    st.sidebar.warning("🟡 FastAPI Offline: Using Local NLP Engine")

# Fetch available roles
roles_list = fetch_roles_from_api(api_url)
role_options = [r["title"] for r in roles_list] if roles_list else ["AI Engineer", "Data Analyst"]

selected_role_name = st.sidebar.selectbox(
    "🎯 Select Target Dream Role",
    options=role_options,
    index=0,
    help="Select the target career path to compare the candidate's profile against."
)

# Display Target Role Specs in Sidebar
selected_role_meta = next((r for r in roles_list if r["title"] == selected_role_name), None)
if selected_role_meta:
    st.sidebar.markdown(f"**Category:** `{selected_role_meta.get('category', 'Technology')}`")
    st.sidebar.caption(selected_role_meta.get("description", ""))
    with st.sidebar.expander("📋 Required Role Skills Benchmark", expanded=False):
        for sk in selected_role_meta.get("required_skills", []):
            st.markdown(f"- **{sk}**")

# Main Workspace Layout
col1, col2 = st.columns([1.1, 0.9])

uploaded_file_bytes = None
uploaded_filename = None

with col1:
    st.markdown("#### 1. Upload Candidate Resume")
    uploaded_file = st.file_uploader(
        "Upload candidate resume in PDF format",
        type=["pdf", "txt"],
        help="Upload candidate PDF resume. BitElevate extracts text, parses skills and cross-evaluates against the target benchmark."
    )

    if uploaded_file is not None:
        uploaded_file_bytes = uploaded_file.read()
        uploaded_filename = uploaded_file.name
        st.success(f"Loaded: `{uploaded_filename}` ({len(uploaded_file_bytes):,} bytes)")

with col2:
    st.markdown("#### 2. Run Assessment")
    st.markdown("""
    The NLP Engine will perform:
    - PDF text stream extraction & section cleansing
    - Canonical skill entity recognition & alias resolution
    - Mathematical set difference gap formulation (`Required - Resume`)
    - BitElevate customized module and course recommendations
    """)
    
    analyze_btn = st.button("🚀 Analyze Skill Gap Now", type="primary", use_container_width=True)

st.markdown("---")

# Execution & Results Handling
if analyze_btn:
    if not uploaded_file_bytes:
        st.error("Please upload a candidate resume in PDF or TXT format first.")
    else:
        with st.spinner(f"Analyzing resume against '{selected_role_name}' requirements..."):
            result = None
            try:
                if api_connected:
                    result = analyze_via_api(api_url, uploaded_file_bytes, uploaded_filename, selected_role_name)
                else:
                    result = analyze_locally(uploaded_file_bytes, uploaded_filename, selected_role_name)
            except Exception as e:
                # If API attempt failed, fallback to local
                try:
                    result = analyze_locally(uploaded_file_bytes, uploaded_filename, selected_role_name)
                    st.warning("FastAPI endpoint had an issue; successfully evaluated using local NLP fallback.")
                except Exception as local_err:
                    st.error(f"Analysis failed: {str(e)} | Local fallback error: {str(local_err)}")

            if result:
                st.session_state["analysis_result"] = result

# Display Results if present in session state
if "analysis_result" in st.session_state:
    res = st.session_state["analysis_result"]
    metrics = res.get("metrics", {})
    candidate = res.get("candidate_metadata", {})
    skills = res.get("skills_breakdown", {})
    recs = res.get("recommendations", {})
    target_role_info = res.get("target_role", {})

    match_pct = metrics.get("match_percentage", 0.0)
    readiness = metrics.get("readiness_level", "Unknown")

    # Candidate Summary Banner
    st.markdown(f"""
    <div style="background: #1E293B; border-radius: 12px; padding: 18px 24px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(255,255,255,0.08);">
        <div>
            <div style="font-size: 0.85rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Candidate Assessment Overview</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #F8FAFC;">{candidate.get('name', 'Candidate')}</div>
            <div style="color: #64748B; font-size: 0.9rem;">Email: {candidate.get('email') or 'N/A'} | Target Role: <span style="color: #818CF8; font-weight: 600;">{target_role_info.get('title', selected_role_name)}</span></div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Readiness Verdict</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: {'#10B981' if match_pct >= 80 else '#F59E0B' if match_pct >= 50 else '#EF4444'};">{readiness}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3 High-Impact Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Role Match Score</div>
            <div class="metric-value" style="color: {'#10B981' if match_pct >= 80 else '#F59E0B' if match_pct >= 50 else '#EF4444'};">{match_pct}%</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Benchmark Alignment</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Matched Skills</div>
            <div class="metric-value" style="color: #10B981;">{metrics.get('matched_count', 0)} / {metrics.get('total_required', 0)}</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Mandatory Skills Met</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Missing Skills</div>
            <div class="metric-value" style="color: #EF4444;">{metrics.get('missing_count', 0)}</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Skill Gap Deficit</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Est. Upskilling Time</div>
            <div class="metric-value" style="color: #818CF8;">{metrics.get('estimated_upskill_weeks', 0)} Wks</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">To Reach Full Readiness</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visual Progress Bar
    st.markdown("**Role Competency Progress Bar**")
    st.progress(float(match_pct) / 100.0)

    # Visual Skill Breakdown Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Skill Gap Matrix", 
        "🚀 BitElevate Personalized Learning Roadmap", 
        "📑 Candidate Extracted Details", 
        "💾 Export Report"
    ])

    with tab1:
        st.markdown("### Technical Competencies Breakdown")
        col_matched, col_missing = st.columns(2)

        with col_matched:
            st.markdown(f"#### ✅ Matched Skills ({len(skills.get('matched_skills', []))})")
            if skills.get("matched_skills"):
                matched_html = "".join([f'<span class="skill-pill skill-pill-matched">✓ {s}</span>' for s in skills["matched_skills"]])
                st.markdown(matched_html, unsafe_allow_html=True)
            else:
                st.info("No mandatory skills matched for this benchmark.")

        with col_missing:
            st.markdown(f"#### ⚠️ Missing Skills (Skill Gap) ({len(skills.get('missing_skills', []))})")
            if skills.get("missing_skills"):
                missing_html = "".join([f'<span class="skill-pill skill-pill-missing">✗ {s}</span>' for s in skills["missing_skills"]])
                st.markdown(missing_html, unsafe_allow_html=True)
            else:
                st.success("🎉 Zero skill gap! All required skills matched.")

        st.markdown("---")
        st.markdown(f"#### 🌟 Bonus / Additional Candidate Skills ({len(skills.get('additional_skills', []))})")
        st.caption("Skills found in the resume that exceed the core target role requirements:")
        if skills.get("additional_skills"):
            additional_html = "".join([f'<span class="skill-pill skill-pill-additional">+ {s}</span>' for s in skills["additional_skills"]])
            st.markdown(additional_html, unsafe_allow_html=True)
        else:
            st.caption("No additional unlisted technical skills detected.")

    with tab2:
        st.markdown("### BitElevate Personalized Career & Upskilling Roadmap")
        st.write(recs.get("verdict", ""))

        learning_path = recs.get("learning_path", [])
        if learning_path:
            st.markdown(f"**Recommended Step-by-Step Learning Sprint ({metrics.get('estimated_upskill_weeks', 0)} Weeks Total):**")
            for idx, item in enumerate(learning_path, 1):
                difficulty = item.get("difficulty", "Intermediate")
                badge_class = f"badge-{difficulty.lower()}"
                st.markdown(f"""
                <div class="roadmap-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="roadmap-title">{idx}. Master {item.get('skill')}: {item.get('module_title')}</span>
                        <span class="roadmap-badge {badge_class}">{difficulty} • {item.get('estimated_weeks', 2)} Wks</span>
                    </div>
                    <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 6px;">{item.get('description')}</div>
                    <div class="cynbit-course-tag">🎓 Recommended Cynbit Program: <u>{item.get('recommended_cynbit_course')}</u></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Candidate already satisfies all target competencies! No remediation required.")

        # Capstone Project
        capstone = recs.get("recommended_capstone") or target_role_info.get("capstone_project")
        if capstone:
            st.markdown("#### 🏆 Recommended Portfolio Capstone Project")
            st.info(f"💡 **{capstone}**\n\n*Building and open-sourcing this project on GitHub provides verifiable proof-of-work to hiring managers.*")

    with tab3:
        st.markdown("### Parsed Text & Extraction Diagnostics")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write(f"**Extracted Candidate Name:** `{candidate.get('name')}`")
            st.write(f"**Extracted Email:** `{candidate.get('email')}`")
            st.write(f"**Extracted Phone:** `{candidate.get('phone')}`")
            st.write(f"**Source Document:** `{res.get('filename')}`")
        with col_d2:
            st.write(f"**Total Character Count:** `{res.get('raw_text_length')}`")
            st.write(f"**Total Skills Identified:** `{len(skills.get('all_extracted_skills', []))}`")

        with st.expander("📄 View Normalized Resume Text Preview", expanded=False):
            st.text(res.get("text_preview", "No preview available."))

    with tab4:
        st.markdown("### Export Assessment Report")
        st.write("Download the complete assessment output for HR integration, BitElevate CRM, or student career counseling:")
        
        json_output = json.dumps(res, indent=2)
        st.download_button(
            label="📥 Download JSON Report",
            data=json_output,
            file_name=f"BitElevate_Report_{candidate.get('name', 'Candidate').replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.85rem; padding-bottom: 20px;">
    <strong>Cynbit Studio - BitElevate Skill Gap Analyzer</strong> • Engineered with FastAPI, spaCy & Streamlit<br>
    Empowering Automated Career Mapping & Intelligent Student Upskilling
</div>
""", unsafe_allow_html=True)
