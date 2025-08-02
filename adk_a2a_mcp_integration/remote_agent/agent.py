"""Module that implements the core logic for the search agent"""
import logging

from google.adk import Runner
from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

from dotenv import load_dotenv
# To load the google api keys
load_dotenv()

logger = logging.getLogger(__name__)

root_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    description="Agent capable of searching internet to find relevant answers to user questions.",
    instruction="""You are an friendly and supportive agent. Your job is to try to answer the user question using the search tool.
    Always provide accurate and relevant information.""",
    tools=[google_search],
)

class BasicSearchAgent:
    """Class that exposes the basic search agent"""
    def __init__(self):
        self.agent = root_agent
        self.runner =  Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
            session_service=InMemorySessionService(),
        )

    async def invoke(self, session_id: str, query: str, user_id: str = None):
        """Invoke the agent"""
        try:
            if not user_id:
               user_id = "Default User"
               session_instance = await self.runner.session_service.get_session(
                   session_id=session_id,
                   user_id=user_id,
                   app_name=self.agent.name
                )

            if not session_instance:
                logger.info(f"Creating new session with id: {session_id}")
                session_instance = await self.runner.session_service.create_session(
                    session_id=session_id,
                    user_id=user_id,
                    app_name=self.agent.name
                )
            
            user_content = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )

            final_response_text = ""
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_instance.id,
                new_message=user_content
            ):
                # We can break when there's final response,
                # but for telemetry usage, the loop must complete 
                # logger.debug(f"Event: {event}")
                if event.is_final_response():
                    if event.content and event.content.parts and event.content.parts[-1].text:
                        final_response_text = event.content.parts[-1].text
            logger.info("Loop finished, yielding final response.")
            yield {
                "status": "success",
                "result": final_response_text
            }
        except Exception as e:
            logger.info(f"Error: {e}")
            yield {
                "status": "error",
                "error_message": str(e)
            }
