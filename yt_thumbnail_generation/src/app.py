"""Streamlit UI for thumbnail generator"""
# pylint: disable=line-too-long,invalid-name

import os
from datetime import datetime, timedelta, timezone
from typing import Union, List, Dict, Any
import streamlit as st
from video_processor.processor import get_video_data
from utils.utility import construct_contents
from core.video_analyzer import VideoAnalyzer
from core.prompt_generator import PromptGenerator
from core.image_generator import ImageGenerator
from core.image_editor import ImageEditor
from core.prompts import video_analyzer_prompt, imagen_prompt_generator

from google import genai

ist_offset = timezone(timedelta(seconds=19800))

st.set_page_config(page_title="Youtube Thumbnail Generator", layout="wide")
st.title("Youtube Thumbnail Generator")

with st.sidebar:
    st.header("Config")
    prompt_model_selector = st.selectbox(
        "Prompt Generation Model",
        ("gemini-2.0-flash-001", "gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-06-05"),
        key="prompt_model"
    )

    image_gen_model_selector = st.selectbox(
        "Image Generation Model",
        ("gemini-2.0-flash-preview-image-generation", "imagen-3.0-generate-002"),
        key="image_model"
    )

    api_key = st.text_input(
        label="Gemini API Key",
        type="password",
        placeholder="Enter your Gemini API Key",
        key="api_key",
        # value="" #Add key for testing or in UI
    )

    # st.header("Workflow Mode")
    # workflow_mode = st.radio(
    #     "Choose processing mode:",
    #     ("Edit & Review", "Automated"),
    #     key="workflow_mode",
    #     disabled=False
    # )
    enable_chat_edit = st.checkbox(
        "Enable Inline Chat Editing",
        value=False,
        key="enable_chat_edit"
    )

video_url_input = st.text_input(
    label="Youtube Video URL",
    placeholder="https://www.youtube.com/watch?v=2lAe1cqCOXo",
    key="video_url"
)

num_snapshots_input = st.number_input(
    label="Number of Snapshots (for videos > 2 mins)",
    min_value=3,
    max_value=30,
    value=5,
    step=1,
    key="num_snapshots"
)

# --- Initialize session state variables ---
if 'video_processor_progress' not in st.session_state:
    st.session_state.video_processor_progress = None
if 'video_processed' not in st.session_state:
    st.session_state.video_processed = False
if 'video_title' not in st.session_state:
    st.session_state.video_title = ""
if 'media_paths' not in st.session_state:
    st.session_state.media_paths = []
if 'video_metadata' not in st.session_state:
    st.session_state.video_metadata = {}
if 'video_downloaded_path' not in st.session_state:
    st.session_state.video_downloaded_path = None
if 'video_description' not in st.session_state:
    st.session_state.video_description = ""
if 'description_generated' not in st.session_state:
    st.session_state.description_generated = False
if 'image_prompt' not in st.session_state:
    st.session_state.image_prompt = ""
if 'prompt_generated' not in st.session_state:
    st.session_state.prompt_generated = False
if 'generated_image_path' not in st.session_state:
    st.session_state.generated_image_path = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""
if 'video_analyzer' not in st.session_state:
    st.session_state.video_analyzer = ""
if 'imagen_prompter' not in st.session_state:
    st.session_state.imagen_prompter = ""
if 'image_generator' not in st.session_state:
    st.session_state.image_generator = ""
if 'image_editor' not in st.session_state:
    st.session_state.image_editor = ""

def validate_api_key(apikey: str):
    """Validate api key"""
    if not apikey:
        return False, "API Key is missing."
    if not apikey.startswith("AIza") or len(apikey) < 30:
        return False, "API Key is invalid."

    client = genai.Client(api_key=apikey)

    return True, client

def get_video_info_and_process(url: str, num_snaps: int=5):
    """Video processing logic
    Returns: (success_flag, message, media_paths, video_metadata, downloaded_path)
    """

    if not url:
        st.session_state.error_message = "Please enter a YouTube video URL."
        return False, st.session_state.error_message, [], {}, None

    if "invalid" in url.lower():
        st.session_state.error_message = "Could not process the video URL. Please check and try again."
        return False, st.session_state.error_message, [], {}, None

    try:
        video_metadata, media_path = get_video_data(url=url, num_snaps=num_snaps)
        st.session_state.video_title = video_metadata.get("title")

        if isinstance(media_path, list):
            st.session_state.media_paths = media_path
            st.session_state.video_metadata = video_metadata
            st.session_state.video_downloaded_path = None
            return True, "Snapshots taken.", media_path, video_metadata, None
        if isinstance(media_path, str):
            st.session_state.video_downloaded_path = media_path
            st.session_state.video_metadata = video_metadata
            st.session_state.media_paths = []
            return True, "Video downloaded successfully.", [], video_metadata, media_path
        return False, "File too big", [], {}, ""
    except Exception as e:
        return False, f"Error occured while processing video: {e}", [], {}, ""

