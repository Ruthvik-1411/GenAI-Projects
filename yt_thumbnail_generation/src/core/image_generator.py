"""Image Generation Module"""

import mimetypes
from utils.utility import save_binary_file, clean_title
from google.genai import types
from google.genai.client import Client as geminiClient

class ImageGenerator():
    """Image generator class"""
    def __init__(self,
                client: geminiClient,
                image_model: str = "gemini-2.0-flash-preview-image-generation"):
        self.client = client
        self.model = image_model

    def generate_image(self, prompt: str, image_name: str):
        """Generates image using given prompt and save as image_name"""
        if "gemini" in self.model:
            response = self.client.models.generate_content(
                model=self.model,
                config = types.GenerateContentConfig(
                    response_modalities=["IMAGE","TEXT"],
                    response_mime_type="text/plain",
                ),
                contents=[prompt]
            )

            if (response.candidates is None
                or response.candidates[0].content is None
                or response.candidates[0].content.parts is None):
                return None

            response_parts = response.candidates[0].content.parts

            for part in response_parts:
                if part.inline_data and part.inline_data.data:
                    image_data = part.inline_data.data
                    file_extension = mimetypes.guess_extension(part.inline_data.mime_type)
                    file_name = f"{clean_title(image_name.lower())}{file_extension}"
                    saved_path = save_binary_file(file_name, image_data)

                    return saved_path

            return None
        else:
            print("Support to be added for imagen/other models")
            return None
