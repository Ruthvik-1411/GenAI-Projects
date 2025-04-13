import json
from typing import List, Annotated, Sequence
from typing_extensions import TypedDict, Annotated

from backend.config import GEMINI_API_KEY

from backend.core.prompts import router_prompt,rag_prompt, query_rewrite_prompt, chitchat_prompt
from backend.core.tools import get_relevant_docs_tool
from backend.ml_config import LLM_CONFIGS

from backend.utils.utility import format_sources, format_citations, format_chat_messages

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

chat_model = ChatGoogleGenerativeAI(**LLM_CONFIGS["gemini-2.0-flash"],google_api_key=GEMINI_API_KEY)

tools = [get_relevant_docs_tool]

rag_chain = rag_prompt | chat_model | StrOutputParser()
rewrite_chain = query_rewrite_prompt | chat_model | StrOutputParser()
chitchat_chain = chitchat_prompt | chat_model | StrOutputParser()

class AgentState(TypedDict):

  messages: Annotated[Sequence[BaseMessage], add_messages]
  chat_messages: Annotated[Sequence[BaseMessage], add_messages]
  chat_history: Sequence[BaseMessage]
  relevant_docs: List
  tool_call: dict
  bot_response: str
  rewritten_query: str

def router(state):
  """Call router to decide which tool to user"""

  print("---CALL ROUTER---")

  messages = state["messages"]
  chat_history = state["chat_history"]
  user_query = messages[0].content

  model_with_tools = chat_model.bind_tools(tools)

  router_chain = router_prompt | model_with_tools

  response = router_chain.invoke({
      "chat_history": chat_history,
      "user_query": user_query
  })

  return {
      "messages": [response],
      "chat_messages": messages,
      "tool_call": response.tool_calls,
      "rewritten_query": state["rewritten_query"]
  }

def tool_check_condition(state):
  print("---CHECK TOOL CALL---")
  print(state["tool_call"])

  if state.get("tool_call"):
    for tool_call in state.get("tool_call"):
      if tool_call.get("name") == "get_relevant_docs_tool":
        return "retrieve_tool"
      elif tool_call.get("name") == "other_tool":
        #should modify graph accordingly
        return "other_tool"
  else:
    return "chit_chat"

def rewrite(state):
  """Rewrite query based on chat history"""

  print("---CALL REWRITE---")

  messages = state["messages"]
  user_query = messages[0].content
  rewritten_query = ""
  chat_history = state["chat_history"]

  if chat_history:
    print("---REWRITING USING HISTORY---")
    rewritten_query = rewrite_chain.invoke({
        "chat_history": chat_history,
        "question": user_query
    })
    print("---REWRITTEN QUERY---")
    print(rewritten_query)

    return {
        "rewritten_query": rewritten_query
    }
  else:
    print("-HISTORY NOT FOUND-")
    return {
        "rewritten_query": ""
    }

def chit_chat(state):
  """Handle chit chat"""

  print("---CALL CHITCHAT---")
  messages = state["messages"]
  chat_history = state.get("chat_history")

  user_query = messages[0].content
  print("---QUERY---", user_query)
  rewritten_query = state.get("rewritten_query")
  if rewritten_query:
    print("---USING REWRITTEN QUERY---", rewritten_query)
    user_query = rewritten_query

  response = chitchat_chain.invoke({
      "chat_history": chat_history,
      "user_query": user_query
  })

  print(response)

  return {
      "messages": [AIMessage(content=response)],
      "chat_messages": [AIMessage(content=response)],
      "bot_response": response,
      "rewritten_query": rewritten_query
  }

def generate(state):
  """Generate response to user query based on retrieved sources"""

  print("---CALL GENERATE---")
  messages = state["messages"]
  chat_history = state.get("chat_history")
  tool_response = json.loads(messages[-1].content)

  user_query = messages[0].content
  print("---QUERY---", user_query)
  rewritten_query = state.get("rewritten_query")
  if rewritten_query:
    print("---USING REWRITTEN QUERY---", rewritten_query)
    user_query = rewritten_query

  sources = format_sources(tool_response)

  response = rag_chain.invoke({
      "sources": sources,
      "user_query": user_query,
      "chat_history": chat_history
  })

  print(response)

  return {
      "messages": [AIMessage(content=response)],
      "chat_messages": [AIMessage(content=response)],
      "relevant_docs": format_citations(tool_response),
      "bot_response": response,
      "rewritten_query": rewritten_query
  }

workflow = StateGraph(AgentState)

workflow.add_node("router", router)
retriever = ToolNode([get_relevant_docs_tool])
workflow.add_node("retriever", retriever)
workflow.add_node("rewrite",rewrite)
workflow.add_node("generate", generate)
workflow.add_node("chit_chat",chit_chat)

workflow.add_edge(START, "rewrite")
workflow.add_edge("rewrite", "router")
workflow.add_conditional_edges(
    "router",
    tool_check_condition,
    {
        "retrieve_tool": "retriever",
        "chit_chat": "chit_chat"
    }

)
workflow.add_edge("retriever", "generate")
workflow.add_edge("generate", END)
workflow.add_edge("chit_chat", END)

graph = workflow.compile()

def chat_session(query, chat_history):
  user_input = {
      "messages": [
          ("user", query)
      ],
      "chat_history": chat_history
  }

  graph_response = graph.invoke(user_input)

  return graph_response.get("bot_response"), graph_response.get("relevant_docs")

def generate_rag_response(input: str, history: list=[]):

    # print(f"Messages {type(history)}: {history}")
    formatted_messages = format_chat_messages(history)
    # print(f"Formatted {type(formatted_messages)}: {formatted_messages}")

    bot_response, citations = chat_session(input, formatted_messages)

    if citations:
        response = {
            "message": bot_response,
            "rich_content": {
                "type": "citations",
                "citations": citations
            }
        }
    else:
        response = {
            "message": bot_response
        }
    return response
def generate_response(input: str, history: list=[]):
    print(input, history)
    if "citations" in input:
        response = {
            "message": f"Echo: {input}",
            "rich_content": {
            "type": "citations",
            "citations": [
                {
                    "title": "Citation 1",
                    "url": "https://mesop-dev.github.io/mesop/"
                },
                {
                    "title": "Citation 2",
                    "url": "https://mesop-dev.github.io/mesop/"
                }
            ]
            }
        }
    elif "chip" in input:
        response = {
            "message": f"Echo: {input}",
            "rich_content": {
            "type": "chips",
            "chips": [
                {
                    "text": "First message"
                },
                {
                    "text": "Second message"
                }
            ]
            }
        }
    else:
        response = {
            "message": f"Echo: {input}"
        }
    
    return response
