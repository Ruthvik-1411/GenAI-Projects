from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder

router_template = """You are a helpful assitant whose purpose is to help users with their queries.
Given user question and previous conversation history, utlize the appropriate tools where required to help them.
Understand the user question and identify which tools are more suitable to help them and use it accordingly.

User Question: {user_query}
"""
router_prompt = ChatPromptTemplate.from_messages([
    ("system", router_template),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{user_query}"),
])

rag_template = """You are a friendly and helpful chat bot. Your role is to help users by answering questions based on the sources provided.
Maintain a friendly and supportive tone while providing accurate and helpful responses. Utilize the provided conversation history to understand previous interactions.
Avoid adding any other explanation.
Sources: {sources}

Conversation History: {chat_history}

User Query: {user_query}
Response:
"""
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", rag_template),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{user_query}"),
])

query_rewrite_template = """Given the following conversation history and user followup question, rephrase the user query to be a standalone question.
The rephrased question should be understood without the chat history and should be meaningful and complete on its own.
If the query is independent and is not related to the chat history, then return it as is. In any other case, rewrite the query.

Conversation History: {chat_history}
User Query: {question}

Standalone Question:
"""
query_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", query_rewrite_template),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{question}"),
])
