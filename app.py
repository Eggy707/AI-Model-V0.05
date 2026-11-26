import streamlit as st
from groq import Groq
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib

st.set_page_config(page_title="Coda", page_icon="🟠", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
SB_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SB_KEY = st.secrets["SUPABASE_KEY"]
SB_HEADERS = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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

# --- SMART CLOUD-FRIENDLY SEARCH (Never blocked on Streamlit Cloud) ---
def needs_search(text):
    clean = text.strip().lower()
    casual_greetings = {
        "hi", "hello", "hey", "yo", "sup", "what's up", "whats up",
        "good morning", "good afternoon", "good evening", "gm", "gn",
        "thanks", "thank you", "ok", "okay", "lol", "lmao", "nice", "cool"
    }
    if clean in casual_greetings or len(clean) < 6:
        return False
    search_triggers = [
        "tier", "tank", "wot", "world of tanks", "dps", "dpm", "ttk", "stats", "nerf", "buff", "patch",
        "update", "build", "loadout", "meta", "weapon", "gun", "armor", "penetration", "reload", "damage",
        "who is", "what is", "when is", "how much", "price", "release", "news", "weather", "score", "?"
    ]
    return any(word in clean for word in search_triggers)

def quick_web_search(query):
    try:
        url = "https://wikipedia.org"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 3
        }
        headers = {"User-Agent": "CodaPersonalApp/1.0"}
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            hits = res.json().get("query", {}).get("search", [])
            if hits:
                snippets = []
                for h in hits:
                    clean_snippet = h.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    snippets.append(f"- {h.get('title', '')}: {clean_snippet}")
                return "\n".join(snippets)
    except Exception:
        pass
    return ""

# --- SUPABASE DIRECT REST HELPERS ---
def get_user_record(username):
    user_key = username.strip().lower()
    url = f"{SB_URL}/rest/v1/users?username=eq.{user_key}&select=*"
    res = requests.get(url, headers=SB_HEADERS)
    if res.status_code == 200:
        rows = res.json()
        return next(iter(rows), None)
    return None

def create_user_record(username, password):
    clean_name = username.strip()
    user_key = clean_name.lower()
    new_row = {
        "username": user_key,
        "display_name": clean_name,
        "password": hash_password(password),
        "memories": []
    }
    res = requests.post(f"{SB_URL}/rest/v1/users", headers=SB_HEADERS, json=new_row)
    if res.status_code in (200, 201):
        return True, ""
    return False, f"Database error ({res.status_code}): {res.text}"

def sync_user_memories():
    if st.session_state.user_name:
        user_key = st.session_state.user_name.strip().lower()
        url = f"{SB_URL}/rest/v1/users?username=eq.{user_key}"
        requests.patch(url, headers=SB_HEADERS, json={"memories": st.session_state.long_term_memories})

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
            "NEVER ask the user to paste search snippets or external data—if [Live Web Search Context] is attached to the message, use it; "
            "otherwise, answer confidently using your own knowledge and double-check all game math (DPS, DPM, reload times, tiers) step-by-step."
            f"{memory_context}"
        )
    }

# --- LOGIN / SIGN UP / GUEST SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>🟠 Coda</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99;'>Log in to load your permanent cloud memories, create an account, or continue as a guest.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
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
                        ok, err_msg = create_user_record(clean_name, new_pass)
                        if not ok:
                            st.error(err_msg)
                        else:
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
                    model="openai/gpt-oss-20b",
                    messages=extract_prompt
                )
                first_choice = next(iter(res.choices))
                new_facts = first_choice.message.content.strip().split("\n")
                today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
                for fact in new_facts:
                    clean_fact = fact.lstrip("-•* ").strip()
                    if clean_fact:
                        st.session_state.long_term_memories.append(f"[{today_str}] {clean_fact}")
                sync_user_memories()
                st.session_state.messages = [get_system_prompt()] + st.session_state.messages[1:]
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
                st.session_state.messages = [get_system_prompt()] + st.session_state.messages[1:]
                st.rerun()
        else:
            st.caption("No memories saved yet.")
        
        manual_mem = st.text_input("Add custom memory:", placeholder="e.g., I grind Tier 9 heavies in WoT")
        if st.button("Add memory", use_container_width=True) and manual_mem.strip():
            today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
            st.session_state.long_term_memories.append(f"[{today_str}] {manual_mem.strip()}")
            sync_user_memories()
            st.session_state.messages = [get_system_prompt()] + st.session_state.messages[1:]
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
        should_search = needs_search(prompt)
        status_label = "Searching & thinking..." if should_search else "Thinking..."
        thought_box = st.status(status_label, expanded=True)
        thought_placeholder = thought_box.empty()
        answer_placeholder = st.empty()

        web_snippets = quick_web_search(prompt) if should_search else ""
        full_thought = f"**Web search notes:**\n{web_snippets}\n\n" if web_snippets else ""
        if full_thought:
            thought_placeholder.markdown(full_thought)

        full_response = ""
        thought_finished = False

        recent_history = st.session_state.messages[1:][-8:]
        api_messages = [get_system_prompt()] + [
            {"role": m["role"], "content": m["content"]}
            for m in recent_history
        ]
        if web_snippets:
            api_messages[-1]["content"] += f"\n\n[Live Web Search Context:\n{web_snippets}]"

        try:
            stream = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=api_messages,
                reasoning_effort="medium",
                stream=True
            )
        except Exception:
            stream = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=api_messages,
                reasoning_effort="medium",
                stream=True
            )

        for chunk in stream:
            for choice in chunk.choices:
                delta = choice.delta
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
