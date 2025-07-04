"""Gemini live client handler"""
import base64
from google import genai
from google.genai import types as genai_types

# TODO: Add more specific prompt + tool declarations
from prompt import SYSTEM_PROMPT
from tools import schedule_meet_tool

schedule_meet_tool_declaration = schedule_meet_tool.tool_metadata()

class GeminiClient:
    """Gemini client class"""
    def __init__(self,
                 api_key: str,
                 model_key: str="gemini-2.0-flash-exp"):
        # Initialize gemini client
        self.client = genai.Client(
            api_key=api_key
        )
        self.model_id = model_key
        self._setup_config()

    def _setup_config(self):
        """Setup Gemini configuration"""
        self.speech_config = genai_types.SpeechConfig(
            language_code="hi-IN",
            voice_config=genai_types.VoiceConfig(
                prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(voice_name="Aoede")
            ),
        )

        self.tool_defs = []

        self.system_instruction_content = genai_types.Content(
            parts=[genai_types.Part(text=SYSTEM_PROMPT)],
            role="system"
        )
        # FIXME: Generation config seems deprecated
        self.generation_config = genai_types.GenerationConfig(
            temperature=0.7
        )
        self.config = genai_types.LiveConnectConfig(
            response_modalities=[genai_types.Modality.AUDIO],
            speech_config=self.speech_config,
            generation_config=self.generation_config,
            tools=[genai_types.Tool(function_declarations=[schedule_meet_tool_declaration])],
            system_instruction=self.system_instruction_content,
            input_audio_transcription=genai_types.AudioTranscriptionConfig(),
            output_audio_transcription=genai_types.AudioTranscriptionConfig(),
        )

    def convert_audio_for_client(self, audio_data: bytes) -> str:
        """Converts audio data to base64 for client"""
        return base64.b64encode(audio_data).decode("utf-8")

    def get_initial_greeter(self):
        """Initiates conversation on behalf of user"""
        user_greeting = "Hello."

        initial_user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=user_greeting)]
        )
        return initial_user_message
