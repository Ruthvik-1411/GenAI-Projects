"""Utils file for commonly used functions"""
# pylint: disable=W0102
import base64

def get_file_data(file):
    """Convert file data to base64"""
    try:
        file.seek(0)
        file_content = file.read()
        file_data = base64.b64encode(file_content).decode("utf-8")
        return file_data
    except Exception as e: # pylint: disable=W0718
        print(f"Error processing image: {e}")
        return None

def process_chat_history(messages: list):
    """Process chat history for llm consumption"""
    chat_history = []
    for message in messages:
        chat_history.append({
            "role": message["role"],
            "content": message["content"]
        })

    return chat_history

def convert_to_message(role: str, content: str, attachments: list=[]):
    """Convert message to usable format"""
    message = {
        "role": role,
        "display_content": content,
        "content": content,
        "attachments": attachments
    }

    return message

def convert_to_multimodal_message(role: str,
                                  contents: list,
                                  attachments: list=[],
                                  for_llm: bool=False):
    """Convert message to usable multimodal format"""
    message_content = []
    message = {}
    for content in contents:
        if isinstance(content, str):
            message_content.append({
                "type": "text",
                "text": content
            })
            message["display_content"] = content
        else:
            # Either of the below approaches can be used
            # Send as media or send as image_url for images, both of them work the same
            for uploaded_file in content:
                if uploaded_file.type in ["application/pdf", "video/mp4"]:
                    file_data = get_file_data(uploaded_file)
                    message_content.append({
                        "type": "media",
                        "data": file_data,
                        "mime_type": uploaded_file.type,
                    })
                else:
                    image_data = get_file_data(uploaded_file)
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{uploaded_file.type};base64,{image_data}"
                        }
                    })

    if for_llm:
        message = {
            "role": role,
            "content": message_content
        }
    else:
        message.update({
            "role": role,
            "content": message_content,
            "attachments": attachments
        })
    return message
