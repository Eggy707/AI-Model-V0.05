import streamlit as st
from groq import Groq
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="AI Model V0.08", page_icon="🟠", layout="wide")

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

# Initialize session states
if "user_name" not in st.session_state:
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
    
    # Inject saved long-term memories into the AI's brain
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

# --- ACCOUNT CREATION / SKIP SCREEN ---
if not st.session_state.setup_done:
    st.markdown("<h2 style='text-align: center; margin-top: 12vh;'>🟠 Welcome to AI Model V0.08</h2>", unsafe_allow_html=True)
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
    st.markdown("### 🟠 AI Model V0.08")
    if st.button("＋  New chat", use_container_width=True):
        # Refresh system prompt so new chat loads all saved memories
        st.session_state.messages = [get_system_prompt()]
        st.rerun()

    # Button to extract and save memories from current conversation
    if st.button("🧠  Save chat to memory", use_container_width=True):
        if len(st.session_state.messages) > 1:
            with st.spinner("Saving memories..."):
                extract_prompt = st.session_state.messages[1:] + [
                    {
                        "role": "user",
                        "content": (
                            "Extract 1 to 3 short, important bullet-point facts or events from our chat above "
                            "that a close friend should remember for future days (e.g. goals, mood, projects, school/work). "
                            "Output ONLY the short bullet points, nothing else."
                        )
                    }
                ]
                res = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=extract_prompt
                )
                new_facts = res.choices[0].message.content.strip().split("\n")
                today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
                for fact in new_facts:
                    clean_fact = fact.lstrip("-•* ").strip()
                    if clean_fact:
                        st.session_state.long_term_memories.append(f"[{today_str}] {clean_fact}")
                # Update active chat's system prompt immediately
                st.session_state.messages[0] = get_system_prompt()
                st.success("Saved to long-term memory!")
        else:
            st.warning("Chat a bit first before saving!")

    # View & manage saved memories
    with st.expander(f"📚 Saved Memories ({len(st.session_state.long_term_memories)})"):
        if st.session_state.long_term_memories:
            for i, mem in enumerate(st.session_state.long_term_memories):
                st.caption(mem)
            if st.button("Clear all memories", use_container_width=True):
                st.session_state.long_term_memories = []
                st.session_state.messages[0] = get_system_prompt()
                st.rerun()
        else:
            st.caption("No memories saved yet. Chat and click 'Save chat to memory'!")
        
        manual_mem = st.text_input("Add custom memory:", placeholder="e.g., I have a math test Friday")
        if st.button("Add memory", use_container_width=True) and manual_mem.strip():
            today_str = datetime.now(ZoneInfo("America/Vancouver")).strftime("%b %d")
            st.session_state.long_term_memories.append(f"[{today_str}] {manual_mem.strip()}")
            st.session_state.messages[0] = get_system_prompt()
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
