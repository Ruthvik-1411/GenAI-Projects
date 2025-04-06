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

# from chunking import PDFTextSplitter

# document_splitter = PDFTextSplitter()