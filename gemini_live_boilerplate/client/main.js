// main.js (Refactored with Chat UI)

import { ApiClient } from './api-client.js';
import { startAudioPlayerWorklet } from './audio-player.js';
import { startAudioRecorderWorklet } from './audio-recorder.js';

// --- Configuration ---
const WEBSOCKET_URL = 'ws://localhost:8081/ws';

// --- DOM Elements ---
const startSessionButton = document.getElementById('startSessionButton');
const micButton = document.getElementById('micButton');
const micButtonLabel = micButton.querySelector('.label');
const logContainer = document.getElementById('log');
const chatTranscriptContainer = document.getElementById('chatTranscript');
// TODO: Add session resumption in backend and use this
const pauseButton = document.getElementById('pauseButton');

// --- State ---
let isRecording = false;
let isAudioInitialized = false;
let isSessionActive = false;
let isPaused = false;
let currentUserBubble = null;
let currentModelBubble = null;

// --- Modules ---
const client = new ApiClient(WEBSOCKET_URL);
let audioPlayerNode;
let audioRecorderNode;

/**
 * Scrolls a DOM element to the bottom.
 * @param {HTMLElement} element The element to scroll.
 */
function scrollToBottom(element) {
    element.scrollTop = element.scrollHeight;
}

function updateUserMessage(chunk) {
    finalizeModelTurn(); // A user message always ends the model's previous turn.

    if (!currentUserBubble) {
        // This is the first chunk of a new turn, so create the bubble.
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble user';
        const p = document.createElement('p'); // The paragraph inside the bubble
        bubble.appendChild(p);
        chatTranscriptContainer.appendChild(bubble);
        currentUserBubble = p; // We'll update the text of this paragraph
    }

    currentUserBubble.textContent += chunk; // Update with the latest transcript
    scrollToBottom(chatTranscriptContainer);
}

function updateModelMessage(chunk) {
    // MODIFICATION: Finalize the user's turn when the model starts speaking.
    finalizeUserTurn();

    if (!currentModelBubble) {
        // This is the first chunk of a new turn, so create the bubble.
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble model';
        const p = document.createElement('p'); // The paragraph inside the bubble
        bubble.appendChild(p);
        chatTranscriptContainer.appendChild(bubble);
        currentModelBubble = p; // We'll append text directly to the paragraph
    }
    currentModelBubble.textContent += chunk;
    scrollToBottom(chatTranscriptContainer);
}

function finalizeUserTurn() {
    currentUserBubble = null;
}

function finalizeModelTurn() {
    currentModelBubble = null;
}

function logMessage(message, type = 'info') {
    const el = document.createElement('div');
    el.className = `log-message ${type}`;
    el.textContent = message;
    logContainer.appendChild(el);
    scrollToBottom(logContainer);
}

function displayToolCall(toolCallData) {
    finalizeModelTurn();
    finalizeUserTurn();

    const toolCallBubble = document.createElement('div');
    toolCallBubble.className = 'chat-bubble function-call';
    toolCallBubble.innerHTML = `
        <p class="tool-call-header"><strong>Tool Call:</strong></p>
        <p class="name">${toolCallData.name}</p>
        <div class="params">Parameters: ${JSON.stringify(toolCallData.args, null, 2)}</div>
    `;
    chatTranscriptContainer.appendChild(toolCallBubble);
    scrollToBottom(chatTranscriptContainer);
}

function base64ToUint8Array(base64) {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
}

// --- Audio Processing ---

async function initializeAudio() {
    if (isAudioInitialized) return;
    logMessage('Initializing audio systems...', 'status');
    try {
        [audioPlayerNode] = await startAudioPlayerWorklet();
        [audioRecorderNode] = await startAudioRecorderWorklet(audioRecorderHandler);
        isAudioInitialized = true;
        logMessage('Audio systems ready.', 'status');
    } catch (error) {
        logMessage(`Audio Init Error: ${error.message}`, 'error');
        throw error;
    }
}

function audioRecorderHandler(pcmData) {
    if (!isRecording || !isSessionActive || !client.isConnected()) return;
    client.sendAudio(pcmData);
}

// --- Application Logic ---
async function startRecording() {
    if (isRecording || !isSessionActive) return;
    if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
    }
    
    // Finalize turns for both UI and logs
    finalizeModelTurn();
    finalizeUserTurn();

    await initializeAudio(); // fallback
    isRecording = true;
    micButton.classList.add('recording');
    micButtonLabel.textContent = 'Stop Recording';
    logMessage('Recording started...', 'status');
}

function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    client.sendEndOfSession();
    micButton.classList.remove('recording');
    micButtonLabel.textContent = 'Start Recording';
    logMessage('Recording stopped. Processing...', 'status');
}

// --- Client Event Handlers ---

client.on('open', () => {
    logMessage('WebSocket connected. Please start a new session.', 'status');
    startSessionButton.disabled = false;
});

client.on('status', async (data) => {

    if (data === 'setup_complete') {
        logMessage('Server is ready. Initializing audio...', 'success');
        isSessionActive = true;
        await initializeAudio();
        micButton.disabled = false;
        startSessionButton.disabled = true; // Don't let user start another session
        startSessionButton.style.display = 'none';
        await startRecording();
        logMessage('Session active. Listening...', 'status');
    } else {
        console.info(`[APP] Client status: ${data}`);
    }
});

client.on('user_transcript', (chunk) => {
    updateUserMessage(chunk);
});

client.on('model_transcript', (chunk) => {
    updateModelMessage(chunk);
});

client.on('audio_chunk', (base64Data) => {
    if (!audioPlayerNode) return
    const audioChunk = base64ToUint8Array(base64Data);
    audioPlayerNode.port.postMessage(audioChunk.buffer, [audioChunk.buffer]);
});

client.on('tool_call', (toolCallData) => {
    displayToolCall(toolCallData);
});

client.on('turn_complete', (data) => {
    logMessage(data, 'status');
});

client.on('interrupt', (data) => {
    logMessage(`Server signaled interrupt. Reason: ${data.reason || 'None provided'}`, 'status');
    if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
    }
});

client.on('error', (data) => {
    logMessage(`Server Error: ${data || 'An unknown error occurred.'}`, 'error');
    micButton.disabled = true;
});

client.on('close', () => {
    // Finalize turns for both UI and logs on close
    finalizeModelTurn();
    finalizeUserTurn()
    logMessage('Connection closed.', 'status');
    isSessionActive = false;
    isRecording = false;
    micButton.disabled = true;
    micButton.classList.remove('recording');
    micButtonLabel.textContent = 'Start Recording';
    startSessionButton.disabled = false;
    startSessionButton.style.display = 'block';
    // micButton.disabled = true;
    if (isRecording) {
        stopRecording();
    }
});

// --- Initialize ---

startSessionButton.addEventListener('click', () => {
    startSessionButton.disabled = true;
    logMessage('Starting session...', 'status');
    client.sendStartSession();
});

micButton.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

startSessionButton.disabled = true;
micButton.disabled = true;
logMessage('Connecting to server...', 'status');
client.connect().catch(() => {
    logMessage('Failed to connect to the server.', 'error');
});

// TODO: Add logic for session pause, new session buttons and event handlers
