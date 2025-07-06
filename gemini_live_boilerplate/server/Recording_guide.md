# Recording User and Model Audio

## The Need for Observability

In traditional text-based chat applications, developers have direct access to the conversation history. This log of messages provides a clear, chronological record of the interaction, which is invaluable for debugging, analysis, and improving the user experience.

However, in a real-time, bidirectional voice application like this one, the context and conversation history are managed entirely by the Gemini Live API on the server side. Without a persistent record, we lose crucial observability into the session.

To bridge this gap, this application implements a robust audio recording system. It captures both the user's input and the model's audio response for the entire duration of a session. This merged recording serves as a comprehensive log, enabling:
-   **Quality Assurance:** Reviewing conversations to identify issues or areas for improvement.
-   **Debugging:** Understanding the context that led to an unexpected model response or behavior.
-   **Compliance and Archiving:** Storing a complete record of interactions.

## Key Technical Considerations

Before diving into the implementation, it's essential to understand the technical constraints and characteristics of the audio streams:

1.  **User Audio (Client -> Server):** The audio stream sent from the client to the Gemini Live API must be in `16-bit PCM, 16kHz, mono` format.
2.  **Model Audio (Server -> Client):** The audio stream received from the Gemini Live API is in `16-bit PCM, 24kHz, mono` format.
3.  **Asymmetrical Streams:** The user's audio is streamed continuously to the server throughout the session. This is a fundamental requirement for features like barge-in (interrupting the model). In contrast, the model's audio is only streamed back when it is actively speaking. Consequently, in a one-minute session, the user audio track will be one minute long, while the model's audio might only total 30 seconds, split across multiple turns.

## Implementation Strategy

Our approach is to use the continuous user audio stream as the primary "base track" for the recording. We then overlay the timestamped model audio segments onto this base track to create a single, mixed audio file.

The implementation details can be found in the `_save_recording()` function within `server/app.py`.

### Step 1: Capturing the User Audio (The Base Track)

The user's audio is the foundation of our recording. Because it is streamed continuously from the start to the end of the session, it provides a perfect, unbroken timeline.

This continuous stream is necessary for the Gemini API's Voice Activity Detection (VAD) to support **barge-in**. When the model is speaking, the API is still listening to the user's stream. If it detects user speech, it interrupts the model's output to listen to the user. This creates a natural conversational flow but reinforces why the user audio track is always longer and continuous.

During the session, all incoming user audio chunks are collected and stored in a list. At the end of the session, these chunks are concatenated to form a single, complete audio segment using the `pydub` library.

### Step 2: Capturing and Timestamping Model Audio

This is the more complex part of the process due to two main challenges:

1.  **Sample Rate Mismatch:** The model's audio (24kHz) has a different sample rate than the user's audio (16kHz). It must be resampled before it can be mixed.
2.  **Intermittent Playback:** The model speaks in turns. We need to know *exactly* when each model utterance occurred relative to the start of the session to overlay it correctly on the base track.

Our solution is to treat each continuous model utterance as a single event.

-   **Marking Start Time:** When the server receives the *first* audio chunk for a new model utterance, it records a timestamp. This timestamp is the elapsed time (in milliseconds) since the session began.
-   **Buffering Chunks:** All subsequent audio chunks for that same utterance are collected and buffered into a single, larger byte string.
-   **Finalizing the Utterance:** When the server receives a `turn_complete` signal from the API, the buffered audio data and its start timestamp are stored together as a complete "model audio event".

This process is repeated for every turn the model takes, resulting in a list of timestamped model audio events: `[(start_ms_1, audio_data_1), (start_ms_2, audio_data_2), ...]`.

### Step 3: Mixing and Saving the Final Recording

Once the session ends, the final recording is assembled:

1.  **Create Base Track:** The complete user audio track is created from the collected chunks at 16kHz.
2.  **Iterate and Overlay:** The system iterates through the list of timestamped model audio events. For each event:
    a. The model's audio data (at 24kHz) is loaded into a `pydub` audio segment.
    b. This segment is **resampled** down to 16kHz to match the base track's sample rate.
    c. The resampled model segment is **overlaid** onto the base track at its recorded `start_ms` position.
3.  **Export:** The final, mixed audio track is exported as an MP3 file, creating a complete and accurate recording of the entire conversation.

This method, developed through experimentation, reliably stitches the asymmetrical audio streams into a coherent and useful session recording.