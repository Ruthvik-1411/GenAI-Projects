"""Utility functions used at various places"""
import os
from os import listdir
from os.path import isfile, join
import json
from langchain_core.messages import HumanMessage, AIMessage

def get_files_in_dir(path):
    """Get complete path of the pdf files in dir"""
    files_list = []
    curr_dir = os.getcwd()
    for file in listdir(path):
        file_path = join(path, file)
        if file_path.endswith(".pdf") and isfile(file_path):
            absolute_file_path = os.path.join(curr_dir, file_path)
            files_list.append(absolute_file_path)

    return files_list

def save_embeddings(embeddings_data, path):
    """Save embeddings to file"""
    try:
        with open(path, 'w') as outfile:
            for entry in embeddings_data:
                json.dump(entry, outfile)
                outfile.write('\n')

        return True
    except Exception as e:
        print(f"Unable to save embeddings data due to {e}.")
        return False

def load_embeddings(path):
    """Load embeddings from jsonl file"""
    with open(path, 'r') as json_file:
        json_data = [json.loads(line) for line in json_file]

    return json_data

def format_sources(relevant_docs: list):
    """Format relevant docs into consumable format by llm"""
    sources = ""
    for i, doc in enumerate(relevant_docs[0]):
        sources += f"<Source{i + 1}>{doc['entity']['content']}</Source{i + 1}>\n"

    return sources

def format_citations(relevant_docs: list):
    """Format citations with required keys and page location"""
    citations = []
    docs = relevant_docs[0]
    for doc in docs:
        citation_data = {}
        citation_data["id"] = doc["id"]
        citation_data["content"] = doc["entity"]["content"]
        document = doc["entity"]["document_metadata"]
        citation_data["title"] = document["title"]
        citation_data["url"] = document["url"] + "#page=" + str(min(doc["entity"]["page_span"]))
        citations.append(citation_data)

    return citations

def format_chat_messages(chat_messages: list):
    """Formats chat messages list to llm consumable format"""
    chat_history = []
    for message in chat_messages:
        if message.role == "user":
            chat_history.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            chat_history.append(AIMessage(content=message.content))
        else:
            raise ValueError("Expected user/assistant role, got something else")

    return chat_history
