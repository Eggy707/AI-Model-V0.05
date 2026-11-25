import streamlit as st
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os

st.set_page_config(page_title="AI Model V0.09", page_icon="🟠", layout="wide")

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

# --- USER DATABASE HELPERS ---
USERS_FILE = "users_db.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False
if "long_term_memories" not in st.session_state:
    st.session_state.long_term_memories = []

def sync_user_memories():
    if st.session_state.user_name:
        users = load_users()
        user_key = st.session_state.user_name.lower()
        if user_key in users:
            users[user_key]["memories"] = st.session_state.long_term_memories
            save_users(users)

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
    memory_context = ""
    if st.session_state.long_term_memories:
        joined_memories = "\n".join(f"- {m}" for m in st.session_state.long_term_memories)
        memory_context = (
            "\n\nHere are long-term memories you remember from past conversations with the user:\n"
            f"{joined_memories}\n"
            "Naturally reference these memories when relevant, just like a real friend would, without sounding robotic."
        )

    return {
        "role": "system",
        "content": (
            f"{name_context}You are my close friend texting me casually. "
            "NEVER say 'How can I help you' or act like a customer service bot. "
            "Keep replies natural, thoughtful, and conversational."
            f"{memory_context}"
        )
    }

# --- LOGIN / SIGN UP / GUEST SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>🟠 AI Model V0.09</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99;'>Log in to load your personal memories, create an account, or continue as a guest.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username", placeholder="Enter your username...")
                login_pass = st.text_input("Password", type="password", placeholder="Enter your password...")
                login_submit = st.form_submit_button("Log In", use_container_width=True, type="primary")
                
                if login_submit:
                    users = load_users()
                    user_key = login_user.strip().lower()
                    if not user_key:
                        st.error("Please enter a username.")
                    elif user_key not in users:
                        st.error("Account not found. Switch to 'Create Account' to sign up!")
                    elif users[user_key]["password"] != hash_password(login_pass):
                        st.error("Incorrect password.")
                    else:
                        st.session_state.user_name = users[user_key]["display_name"]
                        st.session_state.long_term_memories = users[user_key].get("memories", [])
                        st.session_state.setup_done = True
                        st.session_state.messages = [get_system_prompt()]
                        st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("Choose a Username", placeholder="e.g., Ethan")
                new_pass = st.text_input("Create a Password", type="password", placeholder="Create a password...")
                signup_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if signup_submit:
                    users = load_users()
                    clean_name = new_user.strip()
                    user_key = clean_name.lower()
                    if not clean_name or not new_pass:
                        st.error("Please enter both a username and a password.")
                    elif user_key in users:
                        st.error("That username is already taken—try logging in!")
                    else:
                        users[user_key] = {
                            "display_name": clean_name,
                            "password": hash_password(new_pass),
                            "memories": []
                        }
                        save_users(users)
                        st.session_state.user_name = clean_name
                        st.session_state.long_term_memories = []
                        st.session_state.setup_done = True
                        st.session_state.messages = [get_system_prompt()]
                        st.rerun()

        st.divider()
        if st.button("Continue as Guest (No Name)", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.long_term_memories = []
            st.session_state.setup_done = True
            st.session_state.messages = [get_system_prompt()]
            st.rerun()
    st.stop()
import streamlit as st
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os

st.set_page_config(page_title="AI Model V0.09", page_icon="🟠", layout="wide")

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

# --- USER DATABASE HELPERS ---
USERS_FILE = "users_db.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "setup_done" not in st.session_state:
    st.session_state.setup_done = False
if "long_term_memories" not in st.session_state:
    st.session_state.long_term_memories = []

def sync_user_memories():
    if st.session_state.user_name:
        users = load_users()
        user_key = st.session_state.user_name.lower()
        if user_key in users:
            users[user_key]["memories"] = st.session_state.long_term_memories
            save_users(users)

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
    memory_context = ""
    if st.session_state.long_term_memories:
        joined_memories = "\n".join(f"- {m}" for m in st.session_state.long_term_memories)
        memory_context = (
            "\n\nHere are long-term memories you remember from past conversations with the user:\n"
            f"{joined_memories}\n"
            "Naturally reference these memories when relevant, just like a real friend would, without sounding robotic."
        )

    return {
        "role": "system",
        "content": (
            f"{name_context}You are my close friend texting me casually. "
            "NEVER say 'How can I help you' or act like a customer service bot. "
            "Keep replies natural, thoughtful, and conversational."
            f"{memory_context}"
        )
    }

# --- LOGIN / SIGN UP / GUEST SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>🟠 AI Model V0.09</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99;'>Log in to load your personal memories, create an account, or continue as a guest.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username", placeholder="Enter your username...")
                login_pass = st.text_input("Password", type="password", placeholder="Enter your password...")
                login_submit = st.form_submit_button("Log In", use_container_width=True, type="primary")
                
                if login_submit:
                    users = load_users()
                    user_key = login_user.strip().lower()
                    if not user_key:
                        st.error("Please enter a username.")
                    elif user_key not in users:
                        st.error("Account not found. Switch to 'Create Account' to sign up!")
                    elif users[user_key]["password"] != hash_password(login_pass):
                        st.error("Incorrect password.")
                    else:
                        st.session_state.user_name = users[user_key]["display_name"]
                        st.session_state.long_term_memories = users[user_key].get("memories", [])
                        st.session_state.setup_done = True
                        st.session_state.messages = [get_system_prompt()]
                        st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("Choose a Username", placeholder="e.g., Ethan")
                new_pass = st.text_input("Create a Password", type="password", placeholder="Create a password...")
                signup_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if signup_submit:
                    users = load_users()
                    clean_name = new_user.strip()
                    user_key = clean_name.lower()
                    if not clean_name or not new_pass:
                        st.error("Please enter both a username and a password.")
                    elif user_key in users:
                        st.error("That username is already taken—try logging in!")
                    else:
                        users[user_key] = {
                            "display_name": clean_name,
                            "password": hash_password(new_pass),
                            "memories": []
                        }
                        save_users(users)
                        st.session_state.user_name = clean_name
                        st.session_state.long_term_memories = []
                        st.session_state.setup_done = True
                        st.session_state.messages = [get_system_prompt()]
                        st.rerun()

        st.divider()
        if st.button("Continue as Guest (No Name)", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.long_term_memories = []
            st.session_state.setup_done = True
            st.session_state.messages = [get_system_prompt()]
            st.rerun()
    st.stop()
