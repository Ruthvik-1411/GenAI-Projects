"""Main module, yet to be modified"""
from backend.core.chat import generate_rag_response

print(generate_rag_response(input="How to make chilli con carne?", history=[]))
