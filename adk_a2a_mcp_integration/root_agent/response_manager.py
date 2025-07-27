import asyncio
import uuid
import logging

from google.genai import types
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService

from root_agent.agent import root_agent

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class ResponseManager:

    def __init__(self):
        self.agent = root_agent
        self.user_id = "u_123"
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    async def invoke_agent(self, session_id: str, query: str) -> str:

        try:
            logger.info(f"Fetching session data with id: {session_id}")
            session = await self.runner.session_service.get_session(
                app_name=self.agent.name,
                user_id=self.user_id,
                session_id=session_id
            )

            if session is None:
                logger.info(f"Session doesn't exist, creating new session with id: {session_id}")
                session = await self.runner.session_service.create_session(
                    app_name=self.agent.name,
                    user_id=self.user_id,
                    session_id=session_id,
                    state={}
                )

            logger.info(f"{session.id} Running query: {query}")

            content = types.Content(role="user",parts=[types.Part.from_text(text=query)])

            final_response_text = ""
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=session.id,
                new_message=content
            ):
                if event.get_function_calls():
                    yield {
                        "is_final_response": False,
                        "status": "tool_call",
                        "event": event.model_dump(mode='json', exclude_none=True)
                    }
                if event.get_function_responses():
                    yield {
                        "is_final_response": False,
                        "status": "tool_response",
                        "event": event.model_dump(mode='json', exclude_none=True)
                    }
                if event.is_final_response():
                    if event.content and event.content.parts and event.content.parts[-1].text:
                        final_response_text = event.content.parts[-1].text

                    logger.info(f"[{session_id}] Final text: {final_response_text}]")
                    yield {
                        "is_final_response": True,
                        "status": "finished",
                        "result": final_response_text,
                        "event": event.model_dump(mode='json', exclude_none=True)
                    }
        except Exception as e:
            logger.info(f"Error generating response.")
            yield {
                "is_final_response": True,
                "status": "fail",
                "result": "No final response received",
                "error_message": str(e)
            }

async def test_agent(): 

    response_manager = ResponseManager()

    session_id = str(uuid.uuid4())

    first_query = "What are some trending topics in AI?"
    # first_response = await response_manager.invoke_agent(session_id=session_id, query=first_query)
    first_response = response_manager.invoke_agent(session_id=session_id, query=first_query)
    async for response in first_response:
        logger.info(f"Events: {response}")
    # logger.info(f"First response: {first_response}")

    # second_query = "What question did I ask you?"
    # second_response = await response_manager.invoke_agent(session_id=session_id, query=second_query)
    # logger.info(f"Second response: {second_response}")

# asyncio.run(test_agent())