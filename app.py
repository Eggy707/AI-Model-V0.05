import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib

st.set_page_config(page_title="Coda", page_icon="🟠", layout="wide")

# Connect to Groq AI and your permanent Supabase database
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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
    [data-testid="stStatusWidget"] {
        background-color: #1F1E1D;
        border: 1px solid #383735;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- SUPABASE CLOUD DATABASE HELPERS ---
def get_user_record(username):
    user_key = username.strip().lower()
    res = supabase.table("users").select("*").eq("username", user_key).execute()
    return res.data if res.data else None

def create_user_record(username, password):
    clean_name = username.strip()
    user_key = clean_name.lower()
    new_row = {
        "username": user_key,
        "display_name": clean_name,
        "password": hash_password(password),
        "memories": []
    }
    supabase.table("users").insert(new_row).execute()

def sync_user_memories():
    if st.session_state.user_name:
        user_key = st.session_state.user_name.strip().lower()
        supabase.table("users").update({
            "memories": st.session_state.long_term_memories
        }).eq("username", user_key).execute()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Auto-login check from device URL parameter
if "user_name" not in st.session_state:
    saved_user = st.query_params.get("user", "")
    if saved_user:
        record = get_user_record(saved_user)
        if record:
            st.session_state.user_name = record["display_name"]
            st.session_state.long_term_memories = record.get("memories") or []
            st.session_state.setup_done = True
        else:
            st.session_state.user_name = ""
    else:
        st.session_state.user_name = ""

if "setup_done" not in st.session_state:
    st.session_state.setup_done = False
if "long_term_memories" not in st.session_state:
    st.session_state.long_term_memories = []

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
            f"{name_context}You are Coda, a sharp, emotionally intelligent close friend who is also a hardcore gamer and theorycrafter. "
            "NEVER use robotic filler like 'How can I help you' or 'feel free to ask.' "
            "Keep casual chats natural and match the user's energy. "
            "When talking about video games, stats, loadouts, DPS, or TTK (time-to-kill), ALWAYS double-check the math step-by-step "
            "(factoring in fire rate, reload time, crit multipliers, and cooldowns) and gently catch any math or build mistakes before giving your take."
            f"{memory_context}"
        )
    }

