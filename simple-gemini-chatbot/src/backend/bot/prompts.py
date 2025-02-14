"""Prompts and prompts for later use"""
from langchain_core.prompts.prompt import PromptTemplate

# Since we are using multimodal, this might not be that helpful
CHAT_PROMPT = """You are a helpful assistant whose job is to help users with their queries.
Following is the conversation with the user. Make use of the history if required, while answering the questions.
Answer the user's question to the best of your knowledge.

<conversation_history>
{chat_history}
</conversation_history>

<user_question>
{user_input}
</user_question>

Response:"""

chat_prompt_template = PromptTemplate(
    template=CHAT_PROMPT,
    input_variables=["chat_history", "user_input"]
)
