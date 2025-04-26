"""Modules for generating embeddings"""
import copy
from tqdm import tqdm
from ratelimit import limits, sleep_and_retry
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class EmbeddingClient:
    """Custom class for embedding data with Gemini models"""
    def __init__(self, model_name: str="models/text-embedding-004", embedding_api_key: str=""):
      """Initialize embedding client with required params"""
      self.model_name = model_name
      self.embedding_api_key = embedding_api_key
      self.embedding_instance = GoogleGenerativeAIEmbeddings(model=self.model_name,
                                                             google_api_key=self.embedding_api_key)

    @sleep_and_retry
    @limits(calls=120, period=60)
    def _generate_embedding(self, chunk_content):
      """Helper function to generate embedding with rate limiting"""
      try:
        return self.embedding_instance.embed_query(chunk_content)
      except Exception as e:
        print(e)
        return None

    def generate_embeddings(self, chunks_data):
      """Generate embeddings for content"""
      # Batch embeddings can be made, but it takes time to setup
      embeddings_data = copy.deepcopy(chunks_data)

      for chunk in tqdm(embeddings_data):
        chunk_content = chunk["content"]
        chunk_embedding = chunk_embedding = self._generate_embedding(chunk_content)
        chunk["chunk_embedding"] = chunk_embedding

      return embeddings_data

    def get_query_embeddings(self, content: str):
      """Generate embeddings for query during runtime"""

      query_embedding = self.embedding_instance.embed_query(text=content)

      return query_embedding
