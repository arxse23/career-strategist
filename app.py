import streamlit as st
import anthropic
import os

# -----------------------------
# 1. PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Career Change Strategist",
    page_icon="🎯",
    layout="wide"
)

# -----------------------------
# 2. HIDE STREAMLIT BRANDING + CASE-FILE STYLING
# -----------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Paper grain — same trick as the landing page, no external image needed */
.stApp {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/></svg>");
    background-repeat: repeat;
}

/* Case-file header block */
.cf-eyebrow {
    font-family: 'FiraCode', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #B03A2E;
    margin-bottom: 0.35rem;
}
.cf-title-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.2rem; }
.cf-title {
    font-family: 'DMSans', sans-serif;
    font-weight: 700;
    letter-spacing: -0.01em;
    text-transform: uppercase;
    font-size: 2.1rem;
    color: #20242B;
    margin: 0;
}
.cf-subtitle { font-size: 1rem; color: #4A4535; margin-top: 0.3rem; margin-bottom: 1.2rem; }
.cf-hr { border: none; border-top: 1px solid #A79B7A; margin: 1.4rem 0; }

/* Sidebar section labels */
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    font-family: 'FiraCode', monospace !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* Buttons — "double stamp impression" outline, same motif as the landing page */
.stButton > button, [data-testid="stButton"] button,
.stDownloadButton > button, [data-testid="stDownloadButton"] button {
    position: relative;
    font-family: 'DMSans', sans-serif;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    font-size: 0.85rem;
    border-width: 1.5px !important;
}
.stButton > button[kind="primary"], [data-testid="stButton"] button[kind="primary"] {
    box-shadow: -4px 4px 0 0 rgba(176, 58, 46, 0.35);
}
.stButton > button[kind="primary"]:hover, [data-testid="stButton"] button[kind="primary"]:hover {
    box-shadow: -2px 2px 0 0 rgba(176, 58, 46, 0.35);
    transform: translate(-2px, 2px);
}

/* Alerts (free-plan counter / paywall) — force off Streamlit's default blue/grey onto the kraft tone */
div[data-testid="stAlert"],
div[data-testid="stAlert"] > div {
    background-color: #E3D6AF !important;
    border-radius: 0.15rem !important;
    border: 1px solid #8A7C55 !important;
    border-left: 4px solid #B03A2E !important;
}
div[data-testid="stAlert"] * {
    color: #20242B !important;
    fill: #20242B !important;
}

/* Text areas / inputs / selects — same tone as the page, but bordered so fields are still legible */
.stTextArea textarea, .stTextInput input, div[data-baseweb="select"] {
    background-color: #E3D6AF !important;
    border: 1.5px solid #8A7C55 !important;
    border-radius: 0.15rem !important;
}
textarea:focus, input:focus {
    outline: none !important;
    box-shadow: 0 0 0 2px #B03A2E !important;
    border-color: #B03A2E !important;
}

/* Dividers — Streamlit's default hr is nearly invisible on this palette */
hr {
    border: none !important;
    border-top: 1px solid #8A7C55 !important;
    opacity: 1 !important;
    margin: 1.2rem 0 !important;
}

/* Section subheaders (1. The Job You Want / 2. Your Background) */
h3 {
    font-family: 'DMSans', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    font-size: 1.05rem !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 3. SIDEBAR
# -----------------------------
def get_secret_key():
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return ""

api_key = get_secret_key() or os.environ.get("ANTHROPIC_API_KEY", "")

with st.sidebar:
    st.header("⚙️ Settings")
    if api_key:
        st.success("API key detected.")
    else:
        entered_key = st.text_input("Paste Anthropic API Key", type="password")
        if entered_key:
            api_key = entered_key
        st.markdown("Get a key at [console.anthropic.com](https://console.anthropic.com/)")

    model = st.selectbox(
        "Claude Model",
        ["claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929"]
    )

    st.markdown("---")
    st.markdown("**How to use:**")
    st.markdown("1. Paste the job description.")
    st.markdown("2. Paste your old resume.")
    st.markdown("3. Let AI translate your skills.")

# -----------------------------
# 4. HEADER
# -----------------------------
st.markdown("""
<div class="cf-eyebrow">Case file · Resume vs. reality</div>
<div class="cf-title-row">
    <div class="cf-title">Career Change Strategist</div>
</div>
<div class="cf-subtitle">Turn your past experience into a strategic battle plan for your career pivot.</div>
<hr class="cf-hr" />
""", unsafe_allow_html=True)


# -----------------------------
# 5. SESSION STATE + FREE LIMIT
# -----------------------------
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False
if "result" not in st.session_state:
    st.session_state.result = ""

locked = (st.session_state.gen_count >= 3) and not st.session_state.unlocked

# -----------------------------
# 6. SYSTEM PROMPT
# -----------------------------
system_prompt = """
You are an expert career coach and executive resume writer specializing in career transitions.

Your goal is to help a career changer map their past, seemingly unrelated experience to a new target role.

You must:
1. Extract the core competencies required by the job description.
2. Separate the requirements into: Direct experience, Adjacent/transferable experience, and Missing/limited experience.
3. Translate the user's past experience into relevant competencies without exaggerating.
4. Use professional, ATS-friendly language.
5. Avoid lying, exaggerating, or inventing experience.
6. Do not invent numbers, metrics, promotions, qualifications, tools, or business outcomes unless the user explicitly provided them.
7. Do not imply the user has specialized experience they did not mention, especially in forensic, legal, medical, scientific, safety-critical, or government roles.
8. For missing requirements, provide honest bridge language that acknowledges the gap and emphasizes aptitude, related experience, trainability, or willingness to learn.
9. If no numbers are available, use honest qualitative impact language such as "supported", "improved", "maintained", "helped", or "contributed to".
10. Write clearly, simply, and naturally. Avoid generic filler phrases like "strong work ethic" or "passionate".
"""

# -----------------------------
# 7. LOCKED (PAYWALL) vs FREE UI
# -----------------------------
if locked:
    st.markdown("---")
    st.error("🚫 **You've used all 3 of your free Career Plans!**")
    st.markdown("""
    ### Unlock unlimited lifetime access
    For less than the price of a coffee, get unlimited gap analyses, resume rewrites and interview scripts for your whole job search.

    Unlock your unlimited plan here https://sleekforge.gumroad.com/l/career-strategist
    ##
    """)

    unlock_code = st.text_input("Already purchased? Enter your unlock code:", type="password")
    if unlock_code.strip().upper() == "PIVOT2024":
        st.session_state.unlocked = True
        st.rerun()

else:
    if not st.session_state.unlocked:
        remaining = 3 - st.session_state.gen_count
        st.info(f"🎟️ **Free plan:** {remaining} of 3 free plans remaining.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. The Job You Want")
        target_role = st.text_input("Target Role", placeholder="e.g., Paralegal")
        job_desc = st.text_area(
            "Job Description",
            height=300,
            placeholder="Paste the full job description here..."
        )

    with col2:
        st.subheader("2. Your Background")
        years_exp = st.text_input(
            "Current Field / Years",
            placeholder="e.g., Retail management, 5 years"
        )
        resume = st.text_area(
            "Your Resume / Experience",
            height=300,
            placeholder="Paste your resume bullets or background summary..."
        )

    user_prompt = f"""
TARGET ROLE:
{target_role}

CURRENT FIELD / YEARS OF EXPERIENCE:
{years_exp}

JOB DESCRIPTION:
{job_desc}

USER'S PAST EXPERIENCE:
{resume}

IMPORTANT: Use only the facts provided by the user. Do not invent metrics, outcomes, responsibilities, tools, qualifications, or specialized experience.

When rewriting resume bullets, you must use the user's specific metrics and achievements if they were provided and are relevant. Do not omit numbers merely to sound concise. Prefer concrete evidence over generic summaries. Rank the rewritten bullets from most relevant to least relevant for the target job description.

When selecting rewritten resume bullets, prioritize the user's experience that most closely matches the job description. Favor evidence related to documentation, records, written correspondence, case handling, confidential or sensitive information, compliance, audits, reporting, deadlines, stakeholder liaison, research-like analysis, and process improvement. Do not include trivial or weak duties if stronger relevant evidence exists.

If the user lacks a core required qualification or direct experience, state clearly that the role is a stretch. Do not present the user as a direct match. Suggest honest bridge language and, where appropriate, adjacent roles that may be more realistic.

For legal, compliance, government, case management, or administrative roles, prioritize evidence involving case records, confidential or sensitive matters, written correspondence, escalation documentation, audits, compliance, deadlines, reporting, stakeholder liaison, and structured analysis. Do not use the phrase "legal research" unless the user explicitly has legal research experience. If the user has research-like experience, describe it as "structured analysis", "operational investigation", "root-cause analysis", or "records-based analysis" instead.

Style and evidence rules:
- Avoid generic phrases such as "strong work ethic", "passionate", "dynamic team", "quick learner", or "eager to learn" unless they are supported by specific evidence.
- Every rewritten resume bullet must be directly based on a specific fact from the user's provided experience.
- Do not infer new outcomes. For example, do not say "reduced escalations" or "improved customer satisfaction" unless the user explicitly provided that result.
- Where possible, include specific systems, tools, case volumes, response standards, deadlines, audit results, or metrics that the user provided.
- The cover letter bridge must include one honest gap and one specific example from the user's experience.
- The interview talking point must include one specific example from the user's experience, preferably with a metric or concrete result.

Please provide the following in clean Markdown format:

## 🎯 ATS Keyword Match
List the top hard skills and soft skills from the job description.

## ⚠️ Missing Requirements to Address Honestly
List important requirements the user does not clearly have, and suggest how to address them honestly in a cover letter or interview.

## 📊 Role Fit Assessment
Provide a conservative role fit assessment in a Markdown table.
| Category | Assessment |
|---|---|
| Direct match | Low / Medium / High |
| Adjacent or transferable match | Low / Medium / High |
| Missing requirements | Low / Medium / High |
| Overall application strength | Weak / Stretch / Possible / Strong |

After the table, write one or two sentences explaining the rating. Be honest. Do not inflate the score. If the user is missing core required experience, label the role as a stretch and suggest 3 to 5 more realistic adjacent roles at the end of the Role Fit Assessment.

## ✍️ Rewritten Resume Bullets
Provide 4 to 6 highly professional, ATS-optimized resume bullets based only on the user's provided experience. Group them by theme if helpful. Use strong action verbs. Only include numbers if the user provided them. Do not claim specialized tools, systems, or duties the user did not mention.

## 💬 Cover Letter Bridge
Write 2-3 sentences for a cover letter that honestly acknowledges the career change while showing relevance and motivation. Include one specific example from the user's experience.

## 💡 Interview Talking Point
Give one strong, honest narrative hook the user can use when asked: "Tell me about yourself", "Why are you changing careers?", or "How does your experience relate to this role?". Include one specific example from the user's experience.
"""

    if st.button("Generate Strategic Career Plan ✨", type="primary"):
        if not api_key:
            st.error("Please add your API key in the sidebar.")
        elif not job_desc or not resume:
            st.warning("Please paste both the job description and your resume.")
        else:
            with st.spinner("Analyzing keywords and rewriting bullets..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)

                    message = client.messages.create(
                        model=model,
                        temperature=0.3,
                        max_tokens=3000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}]
                    )

                    st.session_state.result = message.content[0].text

                    if not st.session_state.unlocked:
                        st.session_state.gen_count += 1
                        st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# -----------------------------
# 8. DISPLAY RESULTS
# -----------------------------
if st.session_state.result:
    st.markdown("---")
    st.subheader("Your Strategic Career Plan")
    st.markdown(st.session_state.result)

    st.download_button(
        label="Download Results",
        data=st.session_state.result,
        file_name="career_strategy.md",
        mime="text/markdown"
    )

# -----------------------------
# 9. FOOTER
# -----------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B6355; font-size: 12px; margin-top: 30px; font-family: 'FiraCode', monospace;">
    <b>Disclaimer:</b> This tool provides AI-generated career advice. Always review before submitting applications.
</div>
""", unsafe_allow_html=True)