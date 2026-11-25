import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Model V0.05", page_icon="🟠", layout="wide")

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

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are my close friend texting me casually. "
        "NEVER say 'How can I help you' or act like a customer service bot. "
        "Keep replies natural, thoughtful, and conversational."
    )
}

if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]

with st.sidebar:
    st.markdown("### 🟠 AI Model V0.05")
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = [SYSTEM_PROMPT]
        st.rerun()

if len(st.session_state.messages) == 1:
    st.markdown("<h2 style='text-align: center; margin-top: 15vh;'>Good evening, Ethan</h2>", unsafe_allow_html=True)

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
            token = chunk.choices[0].delta.content or ""
            full_response += token
            placeholder.markdown(full_response + "▌")
        placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
