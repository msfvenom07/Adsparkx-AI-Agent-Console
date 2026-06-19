import os
import sys
import json
import base64
from pathlib import Path
import streamlit as st
from PIL import Image

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent))

# Load assets (logo / favicon)
logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
logo_image = None
logo_base64 = ""
if logo_path.exists():
    try:
        logo_image = Image.open(logo_path)
        with open(logo_path, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode()
    except Exception:
        pass

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import check_escalation

# Page Configuration
st.set_page_config(
    page_title="Adsparkx AI Adaptive Support Agent",
    page_icon=logo_image if logo_image else "🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Global styles and resets */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #070A13 !important;
        color: #E2E8F0 !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
        color: #E2E8F0 !important;
        z-index: 99 !important;
    }

    h1, h2, h3, h4, h5, h6, .header-title {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
    }

    /* Scrollbar customization */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #070A13;
    }
    ::-webkit-scrollbar-thumb {
        background: #1F2937;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #374151;
    }

    /* Page container adjustments */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 95% !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #05070D !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Outfit', sans-serif !important;
        color: #F8FAFC !important;
    }
    
    /* Custom Streamlit Sliders & Inputs overrides */
    div[data-baseweb="slider"] {
        margin-bottom: 8px;
    }
    
    /* Sidebar Button Style */
    section[data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #94A3B8 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(99, 102, 241, 0.1) !important;
        color: #F8FAFC !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Custom Modern Header Navigation Bar */
    .header-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(17, 24, 39, 0.6) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 24px;
        margin-bottom: 24px;
        margin-top: 10px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
    }
    .header-logo {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.45rem;
        background: linear-gradient(135deg, #6366F1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .logo-icon-img {
        height: 32px;
        width: auto;
        border-radius: 6px;
        filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
    }
    .logo-spark {
        font-size: 1.25rem;
        text-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
        display: inline-block;
        animation: sparkGlow 2.5s infinite ease-in-out;
    }
    @keyframes sparkGlow {
        0% { transform: scale(1) rotate(0deg); opacity: 0.8; }
        50% { transform: scale(1.15) rotate(10deg); opacity: 1; }
        100% { transform: scale(1) rotate(0deg); opacity: 0.8; }
    }
    .header-status {
        font-size: 0.85rem;
        color: #94A3B8;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10B981;
        animation: pulseDot 2s infinite;
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* Custom Card Containers (Glassmorphic) */
    .diag-card {
        background: rgba(17, 24, 39, 0.45) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .diag-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.25) !important;
        box-shadow: 0 12px 35px rgba(99, 102, 241, 0.08);
    }
    
    .diag-card h4 {
        margin-top: 0px;
        color: #F8FAFC;
        font-size: 1.15rem;
        font-weight: 700;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 10px;
        margin-bottom: 16px;
        letter-spacing: -0.01em;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Persona Badges */
    .badge-tech {
        background-color: rgba(6, 182, 212, 0.12) !important;
        color: #22D3EE !important;
        border: 1px solid rgba(6, 182, 212, 0.3) !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.1);
    }
    
    .badge-frustrated {
        background-color: rgba(244, 63, 94, 0.12) !important;
        color: #FB7185 !important;
        border: 1px solid rgba(244, 63, 94, 0.3) !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(244, 63, 94, 0.1);
    }
    
    .badge-exec {
        background-color: rgba(245, 158, 11, 0.12) !important;
        color: #FBBF24 !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.1);
    }

    /* Metric Progress Bars */
    .metric-progress-container {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 4px;
        height: 6px;
        width: 100%;
        margin-top: 8px;
        margin-bottom: 12px;
        overflow: hidden;
    }
    .metric-progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .bg-tech {
        background: linear-gradient(90deg, #06B6D4, #22D3EE);
        box-shadow: 0 0 8px rgba(6, 182, 212, 0.4);
    }
    .bg-frustrated {
        background: linear-gradient(90deg, #E11D48, #F43F5E);
        box-shadow: 0 0 8px rgba(244, 63, 94, 0.4);
    }
    .bg-exec {
        background: linear-gradient(90deg, #D97706, #F59E0B);
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
    }
    
    /* Chat Bubble Layouts (Premium Modern Look) */
    .chat-label-user {
        text-align: right;
        font-size: 0.75rem;
        font-weight: 600;
        color: #818CF8;
        margin-bottom: 6px;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .chat-label-agent {
        text-align: left;
        font-size: 0.75rem;
        font-weight: 600;
        color: #94A3B8;
        margin-bottom: 6px;
        margin-left: 8px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .chat-bubble-user {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
        color: #FFFFFF;
        border: none;
        padding: 14px 18px;
        border-radius: 16px 16px 4px 16px;
        margin-bottom: 24px;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25);
        line-height: 1.5;
        font-size: 0.95rem;
    }
    
    .chat-bubble-agent {
        background: rgba(17, 28, 48, 0.75) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        color: #F1F5F9;
        padding: 14px 18px;
        border-radius: 16px 16px 16px 4px;
        margin-bottom: 24px;
        max-width: 80%;
        margin-right: auto;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        line-height: 1.55;
        font-size: 0.95rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .chat-bubble-agent p, .chat-bubble-user p {
        margin: 0 0 8px 0;
    }
    .chat-bubble-agent p:last-child, .chat-bubble-user p:last-child {
        margin-bottom: 0;
    }
    .chat-bubble-agent ul, .chat-bubble-user ul {
        margin: 4px 0 8px 0;
        padding-left: 20px;
    }
    .chat-bubble-agent code {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: #E2E8F0 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-family: monospace !important;
        font-size: 0.88em !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    .chat-bubble-agent pre {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
    }
    
    .bubble-border-tech {
        border: 1.5px solid #06B6D4 !important;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.1) !important;
    }
    
    .bubble-border-frustrated {
        border: 1.5px solid #F43F5E !important;
        box-shadow: 0 4px 20px rgba(244, 63, 94, 0.1) !important;
    }
    
    .bubble-border-exec {
        border: 1.5px solid #F59E0B !important;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.1) !important;
    }
    
    .bubble-border-escalated {
        border: 1.5px solid #EF4444 !important;
        background-color: rgba(239, 68, 68, 0.06) !important;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.15) !important;
    }

    .card-escalated {
        border: 1.5px solid #EF4444 !important;
        background-color: rgba(239, 68, 68, 0.04) !important;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.15) !important;
        animation: alertPulse 2s infinite alternate;
    }
    @keyframes alertPulse {
        0% {
            border-color: rgba(239, 68, 68, 0.3);
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.08);
        }
        100% {
            border-color: rgba(239, 68, 68, 0.85);
            box-shadow: 0 0 18px rgba(239, 68, 68, 0.25);
        }
    }
    
    /* Source list item (Polished Container) */
    .source-item {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid #10B981;
        border-radius: 4px;
        padding: 12px 14px;
        margin-bottom: 14px;
        font-size: 0.88rem;
        transition: all 0.2s ease;
        border-top: 1px solid rgba(255, 255, 255, 0.03);
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        border-right: 1px solid rgba(255, 255, 255, 0.03);
    }
    
    .source-item:hover {
        background: rgba(255, 255, 255, 0.04);
        border-left-width: 5px;
        transform: translateX(2px);
    }
    
    .source-title {
        font-weight: 600;
        color: #E2E8F0;
        font-size: 0.88rem;
    }
    
    .source-score {
        color: #34D399;
        font-weight: 700;
        font-size: 0.82rem;
    }

    .source-progress-container {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 2px;
        height: 4px;
        width: 100%;
        margin-top: 5px;
        margin-bottom: 8px;
        overflow: hidden;
    }
    .source-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #10B981, #34D399);
        border-radius: 2px;
        box-shadow: 0 0 6px rgba(16, 185, 129, 0.3);
    }
    
    .source-snippet {
        color: #94A3B8;
        font-style: italic;
        display: block;
        margin-top: 6px;
        line-height: 1.45;
        font-size: 0.82rem;
    }
    
    /* Welcome suggestion buttons styles */
    div[data-testid="column"] button {
        height: 110px !important;
        background: rgba(17, 24, 39, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        color: #E2E8F0 !important;
        text-align: left !important;
        padding: 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        white-space: normal !important;
        display: block !important;
        width: 100% !important;
    }
    div[data-testid="column"] button:hover {
        background: rgba(99, 102, 241, 0.08) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15) !important;
        color: #F8FAFC !important;
    }
    div[data-testid="column"] button:active {
        transform: translateY(1px) !important;
    }
    div[data-testid="column"] button p {
        margin: 0 !important;
        font-size: 0.88rem !important;
        line-height: 1.4 !important;
    }
</style>
""", unsafe_allow_html=True)

# 1. Initialize RAG pipeline (Cached to avoid reloading)
@st.cache_resource
def load_rag_pipeline():
    pipeline = LocalRAGPipeline()
    # Check if DB is empty, ingest if so
    if pipeline.collection.count() == 0:
        pipeline.ingest_directory()
    return pipeline

try:
    rag_pipeline = load_rag_pipeline()
    loaded_chunks = rag_pipeline.collection.count()
except Exception as e:
    st.error(f"Error loading vector database: {e}")
    st.stop()

# 2. Sidebar Configuration Panel
if logo_image:
    st.sidebar.image(logo_image, width=80)
else:
    st.sidebar.image("https://img.icons8.com/color/96/000000/bot.png", width=70)
st.sidebar.markdown(f"### **Support Console Settings**")

# Settings sliders
similarity_threshold = st.sidebar.slider(
    "Confidence Threshold", 
    min_value=0.10, 
    max_value=1.00, 
    value=config.SIMILARITY_THRESHOLD, 
    step=0.05,
    help="Minimum cosine similarity required before escalating to a human."
)

max_turns = st.sidebar.slider(
    "Max Frustrated Turns", 
    min_value=1, 
    max_value=5, 
    value=config.MAX_CONVERSATION_TURNS, 
    step=1,
    help="Max turns user can display frustration before automatically escalating."
)

# API Status indicators in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("#### **System Diagnostics**")
if config.GEMINI_API_KEY:
    st.sidebar.success("Gemini API: Connected")
else:
    st.sidebar.warning("Gemini API: Offline Fallback Active")
st.sidebar.info(f"Loaded Knowledge Base Chunks: {loaded_chunks}")

# Reset Session State
if st.sidebar.button("Clear Conversation History", use_container_width=True):
    st.session_state.messages = []
    st.session_state.conversation_history = []
    st.session_state.last_persona = "None Detected"
    st.session_state.last_confidence = 0.0
    st.session_state.last_reasoning = "Awaiting first user message..."
    st.session_state.last_sources = []
    st.session_state.escalated = False
    st.session_state.handoff_report = None
    st.session_state.escalation_reason = None
    st.session_state.suggested_query = None
    st.rerun()

# 3. Setup Session State variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "last_persona" not in st.session_state:
    st.session_state.last_persona = "None Detected"
if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 0.0
if "last_reasoning" not in st.session_state:
    st.session_state.last_reasoning = "Awaiting first user message..."
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "escalated" not in st.session_state:
    st.session_state.escalated = False
if "handoff_report" not in st.session_state:
    st.session_state.handoff_report = None
if "escalation_reason" not in st.session_state:
    st.session_state.escalation_reason = None
if "suggested_query" not in st.session_state:
    st.session_state.suggested_query = None

# Floating Modern Header Navigation
logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-icon-img" />' if logo_base64 else '<span class="logo-spark">⚡</span>'
st.markdown(f"""
<div class="header-nav">
    <div class="header-logo">
        {logo_html} Adsparkx AI Agent Console
    </div>
    <div class="header-status">
        <span class="status-dot"></span> System Live
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Split-Screen Layout (8 cols for chat, 4 cols for diagnostics)
col_chat, col_diag = st.columns([8, 4])

# --- CHAT INTERFACE (LEFT COLUMN) ---
with col_chat:
    st.subheader("Support Session Chat")
    
    # Display chat messages from history
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.markdown(f'<div class="chat-label-user">You</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-user">{content}</div>', unsafe_allow_html=True)
        else:
            # Styled based on the message persona or escalation state
            msg_persona = message.get("persona")
            msg_escalated = message.get("escalated", False)
            
            if msg_escalated:
                border_class = "bubble-border-escalated"
                role_label = "Agent (Escalated Handoff)"
            elif msg_persona == "Technical Expert":
                border_class = "bubble-border-tech"
                role_label = f"Agent ({msg_persona})"
            elif msg_persona == "Frustrated User":
                border_class = "bubble-border-frustrated"
                role_label = f"Agent ({msg_persona})"
            elif msg_persona == "Business Executive":
                border_class = "bubble-border-exec"
                role_label = f"Agent ({msg_persona})"
            else:
                border_class = ""
                role_label = "Agent"
                
            st.markdown(f'<div class="chat-label-agent">{role_label}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-agent {border_class}">{content}</div>', unsafe_allow_html=True)
            
    # Render welcome section if conversation is empty
    if not st.session_state.messages:
        logo_img_html = f'<img src="data:image/png;base64,{logo_base64}" style="height:80px; width:auto; border-radius:12px; margin-bottom:16px; filter:drop-shadow(0 0 12px rgba(99,102,241,0.4));" />' if logo_base64 else '<span style="font-size:4rem;">🤖</span>'
        st.markdown(f"""
        <div style="text-align: center; padding: 40px 20px; margin-top: 10px; margin-bottom: 20px; background: rgba(17, 24, 39, 0.2); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.03);">
            {logo_img_html}
            <div style="font-size: 1.8rem; font-weight: 800; font-family: 'Outfit', sans-serif; background: linear-gradient(135deg, #6366F1 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;">
                Adsparkx AI Support Console
            </div>
            <div style="color: #94A3B8; font-size: 0.95rem; max-width: 500px; margin: 0 auto; line-height: 1.5; font-family: 'Plus Jakarta Sans', sans-serif;">
                Experience our real-time persona-aware support assistant. Choose one of the sample query scenarios below to test the adaptive engine:
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='font-size:0.85rem; font-weight:600; color:#818CF8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;'>Choose a test persona scenario:</div>", unsafe_allow_html=True)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("**💻 Technical Expert**\n\nExplain webhook signature validation headers.", use_container_width=True, key="btn_tech"):
                st.session_state.suggested_query = "Explain the webhook payload signature validation headers."
                st.rerun()
        with col_s2:
            if st.button("**😡 Frustrated User**\n\nThis is completely broken! I need help now!", use_container_width=True, key="btn_frust"):
                st.session_state.suggested_query = "This is completely broken! I've been waiting for an hour and nothing is loading!"
                st.rerun()
        with col_s3:
            if st.button("**📊 Business Executive**\n\nWhat is the business impact and resolution ETA?", use_container_width=True, key="btn_exec"):
                st.session_state.suggested_query = "What is the business impact and resolution ETA of the API downtime?"
                st.rerun()

    # If the conversation is already escalated, disable the chat input
    if st.session_state.escalated:
        st.error("This chat session has been escalated to a human support specialist. Chatting is locked.")
        user_input = ""
    else:
        user_input = st.chat_input("Enter your support request...")

    # Check if a suggestion card was clicked
    if st.session_state.get("suggested_query"):
        user_input = st.session_state.suggested_query
        st.session_state.suggested_query = None

    # Handle new user input
    if user_input:
        # Display user message instantly
        st.markdown(f'<div class="chat-label-user">You</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Override config variables locally
        config.SIMILARITY_THRESHOLD = similarity_threshold
        config.MAX_CONVERSATION_TURNS = max_turns

        # Step 1: Detect Persona (Pass history for context-aware classification)
        persona_result = classify_customer_persona(user_input, st.session_state.conversation_history)
        persona = persona_result.get("persona", "Frustrated User")
        confidence = persona_result.get("confidence", 1.0)
        reasoning = persona_result.get("reasoning", "")
        
        # Save persona details to session state
        st.session_state.last_persona = persona
        st.session_state.last_confidence = confidence
        st.session_state.last_reasoning = reasoning

        # Step 2: Retrieve relevant support documents
        retrieved_chunks = rag_pipeline.retrieve_context(user_input, top_k=config.TOP_K)
        st.session_state.last_sources = retrieved_chunks

        # Step 3: Run Escalation check
        escalation_result = check_escalation(
            user_input, persona, st.session_state.conversation_history, retrieved_chunks
        )

        # Step 4: Generate response based on escalation state
        if escalation_result.get("escalate", False):
            # Escalation triggered
            st.session_state.escalated = True
            st.session_state.escalation_reason = escalation_result.get("reason")
            st.session_state.handoff_report = escalation_result.get("handoff_summary")
            
            # Generate tone-matched handoff response
            response_pkg = generate_adaptive_response(
                user_input, persona, retrieved_chunks, st.session_state.conversation_history
            )
            response_text = response_pkg["response"]
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "persona": persona,
                "escalated": True
            })
            st.rerun()
        else:
            # Generate normal response
            response_pkg = generate_adaptive_response(
                user_input, persona, retrieved_chunks, st.session_state.conversation_history
            )
            response_text = response_pkg["response"]
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "persona": persona,
                "escalated": False
            })
            
            # Update rolling conversation history
            st.session_state.conversation_history.append({
                "role": "user",
                "content": user_input,
                "persona": persona
            })
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            st.rerun()

# --- DIAGNOSTICS DASHBOARD (RIGHT COLUMN) ---
with col_diag:
    st.subheader("Console Diagnostics")
    
    # 1. Persona Detection Card
    with st.container():
        persona = st.session_state.last_persona
        confidence = st.session_state.last_confidence
        reasoning = st.session_state.last_reasoning
        
        # Style badge according to active persona
        if persona == "Technical Expert":
            badge_html = f'<span class="badge-tech">Technical Expert</span>'
            bar_class = "bg-tech"
        elif persona == "Frustrated User":
            badge_html = f'<span class="badge-frustrated">Frustrated User</span>'
            bar_class = "bg-frustrated"
        elif persona == "Business Executive":
            badge_html = f'<span class="badge-exec">Business Executive</span>'
            bar_class = "bg-exec"
        else:
            badge_html = f'<span style="color:#94A3B8; font-weight:600;">{persona}</span>'
            bar_class = "bg-tech"
            
        st.markdown(f"""
        <div class="diag-card">
            <h4>1. User Persona Classification</h4>
            <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#94A3B8; font-size:0.9rem; font-weight:500;">Active Persona:</span>
                {badge_html}
            </div>
            <div style="font-size:0.9rem; margin-bottom:4px; color:#F1F5F9; display:flex; justify-content:space-between;">
                <span style="color:#94A3B8; font-size:0.9rem; font-weight:500;">Classification Confidence:</span>
                <b>{confidence * 100:.0f}%</b>
            </div>
            <div class="metric-progress-container">
                <div class="metric-progress-fill {bar_class}" style="width: {confidence * 100}%;"></div>
            </div>
            <div style="font-size:0.85rem; color:#94A3B8; border-top:1px solid rgba(255, 255, 255, 0.06); padding-top:10px; margin-top:10px; line-height:1.45;">
                <b style="color:#F1F5F9;">Reasoning Details:</b><br>{reasoning}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 2. RAG Sources Card
    with st.container():
        sources = st.session_state.last_sources
        
        sources_html = ""
        if sources:
            for idx, chunk in enumerate(sources):
                page_info = f" (Page {chunk['page']})" if chunk.get('page') else ""
                score_pct = chunk["score"] * 100
                snippet = chunk["text"][:140].replace('"', '&quot;')
                sources_html += f'<div class="source-item"><div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span class="source-title">#{idx+1}: {chunk["source"]}{page_info}</span><span class="source-score">{score_pct:.1f}% Match</span></div><div class="source-progress-container"><div class="source-progress-fill" style="width: {score_pct}%;"></div></div><span class="source-snippet">&ldquo;{snippet}...&rdquo;</span></div>'
        else:
            sources_html = f'<div style="color:#94A3B8; font-style:italic; font-size:0.9rem; padding:10px 0;">No documents retrieved yet. Awaiting chat query.</div>'
            
        st.markdown(f"""
        <div class="diag-card">
            <h4>2. Retrieved Knowledge Base Sources</h4>
            {sources_html}
        </div>
        """, unsafe_allow_html=True)

    # 3. Escalation Panel
    with st.container():
        escalated = st.session_state.escalated
        reason = st.session_state.escalation_reason
        report = st.session_state.handoff_report
        
        if escalated:
            st.markdown(f"""
            <div class="diag-card card-escalated">
                <h4 style="color:#EF4444; border-bottom:1px solid rgba(239, 68, 68, 0.2); margin-bottom:12px;">🚨 Escalation Summary (Active)</h4>
                <div style="font-size:0.9rem; color:#F8FAFC; line-height:1.45;">
                    <b style="color:#EF4444;">Trigger Reason:</b><br>
                    <span style="color:#FCA5A5; font-style:italic;">{reason}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show JSON report in a clean collapsible window
            with st.expander("View Structured Handoff JSON Report", expanded=True):
                try:
                    pretty_json = json.dumps(json.loads(report), indent=2)
                    st.code(pretty_json, language="json")
                except Exception:
                    st.text(report)
        else:
            st.markdown(f"""
            <div class="diag-card">
                <h4>3. Escalation & Human Handoff</h4>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
                    <span class="status-dot"></span>
                    <span style="color:#10B981; font-weight:700; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.02em;">AI Agent Handling</span>
                </div>
                <div style="font-size:0.85rem; color:#94A3B8; line-height:1.45; border-top:1px solid rgba(255, 255, 255, 0.06); padding-top:10px; margin-top:10px;">
                    Real-time safety and confidence thresholds are active. Handoff triggers immediately if the user requests human assistance, presents complex invoicing inquiries, or displays repeated frustration.
                </div>
            </div>
            """, unsafe_allow_html=True)
