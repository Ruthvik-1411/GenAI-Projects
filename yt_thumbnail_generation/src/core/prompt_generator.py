"""Prompt generator for image generation"""
from google.genai import types
from google.genai.client import Client as geminiClient
from google.genai.errors import ClientError, ServerError

class PromptGenerator():
    """Prompt generator class"""
    def __init__(self,
                client: geminiClient,
                system_instructions: str,
                model: str = "gemini-2.0-flash-001"):
        self.client = client
        self.system_instructions = system_instructions
        self.model = model

    def get_imagen_prompt(self, video_description: str, model_key: str = "gemini-2.0-flash-001"):
        """Generates prompt for image generation using video description"""
        try:
            model_code = self.model
            if model_key:
                model_code = model_key
            response = self.client.models.generate_content(
                model=model_code,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instructions,
                    temperature=0.1,
                    max_output_tokens=512
                ),
                contents=["Video Description:",
                        video_description,
                        "\nVisual Design Description:"],
            )

            return response.text, None
        except ClientError as e:
            # Invalid api key or client side error
            return None, str(e)
        except ServerError as e:
            # Server side error
            return None, str(e)
        except Exception as e:
            return None, str(e)
