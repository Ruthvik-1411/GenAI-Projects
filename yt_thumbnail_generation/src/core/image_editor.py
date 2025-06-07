"""Image Editing Module"""

import mimetypes
from utils.utility import history_to_contents, save_binary_file
from google.genai import types
from google.genai.client import Client as geminiClient

class ImageEditor():
    """Image editor class"""
    def __init__(self,
                client: geminiClient,
                system_instructions: str = "",
                image_model: str = "gemini-2.0-flash-preview-image-generation"):
        self.client = client
        self.model = image_model
        self.system_instructions = system_instructions #To be used

    def chat_session(self, message, history: list):
        """Chat session to edit messages"""
        response = self.client.models.generate_content(
            model=self.model,
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE","TEXT"],
                response_mime_type="text/plain",
            ),
            contents=history_to_contents(message, history)
        )
        return response

    def serialize_response(self, response, version):
        """Converts llm response to savable format"""
        response_text = ""
        response_media = ""
        if (response.candidates is None
            or response.candidates[0].content is None
            or response.candidates[0].content.parts is None):
            print("Empty response")

        response_parts = response.candidates[0].content.parts

        for part in response_parts:
            if part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                file_extension = mimetypes.guess_extension(part.inline_data.mime_type)
                saved_media_path = save_binary_file(f"image_edit{version}{file_extension}",
                                                    image_data)
                response_media = saved_media_path
            else:
                print(f"TEXT: {part.text}")
                response_text = part.text

        return response_text, response_media
