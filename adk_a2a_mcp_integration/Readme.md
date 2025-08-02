# Boilerplate for Agent interaction with ADK, A2A and MCP.

[To UPDATE]
A simple implementation of agent which has access to some custom tools and an MCP server for exploring Arxiv research papers. It also has the ability to interact with remote agents using A2A Protocol. The agents are built using ADK and can be run using `adk web` or custom streamlit UI.

```bash
# To start remote agent
python -m remote_agent
```

```bash
# To start MCP server
python mcp_server/server.py
```

```bash
# To interact with root agent in UI
streamlit run app.py
```