"""Utility files for common functions"""
# pylint: disable=consider-using-with
import re
import os
import base64
import requests
from google.genai import types

def clean_title(title_str):
    """Clean the video title"""
    title = re.sub(r'[\\/*?:"<>|]', '_', title_str) # special chars
    title = re.sub(r'[^\x00-\x7F]+', '', title) # no ascii
    title = re.sub(r'\s+', '_', title) # whitespaces
    title = re.sub(r'_+', '_', title) # collapse multiple underscores
    title = title.strip('_') # trim underscores

    return title

def strip_escape_seqs(text):
    """Strip all ansi escape seqs that are received while downloading callback"""
    ansi_escape_chars = re.compile(r'(?:\x1b\[|\x9b)[0-?]*[ -/]*[@-~]')
    return ansi_escape_chars.sub('', text)

def get_file_data(file_path):
    """Convert file data to base64"""
    try:
        file_content = open(file_path, 'rb').read()
        file_data = base64.b64encode(file_content).decode("utf-8")
        return file_data
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def save_binary_file(file_name, data, thumbnails_dir = "thumbnails"):
    """Save the image to thumbnails dir"""
    if not os.path.exists(thumbnails_dir):
        os.makedirs(thumbnails_dir)
        print(f"Created thumbnails directory: {thumbnails_dir}")

    file_path = os.path.join(thumbnails_dir, file_name)
    file = open(file_path, "wb")
    file.write(data)
    file.close()

    print(f"File saved to to: {file_path}")
    return file_path

def get_subtitle_content(subtitle_url, include_time = False):
    """Get the subtitles contents from url"""
    subtitles = []
    subtitle_text = ""

    response = requests.get(subtitle_url)
    data = response.json()

    for event in data.get("events", []):
        if "segs" in event:
            start = event.get("tStartMs", 0) / 1000.0
            duration = event.get("dDurationMs", 0) / 1000.0
            text = "".join(seg.get("utf8", "") for seg in event["segs"])
            subtitles.append({
                "start": start,
                "duration": duration,
                "text": text.strip()
            })

    for sub in subtitles:
        if include_time:
            subtitle_text += f"[{sub['start']:.1f}-{sub['start'] + sub['duration']:.1f}]"
        subtitle_text += sub['text']
        subtitle_text += "\n"

    return subtitle_text

def process_video_metadata(video_metadata):
    """Process the video metadata and return a readable format of fields and their values"""
    metadata_description = ""
    fields_of_interest = ["title", "description","categories","tags"]
    for field in fields_of_interest:
        if video_metadata.get(field):
            metadata_description +=f"**{field.upper()}**: {str(video_metadata.get(field))} \n\n"

    if video_metadata.get('subtitles'):
        subtitles = video_metadata.get('subtitles')
        if subtitles.get('en'):
            english_subtitles = subtitles.get('en')
            formatted_version = english_subtitles[0]
            if formatted_version.get("ext") == "json3":
                subtitle_text = get_subtitle_content(formatted_version.get("url"))
                metadata_description +=f"**SUBTITLES**: {subtitle_text} \n\n"
            else:
                print("Unable to find json3 version for subtitles.")
        else:
            print("Subtitles not found for english language.")
    else:
        metadata_description +="**SUBTITLES**: N/A"

    return metadata_description

def construct_contents(video_metadata, media_path):
    """Construct contents based on media received"""
    if isinstance(media_path, str):
        print("Processing video file")
        contents = [
            f"Video Metadata: {process_video_metadata(video_metadata)}",
            "Video file:",
            types.Part(
                inline_data=types.Blob(data=get_file_data(media_path), mime_type='video/mp4')
            ),
            "Description:"
        ]
    elif isinstance(media_path, list):
        print("Processing snapshots")
        contents = [
            f"Video Metadata: {process_video_metadata(video_metadata)}",
            "Snapshots of video:"
        ]
        for snapshot_image in media_path:
            contents.append(
                types.Part.from_bytes(
                    data=get_file_data(snapshot_image),
                    mime_type=f'image/{snapshot_image.split(".")[-1]}',
                ),
            )
            contents.append("Description:")
    print("Contents length",len(contents))
    return contents

def deserialize_parts(content_data):
    """Converts content stored in db/session_state to parts"""
    parts = []
    if "text" in content_data:
        parts.append(
            types.Part.from_text(text=content_data["text"])
        )
    if "media" in content_data:
        parts.append(types.Part.from_bytes(
            mime_type="image/"+content_data["media"].split(".")[-1],
            data=get_file_data(content_data["media"])
        ))
    
    return parts

def history_to_contents(message, history: list=""):
    """Converts list of messages to llm consumable format"""
    contents = []
    
    for chat_message in history:
        role = chat_message["role"]
        content_data = chat_message["content"]
        parts = deserialize_parts(content_data)
        contents.append(types.Content(role=role, parts=parts))
    
    if isinstance(message, list) and len(message[0]["content"].keys()) > 1:
        message_parts = deserialize_parts(message[0]["content"])
    else:
        message_parts = [types.Part.from_text(text=message)]
    
    contents.append(types.Content(
        role="user",
        parts=message_parts
    ))
    
    return contents

