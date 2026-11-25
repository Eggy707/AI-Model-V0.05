import streamlit as st
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="AI Model V0.07", page_icon="🟠", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {max-width: 780px; padding-top: 2rem; padding-bottom: 5rem;}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #30302E; border-radius: 16px; padding: 12px 18px; border: 1px solid #3D3C3A;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: transparent; padding: 8px 4px; border: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize user account state
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False

# Dynamic greeting (adds ", Name" only if an account was created)
def get_greeting():
    hour = datetime.now(ZoneInfo("America/Vancouver")).hour
    if 5 <= hour < 12:
        base = "Good morning"
    elif 12 <= hour < 17:
        base = "Good afternoon"
    else:
        base = "Good evening"
    
    if st.session_state.user_name.strip():
        return f"{base}, {st.session_state.user_name.strip()}"
    return base

def get_system_prompt():
    name_context = f"The user's name is {st.session_state.user_name}. " if st.session_state.user_name else ""
    return {
        "role": "system",
        "content": (
            f"{name_context}You are my close friend texting me casually. "
            "NEVER say 'How can I help you' or act like a customer service bot. "
            "Keep replies natural, thoughtful, and conversational."
        )
    }

# --- ACCOUNT CREATION / SKIP SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 12vh;'>🟠 Welcome to AI Model V0.07</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99;'>Create a quick profile to personalize your AI, or skip to stay anonymous.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("account_form"):
            name_input = st.text_input("Display Name", placeholder="Enter your name...")
            password_input = st.text_input("Password (optional)", type="password", placeholder="Create a password...")
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                create_btn = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            with btn_col2:
                skip_btn = st.form_submit_button("Skip (Guest)", use_container_width=True)
            
            if create_btn:
                st.session_state.user_name = name_input.strip()
                st.session_state.setup_done = True
                st.session_state.messages = [get_system_prompt()]
                st.rerun()
            elif skip_btn:
                st.session_state.user_name = ""
                st.session_state.setup_done = True
                st.session_state.messages = [get_system_prompt()]
                st.rerun()
    st.stop()

# --- MAIN APP AFTER SETUP ---
if "messages" not in st.session_state:
    st.session_state.messages = [get_system_prompt()]

with st.sidebar:
    st.markdown("### 🟠 AI Model V0.07")
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = [get_system_prompt()]
        st.rerun()
    
    st.divider()
    if st.session_state.user_name:
        st.caption(f"👤 Signed in as **{st.session_state.user_name}**")
        if st.button("Log out / Switch account", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.rerun()
    else:
        st.caption("👤 Guest Mode")
        if st.button("Create Account", use_container_width=True):
            st.session_state.setup_done = False
            st.rerun()

if len(st.session_state.messages) == 1:
    st.markdown(f"<h2 style='text-align: center; margin-top: 15vh;'>{get_greeting()}</h2>", unsafe_allow_html=True)

for msg in st.session_state.messages[1:]:
    avatar = "👤" if msg["role"] == "user" else "🟠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

if prompt := st.chat_input("Write a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🟠"):
        placeholder = st.empty()
        full_response = ""
        
        stream = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=st.session_state.messages,
            stream=True
        )
        for chunk in stream:
            token = chunk.choices.delta.content or ""
            full_response += token
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
