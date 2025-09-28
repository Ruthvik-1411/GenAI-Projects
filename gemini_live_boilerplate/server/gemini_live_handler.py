"""Gemini live client handler"""
import base64
import asyncio
import logging
from typing import Callable, List, Optional
from google import genai
from google.genai import types as genai_types

# TODO: Add more specific prompt
from prompt import SYSTEM_PROMPT
from tool_context import ToolContext # pylint: disable=no-name-in-module
from utils import accepts_tool_context

# TODO: Use same logger everywhere, don't import new one
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class GeminiClient:
    """Gemini client class"""
    def __init__(self,
                 api_key: str,
                 model_key: str="gemini-2.0-flash-exp",
                 tools: List[Callable[..., object]] = None):
        # Initialize gemini client
        # NOTE: Vertex AI project id can also be used here with minimal changes
        self.client = genai.Client(
            api_key=api_key
        )
        self.model_id = model_key
        self.tools = []
        self.tool_definitions = []
        if tools:
            self.tools = tools
            for tool in self.tools:
                self.tool_definitions.append(tool.tool_metadata())
            logger.info(f"Initializing gemini with tools: {self.tool_definitions}")
        self._setup_config()

    def _setup_config(self):
        """Setup Gemini configuration"""
        self.speech_config = genai_types.SpeechConfig(
            language_code="hi-IN",
            voice_config=genai_types.VoiceConfig(
                prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(voice_name="Aoede")
            ),
        )

        self.system_instruction_content = genai_types.Content(
            parts=[genai_types.Part(text=SYSTEM_PROMPT)],
            role="system"
        )

        self.config = genai_types.LiveConnectConfig(
            response_modalities=[genai_types.Modality.AUDIO],
            speech_config=self.speech_config,
            temperature=0.7,
            tools=[genai_types.Tool(function_declarations=self.tool_definitions)],
            system_instruction=self.system_instruction_content,
            input_audio_transcription=genai_types.AudioTranscriptionConfig(),
            output_audio_transcription=genai_types.AudioTranscriptionConfig(),
        )

    # NOTE: Can add support for injected tool arg like langchain, for later
    async def call_function(self,
                            fc_id: str,
                            fc_name: str,
                            fc_args=None,
                            tool_ctx: ToolContext = None):
        """Calls the functions that were defined and returns the function response"""
        func_args = fc_args.copy() if fc_args else {}

        try:
            for tool in self.tools:
                tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
                if tool_name == fc_name and callable(tool):
                    # Check if func accepts tool context
                    param, accepts = accepts_tool_context(tool)
                    if accepts and tool_ctx:
                        func_args[param] = tool_ctx

                    if asyncio.iscoroutinefunction(tool):
                        function_result = await tool(**func_args)
                    else:
                        function_result = tool(**func_args)

                    return genai_types.FunctionResponse(
                        id=fc_id,
                        name=fc_name,
                        response={"result": function_result}
                    )
            logger.error(f"Function with name '{fc_name}' is not defined.")
            return genai_types.FunctionResponse(
                id=fc_id,
                name=fc_name,
                response={
                    "result": f"Function with `{fc_name}` is not defined."
                }
            )
        except Exception as e:
            logger.error(f"Error occured invoking '{fc_name}' with {fc_args}. Error: {str(e)}.")
            return genai_types.FunctionResponse(
                id=fc_id,
                name=fc_name,
                response={
                    "result": "Error occured invoking function. Unable to execute the function"
                }
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
