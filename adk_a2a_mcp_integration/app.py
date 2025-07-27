# app.py

import streamlit as st
import uuid
import asyncio
from root_agent.response_manager import ResponseManager

# --- Page Configuration ---
st.set_page_config(page_title="Agent Response Manager", layout="wide")

# --- Session State Initialization ---
if "response_manager" not in st.session_state:
    st.session_state.response_manager = ResponseManager()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.toast(f"New session created: {st.session_state.session_id}")
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.title("Settings")
    st.markdown(f"**Session ID:**\n`{st.session_state.session_id}`")

    if st.button("New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.toast(f"New session started: {st.session_state.session_id}")
        st.rerun()

    st.divider()
    diagnostics_enabled = st.checkbox("Enable Diagnostics", value=True)

# --- Main Chat Interface ---
st.title("Agent Chat UI")

# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if diagnostics_enabled and "diagnostics" in message and message["diagnostics"]:
            with st.expander("View Diagnostics for this response."):
                st.json(message["diagnostics"])

# --- Coroutine to handle agent invocation and UI updates ---
async def run_agent_and_display(prompt: str):
    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Assistant's turn ---
    with st.chat_message("assistant"):
        final_response_text = ""
        diagnostic_events = []
        status_messages = {
            "tool_call": "Calling tool... 🛠️",
            "tool_response": "Processing tool result... ⚙️",
            "finished": "Response generation complete. ✅"
        }

        status_placeholder = st.empty()
        try:
            # Collect all events and the final response from the agent
            status_placeholder.text("Thinking... 🤔")
            async for event in st.session_state.response_manager.invoke_agent(
                session_id=st.session_state.session_id, query=prompt
            ):
                status_text = status_messages.get(event.get("status"), f"Processing: {event.get('status')}")
                status_placeholder.text(status_text)
                
                diagnostic_events.append(event.get("event"))
                if event.get("is_final_response"):
                    final_response_text = event.get("result", "Sorry, I couldn't generate a response.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            final_response_text = "Sorry, I ran into an error."

        status_placeholder.empty()
        st.markdown(final_response_text)
        
        if diagnostics_enabled and diagnostic_events:
            with st.expander("View Diagnostics for this response."):
                st.json(diagnostic_events)

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_response_text,
        "diagnostics": diagnostic_events
    })

# --- Handle User Input ---
if prompt := st.chat_input("What are some trending topics in AI?"):
    asyncio.run(run_agent_and_display(prompt))