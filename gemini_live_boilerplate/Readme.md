# Gemini Live Boilerplate

This folder consists of a simple setup for client and server based handlers to communicate with gemini live from a browser.

**Client**:
A simple html, css and js based UI to display events from server, establish connections, record and playback audio to and from the backend server. Uses seperate audio worklets to do this.

Most of the audio processing scripts were built on top of the files here. [adk-ws-streaming-docs](https://github.com/google/adk-docs/tree/main/examples/python/snippets/streaming/adk-streaming-ws/app/static/js)

**Server**:
The server uses Quart for the service endpoints as it had a lot of support and features for websocket based applications. The backend is primarily split into three different task handlers:
1. Receiver: This task receives events from the client and processes them, adding audio received from client to an audio queue and other event handling for disconnecting, session pausing etc.
2. Processor: This task handles all communication with the gemini live api(ws endpoint). It starts the session with gemini live, reads from audio queue and adds the response receieved from gemini live api to a response queue.
3. Sender: This task reads the data from the response queue and sends events/audio back the client.

**Client side:**<br>
<img src="https://github.com/Ruthvik-1411/GenAI-Projects/blob/main/gemini_live_boilerplate/assets/sample_ui.png">



TODO: update this documentation to be more descriptive and explain interaction of all events.