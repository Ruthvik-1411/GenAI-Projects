## Simple Multimodal Chatbot
This is a basic implementation of chat interface with Gemini models. 
- The setup uses streamlit for UI and Langchain framework for model inference(very basic).
- Uses Gemini API key from Google AI studio.

### Some Key features
- Uses Multimodal models from google for inference.
- Option to choose from a list of available models.
- Short term persistent memory stored in session states. (New session can be created as required)
- File display in message window to list files upload during the session per each message.

**Further steps can include addition of prompts to align the chatbot with specific usecase. Since the goal was to just implement a basic chatbot, this was not done.**

### Folder structure
```
simple-gemini-chatbot/
├─ assets/ -> Screenshots of the app
├─ src/
│  ├─ backend/
│  │  ├─ bot/
│  │  │  ├─ chat.py -> Wrappers to make LLM call
│  │  │  ├─ prompts.py
│  │  ├─ utils/
│  │  │  ├─ utility.py -> Functions for message transformation for llm
│  │  ├─ config.py -> API keys
│  │  ├─ ml_config.py -> Configs related to model and other settings
│  │  ├─ streamlit_ui.py -> Streamlit UI code
│  ├─ requirements.txt
├─ tests/
├─ README.md
```
### Screenshot
<img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/simple-gemini-chatbot/assets/streamlit-ui-001.png">