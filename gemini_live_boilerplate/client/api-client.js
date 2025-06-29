class EventEmitter {
    constructor() {
        this.events = {};
    }

    on(eventName, listener) {
        if (!this.events[eventName]) {
            this.events[eventName] = [];
        }
        this.events[eventName].push(listener);
    }

    emit(eventName, ...args) {
        if (this.events[eventName]) {
            this.events[eventName].forEach(listener => listener(...args));
        }
    }
}

// ApiClient - Event-driven WebSocket client for multimodal live service.
export class ApiClient extends EventEmitter {
    constructor(url) {
        super();
        this.url = url;
        this.ws = null;
        this.explicitlyClosed = false;
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    connect() {
        return new Promise((resolve, reject) => {
            if (this.isConnected()) {
                console.log('[ApiClient] Already connected.');
                return resolve();
            }

            this.emit('status', 'connecting');
            this.explicitlyClosed = false;
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[ApiClient] WebSocket connection established.');
                this.emit('status', 'connected');
                this.emit('open');
                resolve();
            };

            this.ws.onmessage = this._handleMessage.bind(this);

            this.ws.onclose = (event) => {
                console.log(`[ApiClient] WebSocket closed. Code: ${event.code}, Reason: "${event.reason}"`);
                const wasConnected = !!this.ws;
                this.ws = null;
                if (!this.explicitlyClosed && wasConnected) {
                    this.emit('status', 'disconnected_unexpectedly', { code: event.code, reason: event.reason });
                } else {
                    this.emit('status', 'disconnected');
                }
                this.emit('close', event);
            };

            this.ws.onerror = (error) => {
                console.error('[ApiClient] WebSocket error:', error);
                this.emit('error', error);
                reject(error);
            };
        });
    }

    disconnect() {
        if (!this.ws) return;
        console.log('[ApiClient] Disconnecting explicitly.');
        this.explicitlyClosed = true;
        this.ws.close(1000, 'Client initiated disconnect');
    }

    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            // TODO: log only some info or just event
            console.log('[SERVER -> CLIENT]', message);

            // Emit a generic 'message' event and a specific event type
            this.emit('message', message);

            if (message.event) {
                this.emit(message.event, message.data);
            } else {
                console.warn('[ApiClient] Received message without a event:', message);
            }

        } catch (err) {
            console.error('[ApiClient] Error parsing message:', err);
            this.emit('error', new Error('Failed to parse server message.'));
        }
    }

    _send(payload) {
        if (!this.isConnected()) {
            console.error('[ApiClient] Cannot send message, WebSocket is not open.', payload);
            return;
        }
        this.ws.send(JSON.stringify(payload));
    }

    // --- Public Methods to Send Data ---

    sendStartSession() {
        console.log('[ApiClient] Sending start session signal.');
        this._send({ event: 'start_session' });
    }

    sendAudio(arrayBuffer) {
        // Convert raw audio data to Base64 and send
        let binary = "";
        const bytes = new Uint8Array(arrayBuffer);
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        const base64Audio = window.btoa(binary);
        
        this._send({ event: 'audio_chunk', data: base64Audio });
    }

    sendEndOfSession() {
        console.log('[ApiClient] Sending end session signal.');
        this._send({ event: 'end_session' });
    }
    // For manual interruption
    // sendInterrupt() {
    //     console.log('[ApiClient] Sending interrupt signal.');
    //     this._send({ event: 'interrupt' });
    // }
    
}