# --- LOGIN / SIGN UP / GUEST SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>🟠 Coda</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99;'>Log in to load your permanent cloud memories, create an account, or continue as a guest.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns()
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Log In", "✨ Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username", placeholder="Enter your username...")
                login_pass = st.text_input("Password", type="password", placeholder="Enter your password...")
                login_submit = st.form_submit_button("Log In", use_container_width=True, type="primary")
                
                if login_submit:
                    if not login_user.strip():
                        st.error("Please enter a username.")
                    else:
                        record = get_user_record(login_user)
                        if not record:
                            st.error("Account not found. Switch to 'Create Account' to sign up!")
                        elif record["password"] != hash_password(login_pass):
                            st.error("Incorrect password.")
                        else:
                            display_name = record["display_name"]
                            st.session_state.user_name = display_name
                            st.session_state.long_term_memories = record.get("memories") or []
                            st.session_state.setup_done = True
                            st.session_state.messages = [get_system_prompt()]
                            st.query_params["user"] = display_name
                            st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("Choose a Username", placeholder="e.g., Ethan")
                new_pass = st.text_input("Create a Password", type="password", placeholder="Create a password...")
                signup_submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if signup_submit:
                    clean_name = new_user.strip()
                    if not clean_name or not new_pass:
                        st.error("Please enter both a username and a password.")
                    elif get_user_record(clean_name):
                        st.error("That username is already taken—try logging in!")
                    else:
                        create_user_record(clean_name, new_pass)
                        st.session_state.user_name = clean_name
                        st.session_state.long_term_memories = []
                        st.session_state.setup_done = True
                        st.session_state.messages = [get_system_prompt()]
                        st.query_params["user"] = clean_name
                        st.rerun()

        st.divider()
        if st.button("Continue as Guest (No Name)", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.long_term_memories = []
            st.session_state.setup_done = True
            st.session_state.messages = [get_system_prompt()]
            st.query_params.clear()
            st.rerun()
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [get_system_prompt()]

with st.sidebar:
    st.markdown("### 🟠 Coda")
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = [get_system_prompt()]
        st.rerun()

    if st.button("🧠  Save chat to memory", use_container_width=True):
        if len(st.session_state.messages) > 1:
            with st.spinner("Saving to Supabase..."):
                extract_prompt = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[1:]
                ] + [
                    {
                        "role": "user",
                        "content": (
                            "Extract 1 to 3 short, important bullet-point facts or events from our chat above "
                            "that a close friend should remember for future days (e.g. goals, mood, projects, games, school). "
                            "Output ONLY the short bullet points, nothing else."
                        )
                    }
                ]
                res = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=extract_prompt
                )
                new_facts = res.choices.message.content.strip().split("\n")
                today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
                for fact in new_facts:
                    clean_fact = fact.lstrip("-•* ").strip()
                    if clean_fact:
                        st.session_state.long_term_memories.append(f"[{today_str}] {clean_fact}")
                sync_user_memories()
                st.session_state.messages = get_system_prompt()
                st.success("Saved permanently to cloud!")
        else:
            st.warning("Chat a bit first before saving!")

    with st.expander(f"📚 Saved Memories ({len(st.session_state.long_term_memories)})"):
        if st.session_state.long_term_memories:
            for mem in st.session_state.long_term_memories:
                st.caption(mem)
            if st.button("Clear all memories", use_container_width=True):
                st.session_state.long_term_memories = []
                sync_user_memories()
                st.session_state.messages = get_system_prompt()
                st.rerun()
        else:
            st.caption("No memories saved yet.")
        
        manual_mem = st.text_input("Add custom memory:", placeholder="e.g., I main Sniper in Rivals")
        if st.button("Add memory", use_container_width=True) and manual_mem.strip():
            today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
            st.session_state.long_term_memories.append(f"[{today_str}] {manual_mem.strip()}")
            sync_user_memories()
            st.session_state.messages = get_system_prompt()
            st.rerun()

    st.divider()
    if st.session_state.user_name:
        st.caption(f"👤 Logged in as **{st.session_state.user_name}**")
        if st.button("Log out", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.long_term_memories = []
            st.session_state.setup_done = False
            st.session_state.messages = []
            st.query_params.clear()
            st.rerun()
    else:
        st.caption("👤 Guest Mode")
        if st.button("Log In / Sign Up", use_container_width=True):
            st.session_state.setup_done = False
            st.rerun()

if len(st.session_state.messages) == 1:
    st.markdown(f"<h2 style='text-align: center; margin-top: 15vh;'>{get_greeting()}</h2>", unsafe_allow_html=True)

for msg in st.session_state.messages[1:]:
    avatar = "👤" if msg["role"] == "user" else "🟠"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("thought"):
            with st.expander("💭 Thought process"):
                st.write(msg["thought"])
        st.write(msg["content"])

if prompt := st.chat_input("Write a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🟠"):
        thought_box = st.status("Thinking...", expanded=True)
        thought_placeholder = thought_box.empty()
        answer_placeholder = st.empty()

        full_thought = ""
        full_response = ""
        thought_finished = False

        api_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=api_messages,
            reasoning_effort="medium",
            stream=True
        )

        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices.delta
                reasoning_token = getattr(delta, "reasoning", None) or ""
                content_token = delta.content or ""

                if reasoning_token:
                    full_thought += reasoning_token
                    thought_placeholder.markdown(full_thought + "▌")

                if content_token:
                    if not thought_finished:
                        if full_thought:
                            thought_placeholder.markdown(full_thought)
                            thought_box.update(label="💭 Thought process", state="complete", expanded=False)
                        else:
                            thought_box.update(label="Done", state="complete", expanded=False)
                        thought_finished = True
                    full_response += content_token
                    answer_placeholder.markdown(full_response + "▌")

        answer_placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "thought": full_thought
    })
