"""
app.py
PromptCraft AI Studio - A minimal, whitespace-driven multi-tool LLM wrapper application.
Renders 6 practical tools in styled tabs with session states, latency metrics, and query history.
"""

import time
import streamlit as st
from dotenv import load_dotenv
import prompts
import utils

# Force reload environment variables from .env on every rerun
load_dotenv(override=True)

# ==========================================
# PAGE CONFIGURATION & THEME STYLING
# ==========================================
st.set_page_config(
    page_title="PromptCraft AI Studio",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom minimal CSS matching the light, whitespace-driven editorial guidelines.
# Replaces Streamlit defaults, removes pill buttons/card borders/shadows,
# sets clean hairline lines, and formats active tabs with a thin black underline.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Global reset for background and font */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #FAFAFA !important;
        color: #1A1A1A !important;
    }
    
    /* Center container padding for whitespace-driven structure */
    div.block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 6rem !important;
        padding-right: 6rem !important;
        max-width: 1200px !important;
    }

    /* Streamlit header transparency */
    [data-testid="stHeader"] {
        background-color: rgba(250, 250, 250, 0.0) !important;
        border-bottom: none !important;
        height: 3rem !important;
    }

    /* Sidebar minimal layout */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E5E5 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #4A4A4A !important;
        font-size: 0.9rem !important;
    }
    
    /* Title, header typography customization */
    h1 {
        font-size: 2.2rem !important;
        font-weight: 300 !important;
        letter-spacing: -0.02em !important;
        color: #1A1A1A !important;
        margin-bottom: 0.25rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        font-weight: 300 !important;
        color: #1A1A1A !important;
        margin-top: 2rem !important;
        margin-bottom: 1.25rem !important;
    }
    
    h3 {
        font-size: 1.15rem !important;
        font-weight: 500 !important;
        color: #1A1A1A !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    /* Text area and inputs flat design styling */
    textarea, input, select, [data-baseweb="select"] {
        border: 1px solid #E5E5E5 !important;
        border-radius: 0px !important;
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        box-shadow: none !important;
        font-size: 0.9rem !important;
    }
    textarea:focus, input:focus {
        border-color: #1A1A1A !important;
        outline: none !important;
    }

    /* Understated Streamlit Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #E5E5E5 !important;
        gap: 2rem !important;
        padding-bottom: 0.25rem !important;
        margin-bottom: 2rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #888888 !important;
        font-weight: 400 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 0.2rem !important;
        transition: color 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #1A1A1A !important;
        font-weight: 500 !important;
        border-bottom: 2px solid #1A1A1A !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1A1A1A !important;
    }

    /* Primary buttons: solid charcoal background with white text, zero border-radius */
    div.stButton > button {
        border: 1px solid #1A1A1A !important;
        border-radius: 0px !important;
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        letter-spacing: 0.03em !important;
    }
    div.stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border-color: #1A1A1A !important;
    }

    /* Secondary action buttons (e.g. Download buttons): outlined, white background */
    div.stDownloadButton > button {
        border: 1px solid #E5E5E5 !important;
        border-radius: 0px !important;
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        font-weight: 400 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        margin-top: 1rem !important;
    }
    div.stDownloadButton > button:hover {
        border-color: #1A1A1A !important;
        background-color: #FAFAFA !important;
        color: #1A1A1A !important;
    }

    /* Hairline-bordered output panel boxes */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #E5E5E5 !important;
        border-radius: 0px !important;
        background-color: #FFFFFF !important;
        box-shadow: none !important;
        padding: 1.75rem !important;
    }

    /* Hide redundant elements and metric formatting */
    [data-testid="stMetric"] {
        border: none !important;
        background-color: transparent !important;
        padding: 0px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 300 !important;
        color: #1A1A1A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 400 !important;
        color: #888888 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Sidebar slider labels and status formatting */
    .stSlider label {
        font-size: 0.8rem !important;
        color: #4A4A4A !important;
    }
    
    /* Space utility */
    .vertical-spacer {
        height: 2rem;
    }
    .vertical-spacer-lg {
        height: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "outputs" not in st.session_state:
    st.session_state.outputs = {
        "summarizer": "",
        "writer": "",
        "explainer": "",
        "translator": "",
        "interview": "",
        "resume": ""
    }
if "history" not in st.session_state:
    st.session_state.history = []
if "last_latency" not in st.session_state:
    st.session_state.last_latency = None

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.markdown("<h3 style='margin-top: 1rem; margin-bottom: 0.5rem;'>Settings</h3>", unsafe_allow_html=True)

# Provider & Model Settings
provider = st.sidebar.selectbox("LLM Provider", ["Groq", "OpenAI"], key="provider")

if provider == "Groq":
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
else:
    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

model = st.sidebar.selectbox("Model", models, key="model")

# Password field for API key (supports optional 'mock' value)
api_key_input = st.sidebar.text_input(
    "API Key",
    type="password",
    help="Enter your API Key. Leave blank to load from .env, or write 'mock' for simulated generation.",
    key="api_key"
)

# Hyperparameters
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.5, value=0.7, step=0.1)
max_tokens = st.sidebar.slider("Max Tokens", min_value=128, max_value=2048, value=1024, step=64)

# Connection Status Notification
resolved_key = api_key_input.strip() if api_key_input else utils.get_default_api_key(provider)
if resolved_key.lower() == "mock" or not resolved_key:
    st.sidebar.info("💡 Running in Mock/Simulated Mode.")
    active_api_key = "mock"
else:
    st.sidebar.success(f"🔌 Connected to {provider.upper()} API.")
    active_api_key = resolved_key

# Latency Metric Panel
st.sidebar.markdown("---")
st.sidebar.metric(
    label="Last Response Latency",
    value=f"{st.session_state.last_latency:.2f} s" if st.session_state.last_latency else "—"
)

# Session Request History (max 25 entries)
st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 0.8rem; font-weight: 500; color: #888888; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>Request History</p>", unsafe_allow_html=True)
if not st.session_state.history:
    st.sidebar.caption("No queries recorded in this session.")
else:
    for item in st.session_state.history:
        # Standard clean expander for history view
        with st.sidebar.expander(f"{item['timestamp']} - {item['tool']}", expanded=False):
            st.markdown(f"**Model:** `{item['model']}`")
            st.markdown(f"**Latency:** {item['latency']:.2f}s")
            st.markdown(f"**Prompt Snippet:**\n*{item['query_preview']}*")
            st.markdown("---")
            st.markdown(f"**Response:**\n{item['response']}")

# ==========================================
# MAIN CANVAS - TYPOGRAPHY HEADER
# ==========================================
st.markdown("<h1>PromptCraft AI Studio</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #666666; font-size: 1rem; font-weight: 300; margin-bottom: 2rem;'>A quiet, minimal workspace for crafting text, code, and documents via specialized prompt layouts.</p>", unsafe_allow_html=True)

# Segmented control tab layout
tab_summarizer, tab_writer, tab_explainer, tab_translator, tab_interview, tab_resume = st.tabs([
    "Text Summarizer",
    "Essay / Blog Writer",
    "Code Explainer",
    "Language Translator",
    "Interview Prep",
    "Resume Bullets"
])

# ==========================================
# TAB 1: TEXT SUMMARIZER
# ==========================================
with tab_summarizer:
    st.markdown("<h3>Text Summarizer</h3>", unsafe_allow_html=True)
    text_input = st.text_area(
        "Source Text", 
        height=200, 
        placeholder="Pasted text here...", 
        key="sum_text",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        length = st.selectbox(
            "Summary Length", 
            ["1 sentence", "short paragraph", "3 bullets", "detailed 200 words"], 
            key="sum_len"
        )
    with col2:
        style = st.selectbox(
            "Summary Style", 
            ["neutral", "ELI5", "formal", "casual"], 
            key="sum_style"
        )
    
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Generate Summary", key="sum_submit"):
        if not text_input.strip():
            st.warning("Please paste some text to summarize.")
        else:
            with st.spinner("Summarizing..."):
                sys_prompt = prompts.SUMMARIZER_SYSTEM
                usr_prompt = prompts.get_summarizer_prompt(text_input, length, style)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["summarizer"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Summarizer",
                    "model": model,
                    "latency": latency,
                    "query_preview": text_input[:50] + ("..." if len(text_input) > 50 else ""),
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["summarizer"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Generated Summary</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
        
        word_count = len(output.split())
        st.caption(f"Word Count: {word_count}")
        st.download_button(
            label="Download Output",
            data=output,
            file_name="summary.md",
            mime="text/markdown",
            key="sum_download"
        )

# ==========================================
# TAB 2: ESSAY / BLOG WRITER
# ==========================================
with tab_writer:
    st.markdown("<h3>Essay / Blog Writer</h3>", unsafe_allow_html=True)
    
    topic = st.text_input(
        "Content Topic", 
        placeholder="Enter topic or title guidelines...", 
        key="write_topic_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        content_type = st.selectbox(
            "Format Type", 
            ["essay", "blog post", "opinion piece", "LinkedIn post"], 
            key="write_type"
        )
    with col2:
        tone = st.selectbox(
            "Tone", 
            ["informative", "persuasive", "conversational", "professional", "humorous"], 
            key="write_tone"
        )
    with col3:
        target_words = st.slider(
            "Target Word Count", 
            min_value=100, 
            max_value=1500, 
            value=500, 
            step=50, 
            key="write_words"
        )
        
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Generate Piece", key="write_submit"):
        if not topic.strip():
            st.warning("Please enter a content topic.")
        else:
            with st.spinner("Drafting piece..."):
                sys_prompt = prompts.WRITER_SYSTEM
                usr_prompt = prompts.get_writer_prompt(topic, content_type, tone, target_words)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["writer"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Writer",
                    "model": model,
                    "latency": latency,
                    "query_preview": f"{content_type} about: {topic[:30]}...",
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["writer"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Generated Piece</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
            
        word_count = len(output.split())
        st.caption(f"Word Count: {word_count}")
        st.download_button(
            label="Download Output",
            data=output,
            file_name="draft.md",
            mime="text/markdown",
            key="write_download"
        )

# ==========================================
# TAB 3: CODE EXPLAINER
# ==========================================
with tab_explainer:
    st.markdown("<h3>Code Explainer</h3>", unsafe_allow_html=True)
    code_input = st.text_area(
        "Pasted Code Block", 
        height=200, 
        placeholder="Paste source code here...", 
        key="code_exp_input",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox(
            "Programming Language", 
            ["Python", "JavaScript", "TypeScript", "Go", "Rust", "C++", "Java", "HTML", "CSS", "Other"], 
            key="code_lang"
        )
    with col2:
        detail_level = st.selectbox(
            "Detail Level", 
            ["beginner", "intermediate", "advanced"], 
            key="code_detail"
        )
        
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Explain Code", key="code_submit"):
        if not code_input.strip():
            st.warning("Please paste some code to explain.")
        else:
            with st.spinner("Analyzing code..."):
                sys_prompt = prompts.CODE_EXPLAINER_SYSTEM
                usr_prompt = prompts.get_code_explainer_prompt(code_input, language, detail_level)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["explainer"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Code Explainer",
                    "model": model,
                    "latency": latency,
                    "query_preview": f"{language} code explainer ({detail_level})",
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["explainer"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Code Analysis</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
            
        st.download_button(
            label="Download Output",
            data=output,
            file_name="explanation.md",
            mime="text/markdown",
            key="code_download"
        )

# ==========================================
# TAB 4: LANGUAGE TRANSLATOR
# ==========================================
with tab_translator:
    st.markdown("<h3>Language Translator</h3>", unsafe_allow_html=True)
    trans_input = st.text_area(
        "Source Text", 
        height=200, 
        placeholder="Enter text to translate...", 
        key="trans_text",
        label_visibility="collapsed"
    )
    
    target_language = st.selectbox(
        "Target Language", 
        ["Spanish", "French", "German", "Hindi", "Japanese", "Chinese", "Arabic", "Portuguese", "Russian"], 
        key="trans_lang"
    )
    
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Translate", key="trans_submit"):
        if not trans_input.strip():
            st.warning("Please enter text to translate.")
        else:
            with st.spinner("Translating text..."):
                sys_prompt = prompts.TRANSLATOR_SYSTEM
                usr_prompt = prompts.get_translator_prompt(trans_input, target_language)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["translator"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Translator",
                    "model": model,
                    "latency": latency,
                    "query_preview": f"Translate to {target_language}: " + trans_input[:20] + "...",
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["translator"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Translated Output</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
            
        st.download_button(
            label="Download Output",
            data=output,
            file_name="translation.md",
            mime="text/markdown",
            key="trans_download"
        )

# ==========================================
# TAB 5: INTERVIEW PREP GENERATOR
# ==========================================
with tab_interview:
    st.markdown("<h3>Interview Prep Generator</h3>", unsafe_allow_html=True)
    
    role = st.text_input(
        "Target Role / Position", 
        placeholder="e.g. Staff Site Reliability Engineer", 
        key="int_role_input"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        seniority = st.selectbox(
            "Seniority Level", 
            ["intern", "entry", "mid", "senior"], 
            key="int_seniority"
        )
    with col2:
        num_questions = st.slider(
            "Number of Questions", 
            min_value=1, 
            max_value=15, 
            value=5, 
            step=1, 
            key="int_num"
        )
        
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Generate Prep Guide", key="int_submit"):
        if not role.strip():
            st.warning("Please specify a target role.")
        else:
            with st.spinner("Generating interview prep..."):
                sys_prompt = prompts.INTERVIEW_PREP_SYSTEM
                usr_prompt = prompts.get_interview_prep_prompt(role, seniority, num_questions)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["interview"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Interview Prep",
                    "model": model,
                    "latency": latency,
                    "query_preview": f"{seniority} {role} ({num_questions} Qs)",
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["interview"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Prepared Interview Questions</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
            
        st.download_button(
            label="Download Output",
            data=output,
            file_name="interview_prep.md",
            mime="text/markdown",
            key="int_download"
        )

# ==========================================
# TAB 6: RESUME BULLET GENERATOR
# ==========================================
with tab_resume:
    st.markdown("<h3>Resume Bullet Generator</h3>", unsafe_allow_html=True)
    
    desc_input = st.text_area(
        "Plain Task / Role Description", 
        height=150, 
        placeholder="Enter your tasks, responsibilities, or accomplishments in plain text...", 
        key="res_desc",
        label_visibility="collapsed"
    )
    
    num_bullets = st.slider(
        "Number of Bullets to Generate", 
        min_value=1, 
        max_value=10, 
        value=3, 
        step=1, 
        key="res_num"
    )
    
    st.markdown('<div class="vertical-space"></div>', unsafe_allow_html=True)
    
    if st.button("Generate Bullets", key="res_submit"):
        if not desc_input.strip():
            st.warning("Please describe your task/role to build resume bullets.")
        else:
            with st.spinner("Generating bullets..."):
                sys_prompt = prompts.RESUME_BULLET_SYSTEM
                usr_prompt = prompts.get_resume_bullet_prompt(desc_input, num_bullets)
                
                result, latency = utils.call_llm(
                    provider=provider,
                    model=model,
                    system_prompt=sys_prompt,
                    user_prompt=usr_prompt,
                    api_key=active_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.outputs["resume"] = result
                st.session_state.last_latency = latency
                st.session_state.history.insert(0, {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "tool": "Resume Bullets",
                    "model": model,
                    "latency": latency,
                    "query_preview": desc_input[:50] + ("..." if len(desc_input) > 50 else ""),
                    "response": result
                })
                st.session_state.history = st.session_state.history[:25]
                st.rerun()

    # Display Output if exists
    output = st.session_state.outputs["resume"]
    if output:
        st.markdown("---")
        st.markdown("<h4>Generated Resume Bullets</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(output)
            
        st.download_button(
            label="Download Output",
            data=output,
            file_name="resume_bullets.md",
            mime="text/markdown",
            key="res_download"
        )
