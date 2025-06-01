"""Video description generator module"""
from google.genai import types
from google.genai.client import Client as geminiClient

class VideoAnalyzer():
    """Video Analyzer class"""
    def __init__(self,
                client: geminiClient,
                system_instructions: str,
                model: str ="gemini-2.0-flash-001"):
        self.client = client
        self.system_instructions = system_instructions
        self.model = model
        print("Initialized video analyzer")

    def get_gemini_response(self, contents):
        """Generates video description based on input contents"""
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instructions,
                temperature=0.1,
                max_output_tokens=512
            ),
            contents=contents,
        )

        return response.text
