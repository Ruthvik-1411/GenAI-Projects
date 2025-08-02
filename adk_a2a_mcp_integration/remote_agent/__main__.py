"""Module that exposes the remote agent as a server, sharing it's capabilities
and methods to invoke it"""
import uvicorn
import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from remote_agent.task_manager import BasicSearchAgentExecutor

logger = logging.getLogger(__name__)

agent_url = "http://localhost:8090/"

def start_remote_agent():
    """Start the remote agent and expose it's capabilities"""
    agent_skill = AgentSkill(
        id="search_agent",
        name="Search Agent",
        description="""Agent that can get the latest search results from the
        internet using google search and gives accurate results""",
        input_modes=["text"],
        output_modes=["text"],
        tags=["search agent", "google search tool", "web search"],
        examples=[
            "What are the latest news in AI?",
            "Explain the key difference between Langchain and Langgraph.",
            "Who won the last IPL match?"]
    )

    public_agent_card = AgentCard(
        name="Search agent",
        description="Agent that can search the internet to answer queries.",
        url=agent_url,
        version="0.0.1",
        skills=[agent_skill],
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supportsAuthenticatedExtendedCard=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=BasicSearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler
    )
    app = server.build()
    logger.info("Uvicorn server starting...")
    uvicorn.run(app, host="127.0.0.1", port=8090)

if __name__ == "__main__":
    start_remote_agent()
