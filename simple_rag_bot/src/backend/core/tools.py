from langchain_core.tools import tool

from backend.config import GEMINI_API_KEY
from backend.core.embedding import EmbeddingClient
from backend.core.retriever import CustomMilvusClient

embedding_instance = EmbeddingClient(embedding_api_key=GEMINI_API_KEY)
retriever_instance = CustomMilvusClient(uri="backend/local_db/local_milvus.db")

def get_relevant_docs(collection_name: str, query: str, top_n: int=3):
  """Get relevant docs for a given query"""
  query_embedding = embedding_instance.get_query_embeddings(content=query)

  docs = retriever_instance.query_collection(collection_name=collection_name,
                                             query_embedding=query_embedding,
                                             limit=top_n,
                                             output_fields=["content", "page_span","document_metadata"])

  return docs

@tool
def get_relevant_docs_tool(query: str) -> list:
  """Utilize this function if user asks any questions related to climate change, recipes and LLMs terminology.
  This tool searches and return information about recipes, LLM terminology and climate change.
  For all user questions, utlize this tool to get relevant sources for answering user query.
  Args:
      query: The exact question asked by the user without any modifications
  """
  print("---CALL RETRIEVER--")
  collection_name = "local_pdf_rag"
  relevant_docs = get_relevant_docs(collection_name=collection_name,
                                    query=query)
  # reranking logic etc can be added

  return relevant_docs