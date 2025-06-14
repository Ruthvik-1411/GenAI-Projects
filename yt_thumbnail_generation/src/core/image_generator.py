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

    def generate_image(self, prompt: str, image_name: str, model_key: str=""):
        """Generates image using given prompt and save as image_name"""
        model_code = self.model
        if model_key:
            model_code = model_key
        if "gemini" in model_code:
            response = self.client.models.generate_content(
                model=model_code,
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
        if "imagen" in model_code:
            response = self.client.models.generate_images(
                model=model_code,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images= 1, # Let's keep only one for now, works with current UI
                    aspect_ratio="16:9", # youtube thumbnail usually landscape
                    output_mime_type="image/png" # should be configurable from UI
                )
            )

            for generated_image in response.generated_images:
                image_data = generated_image.image.image_bytes
                file_extension = generated_image.image.mime_type.split("/")[-1]
                file_name = f"{clean_title(image_name.lower())}.png"
                saved_path = save_binary_file(file_name, image_data)

                return saved_path
        print("Support to be added for other models")
        return None
