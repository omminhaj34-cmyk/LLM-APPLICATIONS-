import streamlit as st
import json
import tempfile
import datetime
import os
from parser import read_resume
from ats import analyze_resume
from gemini import client

st.set_page_config(page_title="ResumeAI", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# ---------- SESSION STATE INIT ----------
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "history" not in st.session_state:
    st.session_state.history = []

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    .stApp { background: #0d0e14; }
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent;
    }

    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0.5rem;
        border-bottom: 1px solid #23242f;
        margin-bottom: 2rem;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .topbar-left {
        display: flex;
        align-items: center;
        gap: 2.5rem;
    }
    .topbar-logo {
        font-size: 1.7rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .topbar-links {
        display: flex;
        gap: 2rem;
        color: #9ca3af;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .topbar-links span.active {
        color: #ffffff;
        border-bottom: 2px solid #ec4899;
        padding-bottom: 0.25rem;
    }
    .topbar-right {
        display: flex;
        align-items: center;
        gap: 1.3rem;
    }
    .topbar-icon {
        color: #9ca3af;
        font-size: 1.3rem;
        filter: grayscale(1) brightness(1.6);
        opacity: 0.85;
    }
    .upload-btn-top {
        background: linear-gradient(90deg, #a855f7, #ec4899);
        color: white;
        padding: 0.6rem 1.4rem;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.95rem;
    }

    .hero { text-align: center; padding: 1rem 0 2.5rem 0; }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero p { color: #9ca3af; font-size: 1.05rem; max-width: 600px; margin: 0 auto; }

    .card {
        background-color: #15161f;
        border: 1px solid #23242f;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }

    .score-row { display: flex; align-items: center; gap: 2rem; }
    .score-badge {
        display: inline-block;
        background: rgba(34,197,94,0.12);
        color: #22c55e;
        padding: 0.25rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .score-title { font-size: 1.8rem; font-weight: 800; color: #fff; margin: 0.2rem 0 0.5rem 0; }
    .score-desc { color: #c3c7d1; line-height: 1.7; font-size: 1.05rem; }

    .pill-strength {
        display: inline-block;
        background: rgba(34,197,94,0.1);
        border: 1px solid rgba(34,197,94,0.3);
        color: #4ade80;
        padding: 0.55rem 1.2rem;
        border-radius: 30px;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.4;
        margin: 0.35rem 0.4rem 0.35rem 0;
    }
    .pill-weakness {
        display: inline-block;
        background: rgba(244,63,94,0.1);
        border: 1px solid rgba(244,63,94,0.3);
        color: #fb7185;
        padding: 0.55rem 1.2rem;
        border-radius: 30px;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.4;
        margin: 0.35rem 0.4rem 0.35rem 0;
    }
    .cta-banner {
        position: relative;
        border-radius: 20px;
        overflow: hidden;
        padding: 3.5rem 2rem;
        text-align: center;
        margin: 2rem 0;
        background:
            linear-gradient(rgba(13,14,20,0.75), rgba(13,14,20,0.85)),
            linear-gradient(120deg, #1e1b3a 0%, #3b1d3f 50%, #1a1330 100%);
    }
    .cta-banner h3 {
        color: #fff;
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 0.6rem;
    }
    .cta-banner p {
        color: #c3c7d1 !important;
        font-size: 1.05rem !important;
        max-width: 500px;
        margin: 0 auto;
    }
    .section-heading {
        color: #fff;
        font-weight: 700;
        font-size: 1.4rem;
        margin-bottom: 1.1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .card p, .card li {
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
    }
    .score-title { font-size: 2rem !important; }
    .topbar-logo { font-size: 1.8rem !important; }

    section[data-testid="stSidebar"] {
        background-color: #0d0e14;
        border-right: 1px solid #23242f;
    }
    .sidebar-profile {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 1rem 0.5rem 1.5rem 0.5rem;
        border-bottom: 1px solid #23242f;
        margin-bottom: 1rem;
    }
    .sidebar-avatar {
        width: 42px; height: 42px; border-radius: 50%;
        background: linear-gradient(135deg, #a855f7, #ec4899);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem;
    }
    .sidebar-name { color: #fff; font-weight: 700; font-size: 0.95rem; }
    .sidebar-sub { color: #6b7280; font-size: 0.75rem; }

    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.4rem; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: transparent;
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
        width: 100%;
        transition: background-color 0.15s ease;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background-color: #1c1d28; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        font-size: 1.05rem !important;
        color: #d1d5db;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, #a855f7, #ec4899);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 700;
    }

    section[data-testid="stFileUploader"] {
        background-color: #15161f;
        border: 2px dashed #33343f;
        border-radius: 20px;
        padding: 2rem;
    }
    div.stProgress > div > div > div > div {
        background: linear-gradient(90deg, #a855f7, #ec4899);
    }

    /* general widget text sizing */
    .stMarkdown p, .stMarkdown li, .stCaption, div[data-testid="stCaptionContainer"] {
        font-size: 1.05rem !important;
    }
    .stButton button {
        font-size: 1.05rem !important;
        padding: 0.6rem 1.4rem !important;
        border-radius: 10px !important;
        background: linear-gradient(90deg, #a855f7, #ec4899) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton button:hover {
        opacity: 0.9;
    }
    /* popover trigger icons (bell/profile) stay plain, not gradient buttons */
    div[data-testid="stPopover"] > button {
        background: transparent !important;
        border: none !important;
        color: #9ca3af !important;
        font-size: 1.3rem !important;
        padding: 0.3rem 0.6rem !important;
        filter: grayscale(1) brightness(1.6);
        opacity: 0.85;
    }
    .stTextArea textarea {
        font-size: 1.05rem !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        font-size: 1.05rem !important;
    }
    div[data-testid="stAlert"] p {
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR NAV ----------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-profile">
        <div class="sidebar-avatar">🤖</div>
        <div>
            <div class="sidebar-name">AI Analyst</div>
            <div class="sidebar-sub">V2.4 Active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📊 Overview", "🔍 Deep Dive", "✨ Optimization", "💼 Job Match", "📈 Analysis", "⚙️ Settings"],
        label_visibility="collapsed",
        key="nav_page"
    )

# ---------- TOP BAR ----------
st.markdown('<div class="topbar-logo" style="padding-top:0.4rem;">ResumeAI</div>', unsafe_allow_html=True)
st.markdown('<hr style="border-color:#23242f; margin: 0.5rem 0 2rem 0;">', unsafe_allow_html=True)


def render_score_card(data):
    score = data['ats_score']
    score_color = "#22c55e" if score >= 75 else "#fbbf24" if score >= 50 else "#f43f5e"
    match_label = "Excellent Match" if score >= 75 else "Good Match" if score >= 50 else "Needs Work"
    radius = 54
    circumference = 2 * 3.14159 * radius
    offset = circumference - (score / 100) * circumference
    ring_svg = f"""
    <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="{radius}" fill="none" stroke="#23242f" stroke-width="12"/>
        <circle cx="70" cy="70" r="{radius}" fill="none" stroke="{score_color}" stroke-width="12"
            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            stroke-linecap="round" transform="rotate(-90 70 70)"/>
        <text x="70" y="80" text-anchor="middle" font-size="32" font-weight="800" fill="white">{score}</text>
    </svg>
    """
    st.markdown(f"""
    <div class="card">
        <div class="score-row">
            <div>{ring_svg}</div>
            <div>
                <div class="score-badge">✔ {match_label}</div>
                <div class="score-title">ATS Compatibility Score</div>
                <div class="score-desc">{data['summary']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        strengths_html = "".join([f'<span class="pill-strength">{s}</span>' for s in data['strengths']])
        st.markdown(f"""
        <div class="card">
            <div class="section-heading">👍 Strengths</div>
            {strengths_html}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        weaknesses_html = "".join([f'<span class="pill-weakness">{w}</span>' for w in data['weaknesses']])
        st.markdown(f"""
        <div class="card">
            <div class="section-heading">⚠️ Weaknesses</div>
            {weaknesses_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="cta-banner">
        <h3>Ready to land your dream job?</h3>
        <p>Our AI is processing thousands of job descriptions daily to keep your resume competitive.</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PAGE: OVERVIEW
# ============================================================
if page == "📊 Overview":
    st.markdown("""
    <div class="hero">
        <h1>AI Resume Analyzer</h1>
        <p>Optimize your career path with Gemini-powered insights. Get instant feedback
        on your resume's marketability and ATS compatibility.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        with st.spinner("🔍 Extracting text from resume..."):
            resume_text = read_resume(tmp_path)

        with st.spinner("🤖 Analyzing with Gemini AI..."):
            result = analyze_resume(resume_text)

        try:
            cleaned = result.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned)

            st.session_state.resume_text = resume_text
            st.session_state.analysis_data = data
            st.session_state.history.append({
                "filename": uploaded_file.name,
                "score": data['ats_score'],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })

            render_score_card(data)

        except json.JSONDecodeError:
            st.error("Couldn't parse AI response. Raw output:")
            st.code(result)

    elif st.session_state.analysis_data:
        st.info("Showing your last analyzed resume. Upload a new one to refresh.")
        render_score_card(st.session_state.analysis_data)


# ============================================================
# PAGE: DEEP DIVE
# ============================================================
elif page == "🔍 Deep Dive":
    st.markdown('<div class="hero"><h1>Deep Dive</h1><p>Section-by-section breakdown of your resume.</p></div>', unsafe_allow_html=True)

    if not st.session_state.resume_text:
        st.warning("Please upload a resume on the Overview page first.")
    else:
        if st.button("Run Deep Dive Analysis"):
            with st.spinner("🤖 Analyzing sections with Gemini..."):
                prompt = f"""
You are a resume section analyzer. Analyze the resume below and break it into these
sections: Summary, Experience, Skills, Education.

For each section, return a score (0-100) and 1-2 sentences of feedback.

Resume:
{st.session_state.resume_text}

Return ONLY JSON in this format:
{{
  "sections": [
    {{"name": "Summary", "score": 80, "feedback": "..."}},
    {{"name": "Experience", "score": 75, "feedback": "..."}},
    {{"name": "Skills", "score": 90, "feedback": "..."}},
    {{"name": "Education", "score": 70, "feedback": "..."}}
  ]
}}
No extra text, no markdown fences.
"""
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
                try:
                    cleaned = response.text.strip().replace("```json", "").replace("```", "")
                    sections_data = json.loads(cleaned)
                    st.session_state.deep_dive = sections_data
                except json.JSONDecodeError:
                    st.error("Couldn't parse response.")
                    st.code(response.text)

        if "deep_dive" in st.session_state:
            for sec in st.session_state.deep_dive["sections"]:
                color = "#22c55e" if sec["score"] >= 75 else "#fbbf24" if sec["score"] >= 50 else "#f43f5e"
                st.markdown(f"""
                <div class="card">
                    <div class="section-heading">{sec['name']} — <span style="color:{color}">{sec['score']}/100</span></div>
                    <p style="color:#9ca3af;">{sec['feedback']}</p>
                </div>
                """, unsafe_allow_html=True)


# ============================================================
# PAGE: OPTIMIZATION
# ============================================================
elif page == "✨ Optimization":
    st.markdown('<div class="hero"><h1>Optimization</h1><p>AI-rewritten bullet points to strengthen your resume.</p></div>', unsafe_allow_html=True)

    if not st.session_state.resume_text:
        st.warning("Please upload a resume on the Overview page first.")
    else:
        if st.button("Generate Improved Bullet Points"):
            with st.spinner("✨ Rewriting with Gemini..."):
                prompt = f"""
You are a resume writing expert. From the resume below, pick the 4 weakest bullet
points/lines describing experience or projects, and rewrite each into a stronger,
achievement-oriented, quantified version.

Resume:
{st.session_state.resume_text}

Return ONLY JSON in this format:
{{
  "rewrites": [
    {{"original": "...", "improved": "..."}}
  ]
}}
No extra text, no markdown fences.
"""
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
                try:
                    cleaned = response.text.strip().replace("```json", "").replace("```", "")
                    st.session_state.optimization = json.loads(cleaned)
                except json.JSONDecodeError:
                    st.error("Couldn't parse response.")
                    st.code(response.text)

        if "optimization" in st.session_state:
            for item in st.session_state.optimization["rewrites"]:
                st.markdown(f"""
                <div class="card">
                    <p style="color:#fb7185; margin-bottom:0.5rem;"><b>Before:</b> {item['original']}</p>
                    <p style="color:#4ade80;"><b>After:</b> {item['improved']}</p>
                </div>
                """, unsafe_allow_html=True)


# ============================================================
# PAGE: JOB MATCH
# ============================================================
elif page == "💼 Job Match":
    st.markdown('<div class="hero"><h1>Job Match</h1><p>Compare your resume against a job description.</p></div>', unsafe_allow_html=True)

    if not st.session_state.resume_text:
        st.warning("Please upload a resume on the Overview page first.")
    else:
        jd_text = st.text_area("Paste the job description here", height=200)
        if st.button("Compare"):
            with st.spinner("🤖 Comparing with Gemini..."):
                prompt = f"""
Compare the resume with the job description below.

Resume:
{st.session_state.resume_text}

Job Description:
{jd_text}

Return ONLY JSON in this format:
{{
  "match_score": 82,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "recommendation": "1-2 sentence recommendation"
}}
No extra text, no markdown fences.
"""
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
                try:
                    cleaned = response.text.strip().replace("```json", "").replace("```", "")
                    st.session_state.job_match = json.loads(cleaned)
                except json.JSONDecodeError:
                    st.error("Couldn't parse response.")
                    st.code(response.text)

        if "job_match" in st.session_state:
            jm = st.session_state.job_match
            st.markdown(f"""
            <div class="card">
                <div class="score-title">Match Score: {jm['match_score']}/100</div>
                <p style="color:#9ca3af;">{jm['recommendation']}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                matched_html = "".join([f'<span class="pill-strength">{s}</span>' for s in jm['matched_skills']])
                st.markdown(f'<div class="card"><div class="section-heading">✅ Matched Skills</div>{matched_html}</div>', unsafe_allow_html=True)
            with col2:
                missing_html = "".join([f'<span class="pill-weakness">{s}</span>' for s in jm['missing_skills']])
                st.markdown(f'<div class="card"><div class="section-heading">❌ Missing Skills</div>{missing_html}</div>', unsafe_allow_html=True)


# ============================================================
# PAGE: ANALYSIS
# ============================================================
elif page == "📈 Analysis":
    st.markdown('<div class="hero"><h1>Analysis</h1><p>Visual breakdown of your resume performance.</p></div>', unsafe_allow_html=True)

    if not st.session_state.analysis_data:
        st.warning("Please upload and analyze a resume on the Overview page first.")
    else:
        data = st.session_state.analysis_data

        st.markdown(f"""
        <div class="card">
            <div class="section-heading">📊 Overall ATS Score</div>
            <p style="color:#9ca3af;">Your resume currently scores <b style="color:#fff;">{data['ats_score']}/100</b>.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="section-heading">👍 Strength Count</div>
                <p style="color:#4ade80; font-size:2rem; font-weight:800;">{len(data['strengths'])}</p>
                <p style="color:#9ca3af;">Areas where your resume performs well.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="section-heading">⚠️ Weakness Count</div>
                <p style="color:#fb7185; font-size:2rem; font-weight:800;">{len(data['weaknesses'])}</p>
                <p style="color:#9ca3af;">Areas that could use improvement.</p>
            </div>
            """, unsafe_allow_html=True)

        if "deep_dive" in st.session_state:
            st.markdown('<div class="section-heading" style="margin-top:1rem;">📐 Section Scores</div>', unsafe_allow_html=True)
            chart_data = {sec["name"]: sec["score"] for sec in st.session_state.deep_dive["sections"]}
            st.bar_chart(chart_data)
        else:
            st.info("Run **Deep Dive** first to see a section-by-section score chart here.")

        if len(st.session_state.history) > 1:
            st.markdown('<div class="section-heading" style="margin-top:1rem;">📈 Score History (this session)</div>', unsafe_allow_html=True)
            history_chart = {f"{i+1}. {e['filename'][:15]}": e["score"] for i, e in enumerate(st.session_state.history)}
            st.bar_chart(history_chart)


# ============================================================
# PAGE: SETTINGS
# ============================================================
elif page == "⚙️ Settings":
    st.markdown('<div class="hero"><h1>Settings</h1><p>App configuration and status.</p></div>', unsafe_allow_html=True)

    import os
    key_status = "✅ Loaded" if os.getenv("GEMINI_API_KEY") else "❌ Not found"

    st.markdown(f"""
    <div class="card">
        <div class="section-heading">🔑 API Key Status</div>
        <p style="color:#9ca3af;">Gemini API Key: {key_status}</p>
    </div>
    <div class="card">
        <div class="section-heading">ℹ️ App Info</div>
        <p style="color:#9ca3af;">ResumeAI Analyzer • v2.4.0<br>Model: gemini-2.5-flash-lite</p>
    </div>
    """, unsafe_allow_html=True)


# ---------- FOOTER ----------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;
            color:#6b7280; padding: 2rem 0.5rem; border-top: 1px solid #23242f; margin-top: 2rem;">
    <div>
        <b style="background: linear-gradient(90deg, #a855f7, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size:1.05rem;">ResumeAI</b>
        <div style="font-size:0.85rem; color:#6b7280;">© 2026 ResumeAI Analyzer • v2.4.0</div>
    </div>
    <div style="display:flex; gap:2rem; font-size:0.95rem; color:#9ca3af;">
        <span>Terms of Service</span>
        <span>Privacy Policy</span>
        <span>Built with Streamlit</span>
    </div>
</div>
""", unsafe_allow_html=True)