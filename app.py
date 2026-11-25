import streamlit as st
import ollama
import json
import os
from datetime import datetime, date

st.set_page_config(page_title="AI Model V0.04", page_icon="🟠", layout="wide")

# Custom CSS to match Claude's clean charcoal aesthetic
st.markdown("""
<style>
    /* Hide default Streamlit top header and deploy menu */
    #MainMenu, header, footer {visibility: hidden;}
    
    /* Main chat container width like Claude */
    .block-container {
        max-width: 780px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        border-right: 1px solid #333230;
    }
    
    /* User message pill styling */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #30302E;
        border-radius: 16px;
        padding: 12px 18px;
        margin-bottom: 16px;
        border: 1px solid #3D3C3A;
    }

    /* Assistant message: clean, borderless text directly on background */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: transparent;
        padding: 8px 4px;
        margin-bottom: 20px;
        border: none;
    }

    /* Thinking expander box styling */
    [data-testid="stStatusWidget"] {
        background-color: #1F1E1D;
        border: 1px solid #383735;
        border-radius: 10px;
    }

    /* Floating rounded chat input box */
    [data-testid="stChatInput"] {
        background-color: #30302E !important;
        border: 1px solid #454441 !important;
        border-radius: 18px !important;
    }
    
    /* Subtle sidebar buttons */
    [data-testid="stSidebar"] button {
        border-radius: 8px;
        border: 1px solid #383735;
        background-color: #262624;
        text-align: left;
    }
    [data-testid="stSidebar"] button:hover {
        border-color: #D97757;
        color: #D97757;
    }
</style>
""", unsafe_allow_html=True)

# Folder to save past chats so the sidebar works like Claude's "Chats" list
CHAT_DIR = "saved_chats"
os.makedirs(CHAT_DIR, exist_ok=True)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are my close friend texting me casually. "
        "NEVER say 'How can I help you', 'feel free to ask', or act like a customer service bot. "
        "Keep replies natural, thoughtful, and conversational. "
        "If I ask how your day was, share a relatable mini-story (gaming, music, coding, chilling) and ask about mine."
    )
}

def save_current_chat():
    if len(st.session_state.messages) > 1:
        filepath = os.path.join(CHAT_DIR, f"{st.session_state.chat_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "title": st.session_state.chat_title,
                "messages": st.session_state.messages
            }, f, indent=2)

# Initialize session state
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.chat_title = "New conversation"
    st.session_state.messages = [SYSTEM_PROMPT]

# --- SIDEBAR (Claude Layout) ---
with st.sidebar:
    st.markdown("### 🟠 AI Model V0.04")
    
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.chat_title = "New conversation"
        st.session_state.messages = [SYSTEM_PROMPT]
        st.rerun()

    if st.button("📝  Summarize today", use_container_width=True):
        if len(st.session_state.messages) > 1:
            summary_prompt = st.session_state.messages + [
                {"role": "user", "content": "Summarize our chat today into: 1) Key Highlights, 2) Overall Mood, and 3) Things to remember for tomorrow."}
            ]
            raw_summary = ollama.chat(model="deepseek-r1:1.5b", messages=summary_prompt)["message"]["content"]
            clean_summary = raw_summary.split("</think>")[-1].strip()
            filename = f"journal_{date.today()}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(clean_summary)
            st.success(f"Saved {filename}")
            st.caption(clean_summary)

    st.markdown("---")
    st.caption("Chats")
    
    # List saved chats in sidebar
    saved_files = sorted(os.listdir(CHAT_DIR), reverse=True)
    for file in saved_files[:10]:
        if file.endswith(".json"):
            with open(os.path.join(CHAT_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)
            if st.button(data.get("title", file), key=file, use_container_width=True):
                st.session_state.chat_id = file.replace(".json", "")
                st.session_state.chat_title = data.get("title", "Chat")
                st.session_state.messages = data["messages"]
                st.rerun()

    st.markdown("---")
    st.caption("👤 Ethan  •  Local `deepseek-r1:1.5b`")

# --- MAIN CHAT AREA ---
if len(st.session_state.messages) == 1:
    st.markdown("<h2 style='text-align: center; color: #ECEBE8; margin-top: 15vh; font-weight: 500;'>Good evening, Ethan</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9E9D99; margin-bottom: 2rem;'>How did your day go?</p>", unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages[1:]:
    avatar = "👤" if msg["role"] == "user" else "🟠"
    with st.chat_message(msg["role"], avatar=avatar):
        content = msg["content"]
        if "</think>" in content:
            thought, answer = content.split("</think>", 1)
            with st.expander("Thought process"):
                st.write(thought.replace("<think>", "").strip())
            st.write(answer.strip())
        else:
            st.write(content)

# Chat input
if prompt := st.chat_input("Write a message..."):
    # Auto-name the chat in the sidebar based on your first message
    if st.session_state.chat_title == "New conversation":
        st.session_state.chat_title = prompt[:28] + ("..." if len(prompt) > 28 else "")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🟠"):
        thought_box = st.status("Thinking...", expanded=True)
        thought_placeholder = thought_box.empty()
        answer_placeholder = st.empty()

        full_response = ""
        in_thought = False

        stream = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=st.session_state.messages,
            stream=True
        )

        for chunk in stream:
            token = chunk["message"]["content"]
            full_response += token

            if "<think>" in full_response and "</think>" not in full_response:
                clean_thought = full_response.replace("<think>", "")
                thought_placeholder.markdown(clean_thought + "▌")
            elif "</think>" in full_response:
                if not in_thought:
                    thought_box.update(label="Thought process", state="complete", expanded=False)
                    in_thought = True
                thought_part, answer_part = full_response.split("</think>", 1)
                thought_placeholder.markdown(thought_part.replace("<think>", "").strip())
                answer_placeholder.markdown(answer_part.strip() + "▌")
            else:
                answer_placeholder.markdown(full_response + "▌")

        if "</think>" in full_response:
            _, final_answer = full_response.split("</think>", 1)
            answer_placeholder.markdown(final_answer.strip())
        else:
            thought_box.update(label="Done", state="complete", expanded=False)
            answer_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_current_chat()
