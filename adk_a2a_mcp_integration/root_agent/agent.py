"""Core module for agent orchestration"""
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams

from root_agent.tools import get_current_time, calculate_expression
from root_agent.remote_agent_helpers import list_remote_agents, call_remote_agent

from dotenv import load_dotenv
# To load the google api keys
load_dotenv()

simple_mcp_tool = MCPToolset(
   connection_params=StreamableHTTPConnectionParams(
       url="http://localhost:8000/mcp",
       timeout=10,
       sse_read_timeout=60 * 5,
       terminate_on_close=True,
   ),
   tool_filter=["search_arxiv","get_paper_md"]
)

root_agent = Agent(
   name="root_agent",
   model="gemini-2.0-flash",
   description="Agent to answer questions using tools provided.",
   instruction="""You are a helpful agent who can answer user questions about current time and can do calculations.
   For any queries that require latest/external information, identify if any remote agents can help with that.
   Once you found the relevant agents, use the appropriate tools to get the answer the user query.""",
   tools=[get_current_time,
          calculate_expression,
          simple_mcp_tool,
          list_remote_agents,
          call_remote_agent],
)
