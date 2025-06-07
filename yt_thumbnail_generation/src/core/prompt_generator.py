"""Prompt generator for image generation"""
from google.genai import types
from google.genai.client import Client as geminiClient

class PromptGenerator():
    """Prompt generator class"""
    def __init__(self,
                client: geminiClient,
                system_instructions: str,
                model: str = "gemini-2.0-flash-001"):
        self.client = client
        self.system_instructions = system_instructions
        self.model = model

    def get_imagen_prompt(self, video_description):
        """Generates prompt for image generation using video description"""
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instructions,
                temperature=0.1,
                max_output_tokens=512
            ),
            contents=["Video Description:",
                      video_description,
                      "\nVisual Design Brief:"],
        )

        return response.text
