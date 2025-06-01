"""Code for chat handling logic"""
# pylint: disable=W1203, R1737, no-name-in-module
import logging
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY
from ml_config import LLM_CONFIGS, MODELS
from utils.utility import convert_to_multimodal_message

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def initialize_model():
    """Initialize model in session state"""
    if 'model' not in st.session_state:
        st.session_state['model'] = ChatGoogleGenerativeAI(**LLM_CONFIGS[MODELS[0]],
                                                           google_api_key=GEMINI_API_KEY)

def on_model_change():
    """Callback for model change"""
    model_key =str(st.session_state.model_key)
    st.session_state['model'] = ChatGoogleGenerativeAI(**LLM_CONFIGS[model_key],
                                                       google_api_key=GEMINI_API_KEY)

    logger.info(f"Model updated to : {model_key}")

def get_response(user_input, chat_history):
    """Get response from llm"""
    messages = chat_history + [convert_to_multimodal_message(role="user",
                                                             contents=user_input, for_llm=True)]

    response = st.session_state.model.invoke(messages)

    return response.content

def get_stream_response(user_input, chat_history):
    """Get streaming response from llm"""
    # logger.info(user_input)
    messages = chat_history + [convert_to_multimodal_message(role="user",
                                                             contents=user_input, for_llm=True)]

    response = st.session_state.model.stream(messages)

    for chunk in response:
        yield chunk
