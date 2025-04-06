from utils.utility import get_files_in_dir, save_embeddings, load_embeddings
from core.chunking import PDFTextSplitter
from core.embedding import EmbeddingClient
from core.retriever import CustomMilvusClient
from config import GEMINI_API_KEY

# chat_model = ChatGoogleGenerativeAI(**LLM_CONFIGS["gemini-2.0-flash"],google_api_key=GEMINI_API_KEY)

from core.chat import chat_session, generate_rag_response

print(generate_rag_response(input="How to make chilli con carne?", history=[]))