import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from remote_agent.task_manager import BasicSearchAgentExecutor

agent_url = "http://localhost:8090/"

def start_remote_agent():
  
   agent_skill = AgentSkill(
       id="search_agent",
       name="Search Agent",
       description="Agent that can get the latest search results from internet using google search",
       input_modes=["text"],
       output_modes=["text"],
       tags=["search agent", "browser", "multi query"],
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
   print("Uvicorn server starting...")
   uvicorn.run(app, host="127.0.0.1", port=8090)

if __name__ == "__main__":
   start_remote_agent()
