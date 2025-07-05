"""Module for backend websocket server"""
# pylint: disable=line-too-long,too-many-branches,unused-variable,too-many-statements
import os
import time
import json
import base64
import asyncio
import logging
from dotenv import load_dotenv
from websockets.exceptions import ConnectionClosedOK
from pydub import AudioSegment
from quart import Quart, websocket

from gemini_live_handler import GeminiClient
from tools import schedule_meet_tool, cancel_meet_tool # pylint: disable=no-name-in-module

RECORDINGS_DIR = "recordings"

load_dotenv()

gemini_api_key = os.getenv("AISTUDIO_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = Quart(__name__)

class WebSocketHandler:
    """Manages a single WebSocket connection and its interaction with Gemini Live API."""

    def __init__(self, ws):
        self.websocket = ws
        self.gemini = None
        self.audio_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        self.connection_id = f"conn_{int(time.time() * 1000)}"
        self._gemini_session = None
        self._gemini_client_initialized = False
        self.session_usage_metadata = None
        self.session_started_event = asyncio.Event()
        self._tasks = []

        self.session_start_time = None
        self.user_audio_chunks = []
        self.model_audio_events = []
        self.current_model_utterance_chunks = []
        self.current_model_utterance_start_ms = None
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

    def _finalize_and_store_model_utterance(self):
        """Combines collected model chunks into a single event and stores it."""
        if self.current_model_utterance_start_ms is not None and self.current_model_utterance_chunks:
            # Combine all chunks for this utterance into a single byte string
            full_utterance_data = b"".join(self.current_model_utterance_chunks)

            self.model_audio_events.append(
                (self.current_model_utterance_start_ms, full_utterance_data)
            )
            logger.info(
                f"[{self.connection_id}] Finalized model utterance. "
                f"Start: {self.current_model_utterance_start_ms}ms, "
                f"Chunks: {len(self.current_model_utterance_chunks)}"
            )

        # Reset the state
        self.current_model_utterance_chunks = []
        self.current_model_utterance_start_ms = None

    async def _receive_from_client(self):
        """Handles receiving messages from the client"""
        logger.info(f"[{self.connection_id}] Receiving task started.")
        try:
            while True:
                message = await self.websocket.receive()

                data = json.loads(message)
                message_event = data.get("event")

                logger.debug(f"[{self.connection_id}] Received: {message_event}")

                if message_event == "start_session":
                    logger.info(f"[{self.connection_id}] Start session event received.")
                    self.session_started_event.set()
                    custom_params = data.get("custom_parameters")
                    logger.info(f"[{self.connection_id}] Data received: {custom_params}")
                    if not self.session_start_time:
                        # start the timer
                        self.session_start_time = time.monotonic()
                    continue

                elif message_event == "audio_chunk":
                    # Handle audio data from client
                    audio_data = data.get("data")
                    if audio_data:
                        try:
                            decoded_audio = base64.b64decode(audio_data)
                            self.user_audio_chunks.append(decoded_audio)
                            await self.audio_queue.put(decoded_audio)
                        except Exception as e:
                            logger.error(f"[{self.connection_id}] Error processing audio: {e}")

                elif message_event == "end_session":
                    # Client wants to end the session
                    logger.info(f"[{self.connection_id}] End session event received.")
                    # Exit this task gracefully. The main handler will clean up.
                    return
                else:
                    logger.warning(f"[{self.connection_id}] Unknown message event: {message_event}")

                # TODO: Handle go_away event and session resumption
                # can be implemented later, don't see a need for this now.

        except json.JSONDecodeError:
            logger.error(f"[{self.connection_id}] Invalid JSON received")
        except asyncio.CancelledError:
            logger.info(f"[{self.connection_id}] Receiving task cancelled.")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error in receiving task: {e}", exc_info=True)
        finally:
            # Signal audio stream to stop
            await self.audio_queue.put(None)

    async def _audio_stream_generator(self):
        """Generate an audio stream from the audio queue for gemini"""
        await self.session_started_event.wait()
        while True:
            try:
                audio_data = await self.audio_queue.get()
                if audio_data is None:  # Sentinel value to stop, set by receiver
                    break
                yield audio_data
                self.audio_queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"[{self.connection_id}] Audio stream generator cancelled.")
                break
            except Exception as e:
                logger.error(f"[{self.connection_id}] Error in audio stream generator: {e}", exc_info=True)
                break

    async def _process_gemini_stream(self):
        """Process audio stream with Gemini for this session"""
        if not self._gemini_client_initialized:
            logger.error(f"[{self.connection_id}] Gemini session not initialized.")
            return
        logger.info(f"[{self.connection_id}] Gemini processor task started.")

        try:
            try:
                logger.info(f"[{self.connection_id}] Gemini processor waiting for 'start_session' event from client.")
                await asyncio.wait_for(
                    self.session_started_event.wait(),
                    timeout=30
                )
            except asyncio.TimeoutError:
                # If the timeout is reached, send an error message to client
                logger.warning(f"[{self.connection_id}] Timed out waiting for 'start_session' event.")
                # Send an error message to the client
                await self.response_queue.put({
                    "event": "error",
                    "data": "Session timed out after 30 seconds. Please reconnect."
                })
                # Exit this task gracefully. The main handler will clean up.
                return
            logger.info(f"[{self.connection_id}] 'start_session' event received. Proceeding with Gemini connection.")

            async with self.gemini.client.aio.live.connect(
                model=self.gemini.model_id, config=self.gemini.config
            ) as session:
                self._gemini_session = session
                logger.info(f"[{self.connection_id}] Gemini live session started.")

                await self.response_queue.put({"event": "status", "data": "setup_complete"})
                # Send initial response from bot
                logger.info(f"[{self.connection_id}] Sending message on behalf of user.")
                initial_greeting = self.gemini.get_initial_greeter()

                await self._gemini_session.send_client_content(
                    turns=[initial_greeting], turn_complete=True
                )
                # Main loop to process the stream from Gemini
                async for response in self._gemini_session.start_stream(
                    stream=self._audio_stream_generator(), mime_type="audio/pcm"
                ):
                    # The processor's job is to make the sender's job easy. Only add to response queue.
                    if response.server_content:
                        server_content = response.server_content
                        if server_content.interrupted is not None:
                            logger.warning(f"[{self.connection_id}] User interruption detected!")
                            await self.response_queue.put({"event": "interrupt", "data": {"reason": "User Barge-in detected"}})

                        # For input and output transcripts
                        if server_content.input_transcription and server_content.input_transcription.text:
                            text = server_content.input_transcription.text
                            # logger.info(f"[{self.connection_id}] User transcript: '{text}'")
                            await self.response_queue.put({"event": "user_transcript", "data": text})

                        if server_content.output_transcription and server_content.output_transcription.text:
                            text = server_content.output_transcription.text
                            # logger.info(f"[{self.connection_id}] Model transcript chunk: '{text}'")
                            await self.response_queue.put({"event": "model_transcript", "data": text})

                        # This is for audio chunks primarily
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    if self.current_model_utterance_start_ms is None:
                                        # Record start time for this utterance
                                        offset_ms = int((time.monotonic() - self.session_start_time) * 1000)
                                        self.current_model_utterance_start_ms = offset_ms
                                    self.current_model_utterance_chunks.append(part.inline_data.data)
                                    audio_b64 = self.gemini.convert_audio_for_client(part.inline_data.data)
                                    await self.response_queue.put({"event": "audio_chunk", "data": audio_b64})

                        if server_content.turn_complete or server_content.generation_complete:
                            logger.info(f"[{self.connection_id}] Model turn complete")
                            # Finalize turn audio after model turn complete
                            self._finalize_and_store_model_utterance()
                            await self.response_queue.put({"event": "turn_complete", "data": "Model turn complete"})

                    # TODO: Add end call tool handling. Bot can end websocket connection.
                    elif response.tool_call and response.tool_call.function_calls:
                        function_responses = []
                        for func_call in response.tool_call.function_calls:
                            tool_call_name = func_call.name
                            tool_call_args = func_call.args
                            logger.info(f"Tool call with {tool_call_name} {tool_call_args}")
                            await self.response_queue.put({"event": "tool_call","data": {"name": tool_call_name, "args": tool_call_args}})
                            function_response = self.gemini.call_function(
                                fc_id=func_call.id,
                                fc_name=tool_call_name,
                                fc_args=tool_call_args
                            )
                            # TODO: Send function response event to client
                            # logger.info(f"Function response : {function_response.response}")
                            await self.response_queue.put({"event": "tool_response","data": {"name": tool_call_name, "args": function_response.response}})
                            function_responses.append(function_response)
                        await self._gemini_session.send_tool_response(function_responses=function_responses)

                    # Can be used later
                    elif response.usage_metadata:
                        self.session_usage_metadata = response.usage_metadata.total_token_count
                        logger.info(f"[{self.connection_id}] Session usage: {self.session_usage_metadata} tokens.")

                    else:
                        logger.warning(f"[{self.connection_id}] Unknown/Unhandled server event or type received from gemini.")
        except ConnectionClosedOK:
            # Clean shutdown.
            logger.info(f"[{self.connection_id}] Gemini WebSocket connection closed cleanly (1000 OK). This is normal.")
        except asyncio.CancelledError:
            self._finalize_and_store_model_utterance()
            logger.info(f"[{self.connection_id}] Gemini processor task cancelled.")
        except Exception as e:
            self._finalize_and_store_model_utterance()
            logger.error(f"[{self.connection_id}] Error in Gemini processor task: {e}", exc_info=True)
            await self.response_queue.put({"event": "error", "data": "gemini_processing_failed"})
        finally:
            logger.info(f"[{self.connection_id}] Gemini processor task finished.")
            # Signal the sender task to stop
            await self.response_queue.put(None)

    async def _send_message(self, message_event, data=None):
        """Send a message to the client in the expected format"""
        message = {"event": message_event}
        if data is not None:
            message["data"] = data

        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"[{self.connection_id}] Sent message: {message_event}")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error sending message: {e}")

    async def _send_to_client(self):
        """Handles sending messages to the client"""
        logger.info(f"[{self.connection_id}] Sender task started.")
        try:
            while True:
                message = await self.response_queue.get()
                if message is None: # Sentinel value to stop
                    break

                # The message is already a clean dictionary, can be used directly
                await self._send_message(message.get("event"), message.get("data"))

                self.response_queue.task_done()

        except asyncio.CancelledError:
            logger.info(f"[{self.connection_id}] Sender task cancelled.")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error in sender task: {e}", exc_info=True)
        finally:
            logger.info(f"[{self.connection_id}] Sender task finished.")

    def _clear_response_queue(self):
        """Clear the response queue"""
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
                self.response_queue.task_done()
            except asyncio.QueueEmpty:
                break

    def _clear_all_queues(self):
        """Clear all queues"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except asyncio.QueueEmpty:
                break

        self._clear_response_queue()

    async def handle_websocket_connection(self):
        """Manages the lifecycle of the WebSocket connection"""
        logger.info(f"[{self.connection_id}] New WebSocket connection.")
        # Initialize Gemini client class
        self.gemini = GeminiClient(
            api_key=gemini_api_key,
            tools=[schedule_meet_tool, cancel_meet_tool]
        )
        self._gemini_client_initialized = True

        try:
            # Start tasks
            await self.websocket.accept()
            logger.info(f"[{self.connection_id}] WebSocket connection accepted.")
            receiver = asyncio.create_task(self._receive_from_client(), name=f"receiver[{self.connection_id}]")
            processor = asyncio.create_task(self._process_gemini_stream(), name=f"processor[{self.connection_id}]")
            sender = asyncio.create_task(self._send_to_client(), name=f"sender[{self.connection_id}]")

            self._tasks = [receiver, processor, sender]

            # Wait for any one of the task to complete
            # done, pending = await asyncio.wait(
            #     self._tasks,
            #     return_when=asyncio.FIRST_COMPLETED,
            # )
            # Since gemini live throws an error if we wait for first complete
            # we wait for all tasks to complete themselves
            await asyncio.gather(*self._tasks)

        except ConnectionClosedOK:
            # Clean shutdown. Gemini library throws this exception
            logger.info(f"[{self.connection_id}] Gemini WebSocket connection closed cleanly (1000 OK). This is normal.")
        except asyncio.CancelledError:
            logger.info(f"[{self.connection_id}] WebSocket handler event loop cancelled.")
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error in connection handler main wait: {e}", exc_info=True)
        finally:
            logger.info(f"[{self.connection_id}] Cleaning up connection and all tasks...")
            self._finalize_and_store_model_utterance()

            # Cancel any tasks that are still pending
            for task in self._tasks:
                if task and not task.done():
                    task.cancel()

            if self._tasks:
                await asyncio.gather(*[t for t in self._tasks if t], return_exceptions=True)

            self._clear_all_queues()
            await self._save_recording()
            await self.websocket.close(code=1000, reason="Client initated termination.")
            logger.info(f"[{self.connection_id}] Websocket connection close with status OK.")
            logger.info(f"[{self.connection_id}] Connection handler cleanup complete.")

    async def _save_recording(self):
        """Saves the session conversation by overlaying the timestamped model audio on to
        continuous user audio stream as a single mixed MP3 file."""
        logger.info(f"[{self.connection_id}] Preparing to save session recording.")
        if not self.user_audio_chunks:
            logger.warning(f"[{self.connection_id}] No user audio chunks to create a base recording. Skipping.")
            return

        try:
            # Pydub operations are blocking, so we run them in a separate thread to
            # avoid blocking the event loop.
            def process_and_save():
                # Create the user audio track from the continuous chunks
                # The base track will be user audio as it always sends data and longer
                logger.info(f"[{self.connection_id}] Creating base user audio track...")
                user_full_audio = b"".join(self.user_audio_chunks)
                base_track = AudioSegment(
                    data=user_full_audio,
                    sample_width=2,   # 16-bit PCM
                    frame_rate=16000, # User audio/Model input is at 16kHz
                    channels=1        # Mono
                )
                logger.info(f"[{self.connection_id}] Base user track created. Duration:{len(base_track)/1000:.2f}s")

                # Overlay all the model audio chunk at its recorded offset
                if self.model_audio_events:
                    logger.info(f"[{self.connection_id}] Overlaying {len(self.model_audio_events)} model audio events...")
                    for offset_ms, full_utterance_data in self.model_audio_events:
                        # Create a segment for the complete model utterance
                        model_utterance = AudioSegment(
                            data=full_utterance_data,
                            sample_width=2,
                            frame_rate=24000, # Model output is at 24kHz
                            channels=1
                        )
                        # Resample to match the base user track
                        model_utterance_resampled = model_utterance.set_frame_rate(base_track.frame_rate)

                        # Overlay the complete, resampled utterance at its start position
                        base_track = base_track.overlay(model_utterance_resampled, position=offset_ms)
                    logger.info(f"[{self.connection_id}] Model audio overlay complete.")
                else:
                    logger.info(f"[{self.connection_id}] No model audio events to overlay.")

                # Ideally save this to a Storage like GCS and upload it, but ignore for now
                output_path = os.path.join(RECORDINGS_DIR, f"{self.connection_id}_merged.mp3")
                base_track.export(output_path, format="mp3", bitrate="128k")
                logger.info(f"[{self.connection_id}] Recording saved to {output_path}.")

            await asyncio.to_thread(process_and_save)

        except Exception as e:
            logger.error(f"[{self.connection_id}] Failed to save mixed recording: {e}", exc_info=True)

# --- Quart Routes ---

@app.websocket("/ws")
async def websocket_endpoint():
    """Handles incoming WebSocket connections"""
    handler = WebSocketHandler(websocket)
    await handler.handle_websocket_connection()

@app.before_serving
async def startup():
    """Startup tasks"""
    logger.info("Server starting up.")

@app.after_serving
async def shutdown():
    """Cleanup tasks"""
    logger.info("Server shutting down.")

# TODO: Maybe add a route to fetch recording data after session ends in UI.

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8081"))
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug_mode, use_reloader=debug_mode)