def generate_description_from_video_data(video_metadata: dict, media_content: str, model: str=""):
    """Wrapper to generate video desciption from metadata and media contents"""
    message_content = construct_contents(video_metadata, media_content)

    video_description, status = st.session_state.video_analyzer.get_gemini_response(message_content, model)
    if video_description:
        return True, "Description generated.", video_description
    else:
        return False, f"Error occured while generating video description: {status}", ""

def generate_prompt_from_description(description: str, model: str=""):
    """Wrapper to generate prompt from video description"""
    imagen_prompt, status = st.session_state.imagen_prompter.get_imagen_prompt(description, model)
    if imagen_prompt:
        return True, "Image prompt generated.", imagen_prompt
    else:
        return False, f"Error occured while generating image generation prompt: {status}", ""

def generate_image_from_prompt(prompt: str, title: str, model: str=""):
    """Wrapper to generate image from prompt"""
    try:
        image_result = st.session_state.image_generator.generate_image(prompt, title, model)
        if image_result:
            return True, "Thumbnail image generated successfully!", image_result
        return False, "Something went wrong while generating image, please try again.", None
    except Exception as e:
        st.session_state.error_message = f"Error occured while generating image: {e}"
        return False, st.session_state.error_message, None

def handle_chat_editing(message: Union[List[Dict[str, Any]], str], title: str, history: list):
    """Wrapper to handle chat session and image editing"""
    try:
        response, status = st.session_state.image_editor.chat_session(message, history)
        if response:
            text, media = st.session_state.image_editor.serialize_response(response, title, str(len(history)))
            return text, media
        else:
            return f"Error occured during chat processing: {status}", None
    except Exception as e:
        return f"Error during chat processing: {e}", None

def update_chat_history(msg_role: str, msg_text=None, msg_media=None):
    """Updates chat history in session state"""
    msg_content = {}

    if msg_text:
        msg_content["text"] = msg_text
    if msg_media:
        msg_content["media"] = msg_media

    if msg_content:
        st.session_state.chat_history.append({
            "role": msg_role,
            "content": msg_content
        })
        print(f"History: {st.session_state.chat_history}")
        return True
    return False

# --- Main Workflow ---

col1_btn, col2_btn_clear = st.columns([3,1])
with col1_btn:
    analyze_button_clicked = st.button("Begin", type="primary", use_container_width=True, disabled=not st.session_state.api_key)
