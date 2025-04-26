"""Main logic for chat with rag bot"""
import json
import logging
from typing import List, Annotated, Sequence
from typing_extensions import TypedDict
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

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def add_step(current_steps, new_steps):
    """Appends 'step' key with previous steps to the state"""
    if not isinstance(new_steps, list):
        new_steps = [new_steps]
    return current_steps + new_steps

tools = [get_relevant_docs_tool]
class AgentState(TypedDict):
    """Class for maintaining graph state"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: Sequence[BaseMessage]
    relevant_docs: List
    tool_call: dict
    bot_response: str
    rewritten_query: str
    steps: Annotated[List[dict], add_step] #should stick to normalized format instead of dict

class RAGApp():
    """Class for rag application"""
    def __init__(self, params) -> None:
        logger.info("Initializing rag app...")
        self.gemini_api_key = params.get("gemini_api_key")
        self.model_key = params.get("model")
        self.chat_model = ChatGoogleGenerativeAI(**LLM_CONFIGS[self.model_key],
                                                 google_api_key=self.gemini_api_key)

        self.rag_chain = rag_prompt | self.chat_model | StrOutputParser()
        self.rewrite_chain = query_rewrite_prompt | self.chat_model | StrOutputParser()
        self.chitchat_chain = chitchat_prompt | self.chat_model | StrOutputParser()
        self.router_chain = router_prompt | self.chat_model.bind_tools(tools)

        self.graph = self._build_workflow_graph()

    def rewrite(self, state):
        """Rewrite query based on chat history"""

        logger.info("---CALL REWRITE---")

        messages = state["messages"]
        user_query = messages[0].content
        rewritten_query = ""
        chat_history = state["chat_history"]

        step_trace = {
            "NODE": "REWRITE"
        }

        if chat_history:
            step_trace.update({
                "history_present": True,
                "STEP 1": "REWRITING QUERY USING HISTORY"
            })
            logger.info("---REWRITING USING HISTORY---")
            rewritten_query = self.rewrite_chain.invoke({
                "chat_history": chat_history,
                "question": user_query
            })
            logger.info("---REWRITTEN QUERY---")
            step_trace.update({
                "STEP 2": {
                    "input": query_rewrite_prompt.format(chat_history=chat_history,
                                                         question=user_query),
                    "output": rewritten_query
                },
                "rewritten_query": rewritten_query
            })
            logger.info(rewritten_query)

            return {
                "rewritten_query": rewritten_query,
                "steps": step_trace
            }

        step_trace.update({
            "history_present": False,
            "STEP 1": "NO QUERY REWRITE",
            "rewritten_query": None
        })
        logger.info("-HISTORY NOT FOUND-")
        return {
            "rewritten_query": None,
            "steps": step_trace
        }

    def router(self, state):
        """Call router to decide which tool to user"""

        logger.info("---CALL ROUTER---")

        messages = state["messages"]
        chat_history = state["chat_history"]
        user_query = messages[0].content

        rewritten_query = state.get("rewritten_query")

        step_trace = {
            "NODE": "ROUTER",
            "STEP 1": "USING USER QUERY",
            "user_query": user_query
        }
        if rewritten_query:
            step_trace.update({
                "STEP 1": "USING REWRITTEN QUERY",
                "user_query": rewritten_query
            })
            logger.info(f"---USING REWRITTEN QUERY---\n{rewritten_query}")
            user_query = rewritten_query

        response = self.router_chain.invoke({
            "chat_history": chat_history,
            "user_query": user_query
        })

        step_trace.update({
            "STEP 2": {
                "input": router_prompt.format(chat_history=chat_history,
                                              user_query=user_query),
                "output": response.content if response.content else "TOOL CALL",
                "tool_call": response.tool_calls
            }
        })

        return {
            "messages": [response],
            "chat_messages": messages,
            "tool_call": response.tool_calls,
            "rewritten_query": state["rewritten_query"],
            "steps": step_trace
        }

    def tool_check_condition(self, state):
        """Checks tool call and routes to next layer"""

        logger.info("---CHECK TOOL CALL---")
        logger.info(state["tool_call"])

        if state.get("tool_call"):
            for tool_call in state.get("tool_call"):
                if tool_call.get("name") == "get_relevant_docs_tool":
                    return "retrieve_tool"
                if tool_call.get("name") == "other_tool":
                    #should modify graph accordingly
                    return "other_tool"
        return "chit_chat"

    def chit_chat(self, state):
        """Handle chit chat"""

        logger.info("---CALL CHITCHAT---")
        messages = state["messages"]
        chat_history = state.get("chat_history")

        user_query = messages[0].content
        logger.info(f"---QUERY---\n{user_query}")
        rewritten_query = state.get("rewritten_query")

        step_trace = {
            "NODE": "CHIT-CHAT",
            "STEP 1": "USING ORIGINAL QUERY"
        }
        if rewritten_query:
            step_trace.update({
                "STEP 1": "USING REWRITTEN QUERY"
            })
            logger.info(f"---USING REWRITTEN QUERY---\n{rewritten_query}")
            user_query = rewritten_query

        response = self.chitchat_chain.invoke({
            "chat_history": chat_history,
            "user_query": user_query
        })

        step_trace.update({
            "STEP 2": {
                "input": chitchat_prompt.format(chat_history=chat_history,
                                                user_query=user_query),
                "output": response
            },
            "FINAL RESPONSE": response
        })

        logger.info(response)

        return {
            "messages": [AIMessage(content=response)],
            "chat_messages": [AIMessage(content=response)],
            "bot_response": response,
            "rewritten_query": rewritten_query,
            "steps": step_trace
        }

    def generate(self, state):
        """Generate response to user query based on retrieved sources"""

        logger.info("---CALL GENERATE---")
        messages = state["messages"]
        chat_history = state.get("chat_history")
        tool_response = json.loads(messages[-1].content)

        user_query = messages[0].content
        logger.info(f"---QUERY--- \n {user_query}")
        rewritten_query = state.get("rewritten_query")
        step_trace = {
            "NODE": "GENERATE",
            "STEP 1": "USING ORIGINAL QUERY"
        }
        if rewritten_query:
            step_trace.update({
                "STEP 1": "USING REWRITTEN QUERY"
            })
            logger.info(f"---USING REWRITTEN QUERY---\n{rewritten_query}")
            user_query = rewritten_query

        sources = format_sources(tool_response)
        step_trace.update({
            "Retriever Results": tool_response
        })

        response = self.rag_chain.invoke({
            "sources": sources,
            "user_query": user_query,
            "chat_history": chat_history
        })
        step_trace.update({
            "STEP 2": {
                "input": rag_prompt.format(sources=sources,
                                           user_query=user_query,
                                           chat_history=chat_history),
                "output": response
            },
            "FINAL RESPONSE": response
        })

        logger.info(response)

        return {
            "messages": [AIMessage(content=response)],
            "chat_messages": [AIMessage(content=response)],
            "relevant_docs": format_citations(tool_response),
            "bot_response": response,
            "rewritten_query": rewritten_query,
            "steps": step_trace
        }

    def _build_workflow_graph(self):
        """Build graph"""
        workflow = StateGraph(AgentState)

        workflow.add_node("router", self.router)
        retriever = ToolNode([get_relevant_docs_tool])
        workflow.add_node("retriever", retriever)
        workflow.add_node("rewrite", self.rewrite)
        workflow.add_node("generate", self.generate)
        workflow.add_node("chit_chat", self.chit_chat)

        workflow.add_edge(START, "rewrite")
        workflow.add_edge("rewrite", "router")
        workflow.add_conditional_edges(
            "router",
            self.tool_check_condition,
            {
                "retrieve_tool": "retriever",
                "chit_chat": "chit_chat"
            }

        )
        workflow.add_edge("retriever", "generate")
        workflow.add_edge("generate", END)
        workflow.add_edge("chit_chat", END)

        graph = workflow.compile()

        return graph

    def chat_session(self, query, chat_history):
        """Create session to chat with the graph"""
        user_input = {
            "messages": [HumanMessage(content=query)],
            "chat_history": chat_history,
            "steps": []
        }

        graph_response = self.graph.invoke(user_input)

        return graph_response.get("bot_response"), graph_response.get("relevant_docs"), graph_response.get("steps") # pylint: disable=line-too-long

    def generate_rag_response(self, user_input: str, history: list):
        """Generates responses using input and history"""

        # mesop_chat adds user message to the history for 1st message.
        # Chat history should be added after completion of turn, so ignoring first addition.
        if len(history) == 1:
            history = []
        formatted_messages = format_chat_messages(history)
        bot_response, citations, diagnostic_info = self.chat_session(user_input, formatted_messages)

        if citations:
            response = {
                "message": bot_response,
                "rich_content": {
                    "type": "citations",
                    "citations": citations
                },
                "diagnostic_info": json.dumps(diagnostic_info, indent=4)
            }
        else:
            response = {
                "message": bot_response,
                "diagnostic_info": json.dumps(diagnostic_info, indent=4)
            }
        return response

def generate_response(user_input: str, history: list):
    """Testing function"""
    if "citations" in user_input:
        response = {
            "message": f"Echo: {user_input}",
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
    elif "chip" in user_input:
        response = {
            "message": f"Echo: {user_input}",
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
            "message": f"Echo: {user_input}"
        }

    return response
