# Simple RAG ChatBot with Mesop UI
A modular and simple Retrieval-Augmented Generation (RAG) chatbot, featuring a beautiful UI using Mesop and flexible orchestration powered by LangGraph. Designed for experimentation, viewing diagnostics, citeable responses and rich text elements. This is a very minimal implementation of the actual rag system, with more focus on UI and minimal rag orchestration. The idea was to make a boiler plate version, which can be further improved with agentic systems.

## Features
- Mesop UI - clean, reactive chat interface with
    - Citation chips for rag based responses.
    - Response diagnostic viewer
    - Copyable bot responses and diagnostic info for downstream tasks.
- LLM - Gemini Models using AGoogle AI Studio
- Retriever - High performance semantic search using Milvus Vector DB.
- LangGraph Orchestration:
    - Nodes: `Router`, `Rewriter`, `Generator` etc
    - Easy to manage states and handle tool calls.
- PDF knowledge base:
    - Recursive chunking over small sample of 7 PDFs.
    - Covers knowledge of: Agents & LLMs, Recipes and Climate Change.

## Components

### Mesop
[Mesop](https://github.com/mesop-dev/mesop) it allows building of rich UI elements using python and has a similar level of customization as one would have when building a prototype using react/angular. The [docs](https://mesop-dev.github.io/mesop/) have a lot of ready to use components, easy to modify and customizable as required. I've already built a couple of prototypes using streamlit, it is beginner friendly, but to add custom components, Mesop seemed like a good choice and I would get a chance to tryout a new framework as well.

### LLMs and Embeddings
Google AI studio provides free access to Google's latest Gemini models with comfortable rate limits. For this workflow, i've used `gemini-2.0-flash-001`, being faster, less costly(free anyway) and suitable for this usecase. Used the `text-embedding-004` for getting embeddings during chunking and runtime.

### Retriever
[Milvus](https://github.com/milvus-io/milvus) is a high performance semantic vector db, supports multimodal embeddings, intuitive filters for better vector search. I've already tried using `ChromaDB` and wanted to tryout a new vector DB, hence the choice of Milvus. The [docs](https://milvus.io/docs/quickstart.md) are pretty clear and easy to follow. The main reason for using Milvus was it being used in a lot of production grade usecases, hence it would be nice to get familiar with it.

One issue I've faced down the line when using Milvus (which was my mistake entirely) was it's lack of support for Windows. I've done most of my initial experimentation in colab notebooks, so no issues then. When the time came to make the local setup, I've noticed that milvus isn't fully supported on windows. Had to switch my dev environment to ubuntu.

### LangChain and LangGraph
Used LangChain for document chunking and LangGraph for the workflow orchestration. 

Langchain text splitters support a lot of file formats and chunking strategies. To keep the implementation simple, I've used a small corpus of 7 pdfs covering three topics: Agents & LLMs, Recipes and Climate changed. A relatively smaller sample to build a minimal workflow.
- Used `Recursive text splitter` with some text cleaning to chunk the documents.
- Added page metadata during text splitting, to retain chunk metadata such as page index and character index for each chunk.
- Created an embeddings file for all created chunks to be used later.(Added rate limits to avoid quota errors while generating embeddings)

A custom workflow was built using Langgraph as shown in the image below. The workflow mainly follows these steps:
- `Query rewrite`: All user queries are rewritten based on chat history to be standalone. If not related to history, they are returned as is. This ensure that the downstream modules can work with the standlone query.
- `Router`: LLM with retriever tool is made to decide if the query requires usage of tool or it's a simple chit-chat.
- `Chit-Chat`: This node handles simple greetings and chitchat, router node routes the workflow to this node to handle such queries.
- `Generate`: Router routes to generate node after making a tool call and getting relevant sources. This node generate a response to user query based on retrieved sources and chat history.

Implementation workflow:
<img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/simple_rag_bot/assets/graph_v1.png">

Demo Video:
Coming Soon...


### Development
To use the code in this repo, simply clone the repo, navigate to the `simple_rag_bot` folder.
- Create your venv and install the required packages.
- Change directory to src folder and run your code from the src folder.
- Add your GEMINI API key in the `config.py` file.
- Visit the `setup.py` file to make the initial setup for chunking, creating embeddings. Save the embeddings in a jsonl file and use the MilvusClient to create a db collection and insert the data.
- After the setup is done, run the `app.py` file to see the UI and chat with the bot.

```
- git clone https://github.com/Ruthvik-1411/GenAI-Projects.git
- cd simple_rag_bot
- python -m venv your-env
- source venv/bin/activate (for linux)
- cd src
- pip install -r requirements.txt
(Add Gemini API key in backend/config.py)
(Run backend/setup.py after understanding the code)
- python backend/setup.py
- mesop app.py
```
## Folder Structure
```
simple_rag_bot/
├─ assets/ -> Screenshots of the app
├─ documents/ -> pdf files used for RAG
├─ notebooks/ -> runnable notebooks with same implemenation as in code
├─ src/
│  ├─ app.py # Entry point for mesop code
│  ├─ requirements.txt
│  ├─ backend/
│  │  ├─ core/
│  │  │  ├─ chat.py -> has actual code implementation of chatbot e2e
│  │  │  ├─ chunking.py -> document splitter for chunking pdf files
│  │  │  ├─ embeddings.py -> embedding client for generating embeddings
│  │  │  ├─ prompts.py -> prompts used throughout the code
│  │  │  ├─ retriever.py -> milvus client for querying the vector db
│  │  │  ├─ tools.py -> tool orchestration using all above functions
│  │  ├─ local_db/
│  │  │  ├─ .jsonl -> embeddings jsonl files
│  │  │  ├─ local_milvus.db -> milvus db used for query
│  │  ├─ utils/
│  │  │  ├─ utility.py -> All util functions
│  │  ├─ config.py -> API keys
│  │  ├─ ml_config.py -> Configs related to model and other settings
│  │  ├─ setup.py -> Initial setup to chunk, embed and insert to db
│  ├─ mesop_components
│  │  ├─ mesop_chat.py -> chat elements for main chat box in UI
│  │  ├─ copy_to_clipboard -> component for copying using mesop
├─ README.md
```