with col2_btn_clear:
    if st.button("Reset Workflow", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ['api_key', 'prompt_model', 'image_model', 'workflow_mode', 'video_url', 'num_snapshots']:
                del st.session_state[key]
        st.rerun()

if not st.session_state.api_key:
    st.warning("Missing Gemini API key")

if st.session_state.error_message:
    st.error(f"Erorr: {st.session_state.error_message}")
    st.session_state.error_message = ""

# --- Video Processing & Snapshots ---
with st.expander("Step 1: Video Processing", expanded=True):
    if analyze_button_clicked and st.session_state.api_key and st.session_state.video_url:
        is_key_valid, result = validate_api_key(st.session_state.api_key)
        if not is_key_valid:
            st.error(result)
        else:
            st.session_state.video_analyzer = VideoAnalyzer(
                client=result,
                system_instructions=video_analyzer_prompt
            )

            st.session_state.imagen_prompter = PromptGenerator(
                client=result,
                system_instructions=imagen_prompt_generator
            )

            st.session_state.image_generator = ImageGenerator(
                client=result
            )
            st.session_state.image_editor = ImageEditor(
                client=result
            )
            with st.spinner("Processing video, this might take a while..."):
                success, msg, paths, metadata, dl_path = get_video_info_and_process(
                    st.session_state.video_url,
                    st.session_state.num_snapshots
                )
                if success:
                    st.session_state.video_processed = True
                    st.session_state.media_paths = paths
                    st.session_state.video_metadata = metadata
                    st.session_state.video_downloaded_path = dl_path
                    st.success(msg)
                else:
                    st.error(msg)
                    st.session_state.video_processed = False

    if st.session_state.video_processed:
        if st.session_state.media_paths:
            st.subheader("Snapshots")
            st.info("Snapshots of the video.")

            # Which snapshots to display (e.g., first, middle, last)
            num_to_show = len(st.session_state.media_paths)
            indices_to_show = []
            if num_to_show == 0:
                pass
            elif num_to_show <= 5: # Show all if 5 or less
                indices_to_show = list(range(num_to_show))
            else: # Show first, some middle ones, and last, max 5
                indices_to_show.append(0) # First
                # Middle ones - spread them out
                if num_to_show > 2:
                    indices_to_show.append(num_to_show // 4)
                if num_to_show > 1:
                    indices_to_show.append(num_to_show // 2)
                if num_to_show > 3:
                    indices_to_show.append(num_to_show * 3 // 4)
                indices_to_show.append(num_to_show - 1) # Last
                indices_to_show = sorted(list(set(indices_to_show)))
                indices_to_show = indices_to_show[:5] # Cap at 5 images

            cols = st.columns(len(indices_to_show) if indices_to_show else 1)
            for i, snap_idx in enumerate(indices_to_show):
                path = st.session_state.media_paths[snap_idx]
                if os.path.exists(path):
                    cols[i].image(path, caption=f"Snapshot {snap_idx + 1}", use_container_width=True)
                else:
                    cols[i].warning(f"Snapshot {snap_idx+1} not found.")

        elif st.session_state.video_downloaded_path:
            st.subheader("Video Downloaded")
            st.success(f"Video downloaded to: `{st.session_state.video_downloaded_path}`")

        if st.button("Proceed to Generate Description", disabled=not st.session_state.video_processed):
            st.session_state.description_generated = False # Reset for regeneration if needed
            st.session_state.prompt_generated = False
            st.session_state.generated_image_path = None
            st.rerun()

# --- Video Description ---
with st.expander("Step 2: Generate Video Description", expanded=st.session_state.video_processed and not st.session_state.description_generated):
    if st.session_state.video_processed:
        if not st.session_state.description_generated:
            with st.spinner("Generating video description..."):
                media_data = st.session_state.media_paths if st.session_state.media_paths else st.session_state.video_downloaded_path
                success, msg, desc = generate_description_from_video_data(
                    st.session_state.video_metadata,
                    media_data,
                    st.session_state.prompt_model
                )
                if success:
                    st.session_state.video_description = desc
                    st.session_state.description_generated = True
                    st.success(msg)
                else:
                    st.error(msg)
                    st.session_state.description_generated = False

        if st.session_state.description_generated:
            st.subheader("Video Description")
            edited_description = st.text_area(
                "Review and edit the generated description:",
                value=st.session_state.video_description,
                height=150,
                key="edited_desc"
            )
            st.session_state.video_description = edited_description # Keep it updated

            if st.button("Use Description to Generate Prompt", disabled=not edited_description.strip()):
                st.session_state.prompt_generated = False # Reset for regeneration
                st.session_state.generated_image_path = None
                st.rerun()

# --- Image Prompt Generation ---
with st.expander("Step 3: Generate Image Prompt", expanded=st.session_state.description_generated and not st.session_state.prompt_generated):
    if st.session_state.description_generated and st.session_state.video_description:
        if not st.session_state.prompt_generated:
            with st.spinner("Generating image prompt..."):
                success, msg, prompt_text = generate_prompt_from_description(
                    st.session_state.video_description,
                    st.session_state.prompt_model
                )
                if success:
                    st.session_state.image_prompt = prompt_text
                    st.session_state.prompt_generated = True
                    st.success(msg)
                else:
                    st.error(msg)
                    st.session_state.prompt_generated = False

        if st.session_state.prompt_generated:
            st.subheader("Image Generation Prompt")
            edited_prompt = st.text_area(
                "Review and edit the image generation prompt:",
                value=st.session_state.image_prompt,
                height=200,
                key="edited_prompt"
            )
            st.session_state.image_prompt = edited_prompt # Keep it updated
            col_generate, col_download = st.columns([3, 1])

            with col_generate:
                if st.button(
                    "Generate Thumbnail Image with this Prompt",
                    type="primary",
                    disabled=not edited_prompt.strip(),
                    use_container_width=True
                ):
                    st.session_state.generated_image_path = None # Reset
                    st.rerun()
            with col_download:
                st.download_button(
                    label="Download this Prompt",
                    data=st.session_state.image_prompt,
                    file_name=f"{st.session_state.video_title}_prompt.txt" if st.session_state.video_title else "prompt.txt",
                    mime="text/plain",
                    use_container_width=True,
                    disabled=not edited_prompt.strip()
                )

# --- Final Thumbnail Generation ---
with st.expander("Step 4: Generate Thumbnail", expanded=st.session_state.prompt_generated and st.session_state.image_prompt and not st.session_state.generated_image_path):
    if st.session_state.prompt_generated and st.session_state.image_prompt:
        # This block will execute if the "Generate Thumbnail Image" button was clicked or if we are re-running into this state
        if not st.session_state.generated_image_path: # Only generate if not already done
            with st.spinner(f"Generating thumbnail using {st.session_state.image_model}..."):
                curr_timestamp = datetime.now(ist_offset).strftime("%H%M_%d%m%Y")
                versioned_image_title = f"{st.session_state.video_title}_{curr_timestamp}"
                success, msg, img_path = generate_image_from_prompt(
                    st.session_state.image_prompt,
                    versioned_image_title,
                    st.session_state.image_model,
                )
                if success:
                    st.session_state.generated_image_path = img_path
                    st.success(msg)
                else:
                    st.error(msg)
                    st.session_state.generated_image_path = None

        if st.session_state.generated_image_path:
            st.subheader("Generated Thumbnail!")
            if os.path.exists(st.session_state.generated_image_path):
                st.image(st.session_state.generated_image_path, caption="Final Thumbnail")
                with open(st.session_state.generated_image_path, "rb") as file:
                    st.download_button(
                        label="Download Thumbnail",
                        data=file,
                        file_name=os.path.basename(st.session_state.generated_image_path),
                        mime="image/png"
                    )
            else:
                st.error("Generated image file not found. Something went wrong.")
            st.markdown("##### Want to make changes to this image? Enable inline chat editing from the sidebar.")

# --- Editing Generated Thumbnail ---
if st.session_state.generated_image_path and st.session_state.enable_chat_edit:
    with st.expander("Step 5: Edit Thumbnail via Chat", expanded=True):
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        col_chat, col_reset = st.columns([4, 1])
        with col_chat:
            st.markdown("### Need to improve this image?")
        with col_reset:
            if st.button("Reset Chat", key="reset_chat_btn"):
                st.session_state.chat_history = []
                st.rerun()
        with st.container():
            for i, msg in enumerate(st.session_state.chat_history):
                role = msg["role"]
                if role == "model":
                    role = "assistant"
                with st.chat_message(role):
                    content = msg["content"]
                    if content.get("text"):
                        st.markdown(content["text"])
                    if content.get("media") and os.path.exists(content["media"]):
                        if role == "user":
                            st.image(content["media"], caption="Input Image", width=480)
                        elif role == "assistant":
                            col_img, col_dl = st.columns([1, 1])
                            with col_dl:
                                with open(content["media"], "rb") as img_file:
                                    st.download_button(
                                        label="",
                                        icon=":material/download:",
                                        data=img_file,
                                        file_name=os.path.basename(content["media"]),
                                        mime="image/png",
                                        key=f"download_btn_{i}",
                                        help="Download this image"
                                    )
                            with col_img:
                                st.image(content["media"], caption="Generated Image", use_container_width=True)

        user_message = st.chat_input("Need to add text, change style? Anything you want to change, just ask.")
        if user_message:
            image_title_in_chatmode = st.session_state.generated_image_path.split("\\")[-1].split(".")[0] # for windows
            with st.spinner("Editing image based on your input..."):
                if len(st.session_state.chat_history) == 0:
                    first_message = [
                        {
                            "role": "user",
                            "content": {
                                "text": user_message,
                                "media": st.session_state.generated_image_path
                            }
                        }
                    ]
                    response_text, response_media = handle_chat_editing(message=first_message,
                                                                        title=image_title_in_chatmode,
                                                                        history=st.session_state.chat_history)
                    update_chat_history(msg_role="user",
                                        msg_text=first_message[0]["content"]["text"],
                                        msg_media=first_message[0]["content"]["media"])
                else:
                    response_text, response_media = handle_chat_editing(message=user_message,
                                                                        title=image_title_in_chatmode,
                                                                        history=st.session_state.chat_history)
                    update_chat_history(msg_role="user", msg_text=user_message)
                update_chat_history(msg_role="model", msg_text=response_text, msg_media=response_media)
            st.rerun()
