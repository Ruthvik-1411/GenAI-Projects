"""Module to orchestrate the complete workflow"""
# pylint: disable=invalid-name

from video_processor.processor import get_video_data
from utils.utility import construct_contents
from core.video_analyzer import VideoAnalyzer
from core.prompt_generator import PromptGenerator
from core.image_generator import ImageGenerator

from core.prompts import video_analyzer_prompt, imagen_prompt_generator

from google import genai
client = genai.Client(api_key="GEMINI_API_KEY")

video_analyzer = VideoAnalyzer(
    client=client,
    system_instructions=video_analyzer_prompt
)

imagen_prompter = PromptGenerator(
    client=client,
    system_instructions=imagen_prompt_generator
)

image_generator = ImageGenerator(
    client=client
)


# --- Actual Workflow ---

# video_url = "https://youtu.be/2lAe1cqCOXo?si=lQlS9vEbDOYkGbpW" # Youtube rewind
video_url = "https://youtu.be/u_Gm_Hi7gV4" # my channel videos
# video_url = "https://youtu.be/HnFqBWPk73Q?si=7liv6K5W-tC5PeO4" # my channel videos

video_metadata, media_path = get_video_data(video_url)

video_title = video_metadata.get("title")

message_content = construct_contents(video_metadata, media_path)

video_description = video_analyzer.get_gemini_response(message_content)

print(f"Video Description: {video_description}")

imagen_prompt = imagen_prompter.get_imagen_prompt(video_description)

print(f"Imagen Prompt: {imagen_prompt}")

image_result = image_generator.generate_image(imagen_prompt, video_title)

print(f"Result: {image_result}")
