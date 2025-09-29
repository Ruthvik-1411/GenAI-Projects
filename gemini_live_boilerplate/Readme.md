# Gemini Live Voice Agent

This repository contains the full-stack source code for a real-time, bidirectional voice-based conversational AI agent. The project leverages the power of the Google Gemini Live API and WebSockets to create a seamless, low-latency conversational experience directly in the web browser.

Most of the boilerplate code or guides for Multimodal Live application out there are either built as a react app or some other heavy modules, requiring additional installations and setup. What I wanted to build was a simple, light-weight system which decouples the client, server and keeps components reusable. That way server modifications can be done as needed by the developers and client side, can be packaged into an app, used in a browser or even better, by a telephony system.

The application is split into two main components:
-   **`server/`**: An asynchronous Python backend that handles WebSocket connections, manages the audio stream to and from the Gemini API, and executes function calls.
-   **`client/`**: A vanilla JavaScript frontend that captures microphone audio, plays back the Model's response, and displays the conversation transcript.

## Core Features

-   **Full Duplex Communication**: Real-time, bidirectional audio streaming between the client and server for natural, uninterrupted conversation.
-   **Low Latent Interaction with Gemini Live**: Utilizes the Google Gemini Live API for sophisticated language understanding, response generation, and speech synthesis.
-   **Dynamic Function Calling**: The Model can execute predefined server-side Python functions (tools) to perform actions in the real world, like scheduling meetings or querying databases and interacting with other systems.
-   **High-Performance Asynchronous Backend**: Built with Python, Quart, and `asyncio` to efficiently handle multiple concurrent WebSocket connections.
-   **Responsive Web-Based UI**: A lightweight, modern frontend built with standard web technologies for maximum compatibility and performance.
-   **Session Recording**: Automatically saves the full conversation (user and model audio) as a mixed MP3 file for analysis.
-   **Async Tool Calling**<span style="color:green">**[NEW]**</span>: Tools (functions) can be executed asynchronously, allowing non-blocking operations such as API calls or long-running tasks.
-   **Bot-Initiated Session End**<span style="color:green">**[NEW]**</span>: The model can proactively end a session by invoking the `end_call` tool, useful for scenarios where the conversation is complete.
-   **Stateful Tool Context**<span style="color:green">**[NEW]**</span>: Tools now share state through `ToolContext`, enabling memory and continuity across multiple tool calls within the same session making use of any startup session info.

## High-Level Architecture

The system operates on a classic client-server model connected via WebSockets. This allows for a persistent, low-latency communication channel required for real-time audio.

1.  The **Client** captures microphone audio and sends it as a stream of binary chunks over a WebSocket connection.
2.  The **Server** receives this stream and forwards it directly to the **Google Gemini Live API**.
3.  Gemini processes the audio in real-time, generating transcripts, audio responses, and requests to call tools.
4.  The **Server** streams the AI's audio response back to the **Client**, which plays it instantly. It also handles tool calls by executing local Python functions and sending the results back to Gemini.
5.  All events (transcripts, tool calls, status changes) are sent as JSON messages, allowing the **Client** to update the UI dynamically.
6.  Tool calls are executed asynchronously, and results can be shared across multiple invocations using a session-specific `ToolContext`. The bot can also end the call gracefully if needed.

**High Level Architecture with Client and Sever Interaction**:
<img src="./assets/gemini_live_overall.png">

## Technology Stack

| Component               | Technologies                                                                     |
| ----------------------- | -------------------------------------------------------------------------------- |
| **Server (Backend)**    | Python 3.9+, Quart, `google-genai`, `websockets`, `pydub`, `asyncio`             |
| **Client (Frontend)**   | Vanilla JavaScript (ES6 Modules), HTML5, CSS3, Web Audio API (AudioWorklets)     |
| **Core API**            | Google Gemini Live API  (`gemini-2.0-flash-live`)                                |

**UI Samples**:<br>
<img src="./assets/gemini_live_ui.png">

## Getting Started

To run the full application, you will need to set up and run both the server and the client.

### Prerequisites

-   Git
-   Python 3.9+ and `pip`
-   A Google AI Studio API Key

### 1. Clone the Repository

```bash
git clone https://github.com/Ruthvik-1411/GenAI-Projects
cd GenAI-Projects/gemini_live_boilerplate
```

### 2. Set Up and Run the Backend Server

The server handles all the heavy lifting and communication with the Gemini API.

```bash
# Navigate to the server directory
cd server

# Install dependencies (in a virtual environment)
pip install -r requirements.txt

# Create a .env file with your API key in your IDE or use this:
echo "AISTUDIO_API_KEY='YOUR_GOOGLE_AISTUDIO_API_KEY'" > .env

# Run the server
python app.py
```
> Additional Installations: ffmpeg https://www.ffmpeg.org/download.html https://www.gyan.dev/ffmpeg/builds/

The server should now be running on port `8081`.

> For detailed instructions on server configuration, API, and architecture, see the **[Server README](./server/Readme.md)**.

### 3. Set Up and Run the Frontend Client

The client is a static web application that needs to be served by a simple web server.

```bash
# In a new terminal, navigate to the client directory
cd client

# Start a simple Python web server
python -m http.server 8080
```

### 4. Access the Application

Open your web browser and navigate to:

**`http://localhost:8080`**

You should see the user interface. You can now start a session and begin conversing with the AI.

> For a breakdown of the client's components, UI logic, and data flow, see the **[Client README](./client/Readme.md)**.

## Project Structure

```
/
├── client/          # Contains the frontend web application.
│   ├── main.js
│   ├── api-client.js
│   ├── audio-player.js
│   ├── audio-recorder.js
│   ├── pcm-player-processor.js
│   ├── pcm-recorder-processor.js
│   ├── index.html
│   ├── style.css
│   └── README.md    # <-- Detailed client documentation
│
├── server/          # Contains the backend WebSocket server.
│   ├── app.py
│   ├── env.example
│   ├── gemini_live_handler.py
│   ├── prompt.py
│   ├── requirements.txt
│   ├── tool_context.py
│   ├── tools.py
│   ├── utils.py
│   └── README.md    # <-- Detailed server documentation
│
└── README.md        # You are here.
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.