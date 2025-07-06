// main.js handles the actual logic to communicated with server

import { ApiClient } from './api-client.js';
import { startAudioPlayerWorklet } from './audio-player.js';
import { startAudioRecorderWorklet } from './audio-recorder.js';

// --- Configuration ---
const WEBSOCKET_URL = 'ws://localhost:8081/ws';

// --- DOM Elements ---
const startSessionButton = document.getElementById('startSessionButton');
const newSessionButton = document.getElementById('newSessionButton');
const micButton = document.getElementById('micButton');
const micButtonLabel = micButton.querySelector('.label');
const logContainer = document.getElementById('log');
const chatTranscriptContainer = document.getElementById('chatTranscript');

// --- State ---
let isRecording = false;
let isAudioInitialized = false;
let isSessionActive = false;
let currentUserBubble = null;
let currentModelBubble = null;
let currentSessionId = null;

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
    finalizeModelTurn();

    if (!currentUserBubble) {
        // This is the first chunk of a new turn, so create the bubble.
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble user';
        const p = document.createElement('p');
        bubble.appendChild(p);
        chatTranscriptContainer.appendChild(bubble);
        currentUserBubble = p;
    }

    currentUserBubble.textContent += chunk;
    scrollToBottom(chatTranscriptContainer);
}

function updateModelMessage(chunk) {
    finalizeUserTurn();

    if (!currentModelBubble) {
        // This is the first chunk of a new turn, so create the bubble.
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble model';
        const p = document.createElement('p');
        bubble.appendChild(p);
        chatTranscriptContainer.appendChild(bubble);
        currentModelBubble = p;
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
    // el.textContent = message;
    // logContainer.appendChild(el);
    // Add timestamp
    const now = new Date();
    const date = [
        now.getDate().toString().padStart(2, '0'),
        (now.getMonth() + 1).toString().padStart(2, '0'),
        now.getFullYear()
    ].join('/');
    const time = [
        now.getHours().toString().padStart(2, '0'),
        now.getMinutes().toString().padStart(2, '0'),
        now.getSeconds().toString().padStart(2, '0')
    ].join(':');
    const timestamp = `${date} ${time}`;

    // Set content with a styled span for the timestamp
    el.innerHTML = `<span class="log-timestamp">${timestamp}</span> <br>${message}`;
    logContainer.appendChild(el);
    scrollToBottom(logContainer);
}

function displayToolCall(toolCallData, toolEvent) {
    finalizeModelTurn();
    finalizeUserTurn();

    const toolCallBubble = document.createElement('div');
    toolCallBubble.className = 'chat-bubble function-call';
    toolCallBubble.innerHTML = `
        <p class="tool-call-header"><strong>${toolEvent}:</strong></p>
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

function resetApplicationState() {
    // Stop any active processes
    if (isRecording) {
        stopRecording();
    }
    if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
    }

    // Reset state variables
    isRecording = false;
    isSessionActive = false;
    currentUserBubble = null;
    currentModelBubble = null;
    currentSessionId = null;

    // Reset UI
    logContainer.innerHTML = '';
    chatTranscriptContainer.innerHTML = '';

    micButton.disabled = true;
    micButton.classList.remove('recording');
    micButtonLabel.textContent = 'Start Recording';

    startSessionButton.disabled = true; // Will be enabled on 'open'
    startSessionButton.style.display = 'block';

    logMessage('Session Reset.', 'status');
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
    displayToolCall(toolCallData, "Tool Call");
});

client.on('tool_response', (toolCallData) => {
    displayToolCall(toolCallData, "Tool Response");
});

client.on('turn_complete', (data) => {
    logMessage(data, 'status');
});

client.on('usage', (data) => {
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
    if (isRecording) {
        stopRecording();
    }
});

// --- Initialize ---

startSessionButton.addEventListener('click', () => {
    startSessionButton.disabled = true;

    const uuid = crypto.randomUUID();
    currentSessionId = uuid.replaceAll('-', '');

    // Optional parameters, to simulate data transfer
    const customParameters = {
        userId: "abcd123",
        userRole: "executive_level2",
        isMeetingHost: true
    };

    logMessage(`Starting session (ID:${currentSessionId.slice(0, 10)}..)...`, 'status');
    // Can send empty session as well
    // client.sendStartSession();
    client.sendStartSession({sessionId: currentSessionId, customParams: customParameters});
});

micButton.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

newSessionButton.addEventListener('click', () => {
    resetApplicationState();
    logMessage('New session requested. Reconnecting...', 'status');

    // Disconnect the old client if it's connected, then reconnect.
    if (client.isConnected()) {
        client.disconnect();
    }
    
    // The client's 'close' event will fire, but we've already reset.
    // Now, immediately try to establish a new connection.
    client.connect().catch(() => {
        logMessage('Failed to connect to the server.', 'error');
    });
});

startSessionButton.disabled = true;
micButton.disabled = true;
logMessage('Connecting to server...', 'status');
client.connect().catch(() => {
    logMessage('Failed to connect to the server.', 'error');
});
