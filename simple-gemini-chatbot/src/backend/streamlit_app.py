"""Streamlit UI code"""
# pylint: disable=line-too-long, invalid-name, no-name-in-module
import streamlit as st
from bot.chat import get_stream_response, on_model_change, initialize_model
from ml_config import MODELS, ALLOWED_FILE_TYPES
from utils.utility import process_chat_history, convert_to_multimodal_message

st.set_page_config(page_title="Simple Chat App")
st.title("Simple Chat App")

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'model_key' not in st.session_state:
    st.session_state['model_key'] = MODELS[0]

initialize_model()

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False

def new_session():
    """Reinitialize all session variables"""
    st.session_state['messages'] = []
    st.session_state['model_key'] = MODELS[0]
    st.session_state.uploaded_files = []
    st.session_state.clear_uploader = True

with st.sidebar:
    st.header("Settings")
    st.button("New Session", on_click=new_session, icon=":material/add_circle:")
    st.selectbox(label="Choose Model", options=MODELS, key="model_key", on_change=on_model_change)
    if st.session_state.clear_uploader:
        st.session_state.clear_uploader = False
        uploaded_files = None

    uploaded_files = st.file_uploader(
        label="Upload File",
        type=ALLOWED_FILE_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"file_uploader_{len(st.session_state.messages)}"
    )
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files

for message in st.session_state.messages:
    role, content, attachments =  message.get("role"), message.get("display_content"), message.get("attachments")
    with st.chat_message(role):
        st.markdown(content)
        if attachments:
            for attachment in attachments:
                st.markdown(attachment)

user_input = st.chat_input("Type your message here.")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
        attachments = []
        for uploaded_file in st.session_state.uploaded_files:
            st.write(f"📄 {uploaded_file.name}")
            attachments.append(f"📄 {uploaded_file.name}")

    with st.chat_message("assistant"):
        chat_history = process_chat_history(st.session_state.messages)
        try:
            user_uploads = st.session_state.uploaded_files

            if user_uploads:
                contents = [user_input, user_uploads]
            else:
                contents = [user_input]
            with st.spinner("Generating response...", show_time=True):
                response = st.write_stream(get_stream_response(contents, chat_history))

            st.session_state.messages.append(convert_to_multimodal_message("user", contents, attachments))
            st.session_state.messages.append(convert_to_multimodal_message("assistant", [response]))

            st.session_state.uploaded_files = []
            st.session_state.clear_uploader = True
            st.rerun()
        except Exception as e: # pylint: disable=W0718
            st.error(e)
            print(e)
