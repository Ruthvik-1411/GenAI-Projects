"""File to setup data and vector db initially"""

from backend.utils.utility import get_files_in_dir, save_embeddings, load_embeddings
from backend.core.chunking import PDFTextSplitter
from backend.core.embedding import EmbeddingClient
from backend.core.retriever import CustomMilvusClient
from backend.config import GEMINI_API_KEY

### --- SETUP ----
def initial_setup():
    """Initial setup of chunking and embedding of docs"""
    documents_list = get_files_in_dir("../../documents")

    def generate_chunks_and_embeddings(files_list, folder_name):

        document_splitter = PDFTextSplitter(files_list)

        chunked_data = document_splitter.process_documents()
        print(f"Successfully chunked data to {len(chunked_data)} chunks.")

        save_embeddings(chunked_data,f"{folder_name}/chunked_content.jsonl")
        print("Successfully saved chunked data jsonl file.")

        document_embedding = EmbeddingClient(embedding_api_key=GEMINI_API_KEY)

        embedding_data = document_embedding.generate_embeddings(chunked_data)

        save_embeddings(embedding_data,f"{folder_name}/embeddings.jsonl")
        print("Successfully saved embedding data jsonl file.")

        return f"{folder_name}/embeddings.jsonl"

    embedding_data_path = generate_chunks_and_embeddings(documents_list, "local_db") # pylint: disable=W0612

    embeddings_data = load_embeddings("local_db/embeddings.jsonl")

    def create_vector_db(embeddings_data: list, folder_name: str, db_name: str, collection_name: str):

        retriever_instance = CustomMilvusClient(uri=f"{folder_name}/{db_name}.db")

        retriever_instance.create_collection(collection_name=collection_name,
                                            embedding_dimension=768,
                                            vector_field_name="chunk_embedding",
                                            primary_field_name="chunk_id")

        retriever_instance.insert_data_to_collection(collection_name=collection_name,
                                                    data=embeddings_data)

        return f"{folder_name}/{db_name}.db", collection_name

    milvus_db, milvus_collection = create_vector_db(embeddings_data, # pylint: disable=W0612
                                                    folder_name="local_db",
                                                    db_name="local_milvus",
                                                    collection_name="local_pdf_rag")
# initial_setup()
### --- SETUP END ---

### --- TESTING Vector DB ---
def run_test():
    """Testing the connection to vector db and embeddings"""
    def test_vector_db(milvus_db, milvus_collection, query):

        retriever_instance = CustomMilvusClient(uri=milvus_db)
        embedding_instance = EmbeddingClient(embedding_api_key=GEMINI_API_KEY)

        query_embedding = embedding_instance.get_query_embeddings(content=query)

        docs = retriever_instance.query_collection(collection_name=milvus_collection,
                                                    query_embedding=query_embedding,
                                                    limit=5,
                                                    output_fields=["content", "page_span","document_metadata"])
        print(docs[0][0])
        return docs

    test_vector_db("local_db/local_milvus.db", "local_pdf_rag", "How to make chilli con carne?")
# run_test()
### --- TESTING END ---
