"""Module for backend websocket server"""
# pylint: disable=line-too-long,too-many-branches,unused-variable,too-many-statements
import os
import time
import json
import base64
import asyncio
import logging
from dotenv import load_dotenv
from pydub import AudioSegment
from quart import Quart, websocket
from google.genai import types as genai_types

from gemini_live_handler import GeminiClient
from tools import schedule_meet_tool, cancel_meet_tool

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

log_queue = asyncio.Queue()
app = Quart(__name__)

async def log_worker():
    """Background task for handling logging to non block the main thread"""
    while True:
        try:
            message = await log_queue.get()
            logger.handle(message)
            log_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Log worker cancelled.")
            break
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in log worker: {e}", exc_info=True)

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
        self.session_started_event = asyncio.Event()
        self._tasks = []
        self.user_audio_chunks = []
        self.model_audio_chunks = []
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

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
                    # Continue receiving after setting event
                    continue

                if message_event == "audio_chunk":
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

                # To handle client side interrupt in future
                # elif message_event == "interrupt":
                #     # Client wants to interrupt
                #     logger.info(f"[{self.connection_id}] Interrupt received from client.")
                #     # Clear response queue and stop current audio
                #     self._clear_response_queue()

                else:
                    logger.warning(f"[{self.connection_id}] Unknown message event: {message_event}")

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
                            logger.warning(f"[{self.connection_id}] Gemini interruption detected!")
                            await self.response_queue.put({"event": "interrupt", "data": {"reason": "server_interrupt"}})

                        # For input and output transcripts
                        if server_content.input_transcription and server_content.input_transcription.text:
                            text = server_content.input_transcription.text
                            logger.info(f"[{self.connection_id}] User transcript: '{text}'")
                            await self.response_queue.put({"event": "user_transcript", "data": text})

                        if server_content.output_transcription and server_content.output_transcription.text:
                            text = server_content.output_transcription.text
                            logger.info(f"[{self.connection_id}] Model transcript chunk: '{text}'")
                            await self.response_queue.put({"event": "model_transcript", "data": text})

                        # This is for audio chunks primarily
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    self.model_audio_chunks.append(part.inline_data.data)
                                    audio_b64 = self.gemini.convert_audio_for_client(part.inline_data.data)
                                    await self.response_queue.put({"event": "audio_chunk", "data": audio_b64})

                        if server_content.turn_complete or server_content.generation_complete:
                            logger.info(f"[{self.connection_id}] Model turn complete")
                            await self.response_queue.put({"event": "turn_complete", "data": "Model turn complete"})

                    # TODO: Add end call tool handling. Bot can end websocket connection.
                    if response.tool_call and response.tool_call.function_calls:
                        function_responses = []
                        for func_call in response.tool_call.function_calls:
                            tool_call_name = func_call.name
                            tool_call_args = func_call.args
                            logger.info(f"Tool call with {tool_call_name} {tool_call_args}")
                            await self.response_queue.put({"event": "tool_call","data": {"name": tool_call_name, "args": tool_call_args}})
                            function_response = self.gemini._call_function(
                                fc_id=func_call.id,
                                fc_name=tool_call_name,
                                fc_args=tool_call_args
                            )
                            # TODO: Send function response event to client
                            function_responses.append(function_response)
                        await self._gemini_session.send_tool_response(function_responses=function_responses)

        except asyncio.CancelledError:
            logger.info(f"[{self.connection_id}] Gemini processor task cancelled.")
        except Exception as e:
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
            receiver = asyncio.create_task(self._receive_from_client(), name=f"receiver[{self.connection_id}]")
            processor = asyncio.create_task(self._process_gemini_stream(), name=f"processor[{self.connection_id}]")
            sender = asyncio.create_task(self._send_to_client(), name=f"sender[{self.connection_id}]")

            self._tasks = [receiver, processor, sender]

            # Wait for any one of the task to complete
            done, pending = await asyncio.wait(
                self._tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # TODO: Handle task ending better, check for pending tasks status and clean up.
            for task in done:
                exc = task.exception()
                if exc:
                    logger.error(f"[{self.connection_id}] Task {task.get_name()} failed with exception: {exc}", exc_info=exc)
                else:
                    logger.info(f"[{self.connection_id}] Task {task.get_name()} completed first.")

        # TODO: Hnadle websockets.exceptions.ConnectionClosedOK
        except Exception as e:
            logger.error(f"[{self.connection_id}] Error in connection handler main wait: {e}", exc_info=True)
        finally:
            logger.info(f"[{self.connection_id}] Cleaning up connection and all tasks...")
            # Cancel any tasks that are still pending
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Wait for all tasks to acknowledge cancellation
            await asyncio.gather(*self._tasks, return_exceptions=True)

            self._clear_all_queues()
            await self._save_recording()
            logger.info(f"[{self.connection_id}] Connection handler cleanup complete.")

    # TODO: Combine the audio on both user and model streams
    # Tried mixing them but a lot of issues came up.
    async def _save_recording(self):
        """Saves the user and model audio streams as two seperate MP3 file."""
        logger.info(f"[{self.connection_id}] Preparing to save session recording.")
        if not self.user_audio_chunks or not self.model_audio_chunks:
            logger.info(f"[{self.connection_id}] No audio chunks for atleast user/model to save. Skipping.")
            return

        save_tasks = []

        if self.user_audio_chunks:
            try:
                def save_user_task():
                    logger.info(f"[{self.connection_id}] Processing user audio...")
                    user_full_audio = b"".join(self.user_audio_chunks)
                    user_segment = AudioSegment(
                        data=user_full_audio,
                        sample_width=2,      # 16-bit
                        frame_rate=16000,    # User audio is 16kHz
                        channels=1           # Mono
                    )
                    filepath = os.path.join(RECORDINGS_DIR, f"{self.connection_id}_user.mp3")
                    user_segment.export(filepath, format="mp3", bitrate="96k")
                    logger.info(f"[{self.connection_id}] User recording saved to {filepath}")

                save_tasks.append(asyncio.to_thread(save_user_task))
            except Exception as e:
                logger.error(f"[{self.connection_id}] Failed to process user audio:", exc_info=True)

        if self.model_audio_chunks:
            try:
                def save_model_task():
                    logger.info(f"[{self.connection_id}] Processing and resampling model audio...")
                    model_full_audio = b"".join(self.model_audio_chunks)

                    # The raw audio from model is at 24kHz sample rate
                    model_segment_raw = AudioSegment(
                        data=model_full_audio,
                        sample_width=2,
                        frame_rate=24000,    # Model output audio is 24kHz
                        channels=1
                    )

                    # Resample to 16kHz to standardize and fix the playback speed
                    model_segment_resampled = model_segment_raw.set_frame_rate(16000)

                    filepath = os.path.join(RECORDINGS_DIR, f"{self.connection_id}_model.mp3")
                    model_segment_resampled.export(filepath, format="mp3", bitrate="96k")
                    logger.info(f"[{self.connection_id}] Model recording saved to {filepath}")

                save_tasks.append(asyncio.to_thread(save_model_task))
            except Exception as e:
                logger.error(f"[{self.connection_id}] Failed to process model audio:", exc_info=True)

        if save_tasks:
            await asyncio.gather(*save_tasks)
            logger.info(f"[{self.connection_id}] All audio saving tasks complete.")
        else:
            logger.info(f"[{self.connection_id}] No audio chunks to save for either speaker. Skipping.")

# --- Quart Routes ---

@app.websocket("/ws")
async def websocket_endpoint():
    """Handles incoming WebSocket connections"""
    handler = WebSocketHandler(websocket)
    await handler.handle_websocket_connection()

@app.before_serving
async def startup():
    """Startup tasks"""
    app.background_task = asyncio.create_task(log_worker())
    logger.info("Server starting up.")

@app.after_serving
async def shutdown():
    """Cleanup tasks"""
    logger.info("Server shutting down.")
    try:
        if hasattr(app, 'background_task') and app.background_task:
            app.background_task.cancel()
            await app.background_task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

# TODO: Maybe add a route to fetch recording data after session ends in UI.

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8081"))
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug_mode, use_reloader=debug_mode)
