# Gen AI Mini Projects
This is a repo to implement some Gen AI usecases that seemed interesting.
List of projects/ideas I plan to implement:
- **ChatBots**
  - [x] Basic ChatBot -> [simple-gemini-chatbot](https://github.com/Ruthvik-1411/GenAI-Projects/tree/main/simple-gemini-chatbot#simple-multimodal-chatbot)
  - [x] RAG Based ChatBot (basic) -> [simple-rag-chatbot-with-mesop-ui](https://github.com/Ruthvik-1411/GenAI-Projects/tree/main/simple_rag_bot#simple-rag-chatbot-with-mesop-ui)
  - [ ] RAG Based ChatBot (Complex datasets, using different techniques)
      + Diverse domains, something llm's are not trained on.
      + Various File formats, PDF, Docx, HTML, images, txt. Multimodal embeddings.
      + Rich enough data for retrieval + generations + evals using different techniques for chunking, retrieving...
      + Always on the lookout for such datasets.
- **NL2SQL**
  - [ ] Basic NL2SQL Bot on simple data with viz.
  - [ ] Agentic N2SQL Bot
      * Generate insights, decompose queries, recommendations using adv techniques
      * Use code execution where required. Custom code exec can also be explored.
- **Webscraping**
  - [ ] Webscraping/Research Agent to generate reports.
      * Kind of like deep research, ref: [anthropic blog](https://www.anthropic.com/engineering/built-multi-agent-research-system)
      * Citations, report generation etc. 
- **Media Generation**
  - [x] Youtube Thumbnail Generator -> [yt_thumbnail_generation](https://github.com/Ruthvik-1411/GenAI-Projects/tree/main/yt_thumbnail_generation#youtube-thumbnail-generation)
  - [ ] Short story generator with images.
      * Generates image slides to depict a story. Ensure character consistency.
  - [ ] Short Video generator (max 30s). (Costly with veo, but good exploration)
- **Live Application** (Multimodal Live)
  - [x] Boilerplate code for multimodal applications for prototyping. -> [Gemini Live BoilerPlate](https://github.com/Ruthvik-1411/GenAI-Projects/tree/main/gemini_live_boilerplate)
  - [ ] A simple bank teller agent that helps gather some information about a/c balance, payments made etc (access to tools)
  - [ ] Live gent with access to some data and bunch of tools.(complex)
- **Agentic Applications** (explore MCP along the way)
  - [ ] Website designing agent integrated with some IDE like copilot or via UI.
      * Creates and saves files, edits them based on requirement. Kind of like Replit.
  - [ ] API Integration assistant native to an IDE
      * Helps in providing code references using docs of python package or library or some API docs.
      * Modifies source code, create git branches etc to make edits in the code. 

* I'll add more ideas as they come up.

_Note: These implementations are just to have a hands on experience with the latest models and frameworks. The code might not always be written as per best practices, but I try to do as much as I can. I will also be adding any learning for topics that I found interesting when implementing these mini projects._
