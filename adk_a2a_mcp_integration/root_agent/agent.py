from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams

from root_agent.tools import get_current_time, calculate_expression

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
   name="orchestrator_agent",
   model="gemini-2.0-flash",
   description=(
       "Agent to answer questions using tools provided."
   ),
   instruction=(
       "You are a helpful agent who can answer user questions about current time and can do calculations and explore arxiv collection."
   ),
   tools=[get_current_time, calculate_expression, simple_mcp_tool],
)
