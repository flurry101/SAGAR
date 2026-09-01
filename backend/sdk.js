/**
 * AI Voice Gateway Browser SDK
 *
 * A JavaScript library for integrating browser-based voice assistant
 * functionality with the AI Voice Gateway server.
 *
 * Usage:
 *   const voice = new AIVoiceGateway({
 *       serverUrl: 'wss://voice.example.com:8082',
 *       language: 'en-IN',
 *       onTranscript: (text) => console.log('User said:', text),
 *       onResponse: (text) => console.log('AI said:', text),
 *       onAudio: (audioData) => playAudio(audioData),
 *       onStatus: (status) => updateUI(status),
 *       onError: (error) => handleError(error)
 *   });
 *
 *   await voice.connect();
 *   voice.startListening();
 *
 * @version 1.0.11
 * @author AI Voice Gateway
 */

(function(global) {
    'use strict';

    // Audio magic bytes for identifying audio messages
    const AUDIO_MAGIC = 'AIVGPCM';

    /**
     * AI Voice Gateway Client
     */
    class AIVoiceGateway {
        /**
         * Create a new AIVoiceGateway instance
         * @param {Object} options - Configuration options
         * @param {string} options.serverUrl - WebSocket server URL (required)
         * @param {string} [options.language='en-IN'] - Language code
         * @param {string} [options.apiKey] - API key for authentication
         * @param {Object} [options.metadata] - Custom metadata to send with session
         * @param {Function} [options.onConnect] - Called when connected
         * @param {Function} [options.onDisconnect] - Called when disconnected
         * @param {Function} [options.onTranscript] - Called with user speech transcript
         * @param {Function} [options.onResponse] - Called with the full AI response text (once per turn)
         * @param {Function} [options.onResponseDelta] - Called with each streamed text fragment as the model writes (server LITEBOT_STREAMING); accumulate for word-by-word rendering. onResponse still fires with the full text.
         * @param {Function} [options.onAudio] - Called with audio data to play
         * @param {Function} [options.onStatus] - Called with status updates
         * @param {Function} [options.onError] - Called on errors
         * @param {Function} [options.onHangup] - Called when AI ends the call
         * @param {Function} [options.onTransfer] - Called when the AI asks for a human agent ({ reason }); the widget decides how to hand off
         * @param {boolean} [options.autoGreet=false] - Auto-send greeting to LLM on connect (AI speaks first)
         * @param {string} [options.greetingMessage='hi'] - Message to send for auto-greeting
         * @param {string} [options.ttsProvider] - TTS provider override (sarvam, google, gemini, elevenlabs, deepgram, azure, murf, vexyl, smallest)
         * @param {number} [options.keepAliveMs=30000] - Interval for keep-alive pings (0 disables). Keeps proxies/tunnels from dropping quiet sockets; the server does not treat pings as session activity.
         */
        constructor(options = {}) {
            if (!options.serverUrl) {
                throw new Error('serverUrl is required');
            }

            this.serverUrl = options.serverUrl;
            this.language = options.language || 'en-IN';
            this.apiKey = options.apiKey || null;
            this._checkTransportSecurity();
            this.metadata = options.metadata || {};
            this.ttsProvider = options.ttsProvider || null;
            this._warnReservedMetadata(this.metadata);

            // Auto-greeting options
            this.autoGreet = options.autoGreet || false;
            this.greetingMessage = options.greetingMessage || 'hi';

            // Callbacks
            this.onConnect = options.onConnect || (() => {});
            this.onDisconnect = options.onDisconnect || (() => {});
            this.onTranscript = options.onTranscript || (() => {});
            this.onResponse = options.onResponse || (() => {});
            this.onResponseDelta = options.onResponseDelta || (() => {});
            this.onAudio = options.onAudio || (() => {});
            this.onStatus = options.onStatus || (() => {});
            this.onError = options.onError || (() => {});
            this.onHangup = options.onHangup || (() => {});
            this.onTransfer = options.onTransfer || (() => {});

            // Internal state
            this.ws = null;
            this.mediaRecorder = null;
            this.audioStream = null;
            this.audioContext = null;
            this.isConnected = false;
            this.isListening = false;
            this.isMuted = false;
            this.uuid = null;

            // Audio playback. Frames are scheduled back-to-back on the
            // AudioContext clock (gapless) instead of chained on onended —
            // the server sends one frame per sentence while streaming, and
            // onended-chaining leaves an audible seam between them.
            this.audioQueue = [];            // buffers not yet scheduled
            this.isPlaying = false;
            this.currentSource = null;       // most recently scheduled source (compat)
            this._activeSources = new Set(); // scheduled, not yet ended
            this._nextPlayTime = 0;          // AudioContext time the next buffer starts
            this.isSpeakingSession = false;  // Track entire speaking session for visualization
            this._responseBuffer = '';       // accumulated response_delta text for the current turn
            this._audioCompleteSeen = false; // server sent audio_complete for the current turn
            this._audioSinceComplete = false;// audio frames received since the last audio_complete

            // Audio analyser for visualization
            this.analyserNode = null;
            this.gainNode = null;

            // Keep-alive
            this.keepAliveMs = options.keepAliveMs === undefined ? 30000 : options.keepAliveMs;
            this._keepAliveTimer = null;

            // Reconnection
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
            this.reconnectDelay = options.reconnectDelay || 1000;
            this.autoReconnect = options.autoReconnect !== false;
        }

        /**
         * Connect to the WebSocket server
         * @returns {Promise<void>}
         */
        async connect() {
            return new Promise((resolve, reject) => {
                try {
                    // Build URL with query params
                    let url = this.serverUrl;
                    const params = new URLSearchParams();

                    if (this.apiKey) {
                        params.set('apiKey', this.apiKey);
                    }
                    if (this.language) {
                        params.set('language', this.language);
                    }

                    const queryString = params.toString();
                    if (queryString) {
                        url += (url.includes('?') ? '&' : '?') + queryString;
                    }

                    this.ws = new WebSocket(url);
                    this.ws.binaryType = 'arraybuffer';

                    this.ws.onopen = () => {
                        console.log('[AIVG] Connected to server');
                        this.isConnected = true;
                        this.reconnectAttempts = 0;
                        this._startKeepAlive();
                        resolve();
                    };

                    this.ws.onmessage = (event) => {
                        this._handleMessage(event.data);
                    };

                    this.ws.onerror = (error) => {
                        console.error('[AIVG] WebSocket error:', error);
                        this.onError({ code: 'WS_ERROR', message: 'WebSocket error' });
                    };

                    this.ws.onclose = (event) => {
                        console.log('[AIVG] Disconnected:', event.code, event.reason);
                        this.isConnected = false;
                        this.isListening = false;
                        this.uuid = null;
                        this._stopKeepAlive();

                        this.onDisconnect({ code: event.code, reason: event.reason });

                        // Don't reconnect on certain close codes:
                        // 4001: Invalid API key (permanent error)
                        // 4003: Call limit reached (should wait, not spam reconnects)
                        // 4008: Server idle timeout (reconnecting would idle again)
                        // 4009: Server max session duration reached
                        // 1000: Normal closure (intentional disconnect)
                        const noReconnectCodes = [1000, 4001, 4003, 4008, 4009];
                        if (noReconnectCodes.includes(event.code)) {
                            console.log('[AIVG] Not reconnecting due to close code:', event.code);
                            return;
                        }

                        // Auto reconnect for transient errors
                        if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                            this.reconnectAttempts++;
                            const delay = this.reconnectDelay * this.reconnectAttempts;
                            console.log(`[AIVG] Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`);
                            setTimeout(() => this.connect().catch(() => {}), delay);
                        }
                    };

                    // Timeout
                    setTimeout(() => {
                        if (!this.isConnected) {
                            this.ws.close();
                            reject(new Error('Connection timeout'));
                        }
                    }, 10000);

                } catch (error) {
                    reject(error);
                }
            });
        }

        /**
         * Disconnect from the server
         */
        disconnect() {
            this.autoReconnect = false;
            this._stopKeepAlive();
            this.stopListening();

            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
        }

        /**
         * Start listening for user speech
         * @returns {Promise<void>}
         */
        async startListening() {
            if (!this.isConnected) {
                throw new Error('Not connected');
            }

            if (this.isListening) {
                return;
            }

            try {
                // Request microphone access
                this.audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // Initialize AudioContext for playback
                if (!this.audioContext) {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                        sampleRate: 8000
                    });
                }

                // Send start message FIRST so server is ready
                const startMessage = {
                    type: 'start',
                    language: this.language,
                    metadata: this.metadata
                };
                if (this.ttsProvider) {
                    startMessage.tts_provider = this.ttsProvider;
                }
                this._send(startMessage);

                // Small delay to ensure server processes start message
                await new Promise(resolve => setTimeout(resolve, 100));

                // Create MediaRecorder
                const mimeType = this._getSupportedMimeType();
                console.log('[AIVG] Using audio format:', mimeType);

                this.mediaRecorder = new MediaRecorder(this.audioStream, {
                    mimeType: mimeType,
                    audioBitsPerSecond: 64000
                });

                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0 && this.isConnected && !this.isMuted) {
                        this.ws.send(event.data);
                    }
                };

                this.mediaRecorder.onerror = (error) => {
                    console.error('[AIVG] MediaRecorder error:', error);
                    this.onError({ code: 'RECORDER_ERROR', message: 'Recording error' });
                };

                // Start recording with timeslice for streaming
                this.mediaRecorder.start(100); // Send chunks every 100ms

                this.isListening = true;
                console.log('[AIVG] Started listening');

            } catch (error) {
                console.error('[AIVG] Failed to start listening:', error);
                this.onError({ code: 'MIC_ERROR', message: error.message });
                throw error;
            }
        }

        /**
         * Stop listening for user speech
         */
        stopListening() {
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }

            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }

            this.isListening = false;

            if (this.isConnected) {
                this._send({ type: 'stop' });
            }

            console.log('[AIVG] Stopped listening');
        }

        /**
         * Mute the microphone
         */
        mute() {
            this.isMuted = true;
            if (this.isConnected) {
                this._send({ type: 'mute' });
            }
        }

        /**
         * Unmute the microphone
         */
        unmute() {
            this.isMuted = false;
            if (this.isConnected) {
                this._send({ type: 'unmute' });
            }
        }

        /**
         * Stop audio playback (used for barge-in)
         * Clears the audio queue and stops currently playing audio
         */
        stopPlayback() {
            // Clear the audio queue
            this.audioQueue = [];

            // Stop every scheduled source (current + queued-ahead)
            for (const src of this._activeSources) {
                try {
                    src.onended = null;
                    src.stop();
                } catch (e) {
                    // Ignore errors if source already stopped
                }
            }
            this._activeSources.clear();
            this.currentSource = null;
            this._nextPlayTime = 0;

            // Reset playback state
            this.isPlaying = false;
            this.isSpeakingSession = false;
            this._audioCompleteSeen = false;
            this._audioSinceComplete = false;

            console.log('[AIVG] Playback stopped (barge-in)');
        }

        /**
         * Set the language
         * @param {string} language - Language code (e.g., 'en-IN', 'hi-IN')
         */
        setLanguage(language) {
            this.language = language;
            if (this.isConnected) {
                this._send({ type: 'config', language: language });
            }
        }

        /**
         * Set the TTS provider
         * @param {string} provider - TTS provider (sarvam, google, gemini, elevenlabs, deepgram, azure, murf, vexyl, smallest)
         */
        setTTSProvider(provider) {
            const validProviders = ['sarvam', 'google', 'gemini', 'elevenlabs', 'deepgram', 'azure', 'murf', 'vexyl', 'smallest'];
            if (!validProviders.includes(provider)) {
                console.warn(`[AIVG] Invalid TTS provider: ${provider}. Valid: ${validProviders.join(', ')}`);
                return;
            }
            this.ttsProvider = provider;
            if (this.isConnected) {
                this._send({ type: 'config', tts_provider: provider });
            }
        }

        /**
         * Send metadata and TTS provider to the server as one config message.
         * Safe to repeat — the server merges metadata and ignores absent fields.
         * @private
         */
        _sendSessionConfig() {
            // Language is deliberately omitted: it already travelled on the
            // connect query string, and a 'config' with language makes the
            // server re-run initializeSTT() and open a second Sarvam socket.
            const config = { type: 'config' };
            if (this.metadata && Object.keys(this.metadata).length > 0) {
                config.metadata = this.metadata;
            }
            if (this.ttsProvider) {
                config.tts_provider = this.ttsProvider;
            }
            this._send(config);
        }

        /**
         * Update metadata
         * @param {Object} metadata - Metadata to add/update
         */
        updateMetadata(metadata) {
            this._warnReservedMetadata(metadata);
            this.metadata = { ...this.metadata, ...metadata };
            if (this.isConnected) {
                this._send({ type: 'config', metadata: this.metadata });
            }
        }

        /**
         * Get current status
         * @returns {Object} Status object
         */
        getStatus() {
            return {
                isConnected: this.isConnected,
                isListening: this.isListening,
                isMuted: this.isMuted,
                uuid: this.uuid,
                language: this.language,
                ttsProvider: this.ttsProvider
            };
        }

        /**
         * Handle incoming message
         * @private
         */
        _handleMessage(data) {
            // Check if binary audio data
            if (data instanceof ArrayBuffer) {
                this._handleAudioData(data);
                return;
            }

            // JSON message
            try {
                const message = JSON.parse(data);
                this._handleJsonMessage(message);
            } catch (error) {
                console.error('[AIVG] Invalid message:', error);
            }
        }

        /**
         * Handle JSON message
         * @private
         */
        _handleJsonMessage(message) {
            switch (message.type) {
                case 'connected':
                    this.uuid = message.uuid;
                    this.onConnect({ uuid: this.uuid });

                    // Push session config before anything can trigger the LLM.
                    // The server session is created with empty metadata and only
                    // learns about botId / ttsProvider from 'start', which is not
                    // sent until startListening(). An auto-greeting fires before
                    // that, so without this the first turn ran on the default bot
                    // and the default TTS voice.
                    this._sendSessionConfig();

                    // Send auto-greeting if enabled (AI speaks first)
                    if (this.autoGreet) {
                        console.log('[AIVG] Sending auto-greeting:', this.greetingMessage);
                        this._send({
                            type: 'greeting',
                            text: this.greetingMessage
                        });
                    }
                    break;

                case 'transcript':
                    this.onTranscript(message.text, { isFinal: message.isFinal });
                    break;

                case 'response_delta':
                    // Streamed text fragment (server sentence-streaming). Full
                    // text follows in 'response'.
                    this._responseBuffer += message.text || '';
                    this.onResponseDelta(message.text || '', this._responseBuffer);
                    break;

                case 'response':
                    this._responseBuffer = '';
                    this.onResponse(message.text);
                    break;

                case 'status':
                    // Note: Don't reset isSpeakingSession here - audio may still be playing
                    // It will be reset when audio playback actually finishes
                    this.onStatus(message.status);
                    break;

                case 'error':
                    this.onError({ code: message.code, message: message.message });
                    break;

                case 'audio_complete':
                    // Server has sent the last audio frame of this turn. While
                    // streaming, frames arrive per sentence with gaps — the queue
                    // can drain between them — so playback-complete is reported
                    // only once this has been seen AND everything has played.
                    this._audioCompleteSeen = true;
                    if (!this.isPlaying && this.audioQueue.length === 0) {
                        this._reportPlaybackComplete();
                    }
                    break;

                case 'stop_playback':
                    // Barge-in: server detected user speech, stop TTS playback immediately
                    console.log('[AIVG] Barge-in: stopping playback');
                    this.stopPlayback();
                    break;

                case 'pong':
                    // Ping response
                    break;

                case 'closed':
                    // Server-initiated close (idle timeout, max session, shutdown).
                    // The socket close follows; surface it as a status update.
                    console.log('[AIVG] Server closing connection:', message.code || '', message.reason || '');
                    this.onStatus('closing');
                    break;

                case 'transfer':
                    // Assistant requested a human hand-off. No SIP leg exists on
                    // the browser path; surface it and keep the session alive.
                    console.log('[AIVG] Transfer requested by assistant:', message.reason);
                    this.onTransfer({ reason: message.reason, timestamp: message.timestamp });
                    this.onStatus('transfer');
                    break;

                case 'hangup':
                    console.log('[AIVG] Call ended by assistant:', message.reason);
                    // Disable auto-reconnect since this is an intentional end
                    this.autoReconnect = false;
                    // Stop listening if active
                    this.stopListening();
                    // Notify via onHangup callback if defined
                    if (this.onHangup) {
                        this.onHangup({ reason: message.reason });
                    }
                    // Also send status update
                    this.onStatus('ended');
                    // Close the connection cleanly
                    if (this.ws) {
                        this.ws.close(1000, 'Call ended by assistant');
                    }
                    break;

                default:
                    console.log('[AIVG] Unknown message type:', message.type);
            }
        }

        /**
         * Handle binary audio data
         * @private
         */
        _handleAudioData(arrayBuffer) {
            // Header: 'AIVGPCM' (7) + version (1) [+ sampleRate uint32 LE (4) for v2]
            if (!(arrayBuffer instanceof ArrayBuffer) || arrayBuffer.byteLength < 8) {
                console.warn('[AIVG] Ignoring short binary frame');
                return;
            }
            const dataView = new DataView(arrayBuffer);

            // Check for magic bytes 'AIVGPCM'
            let magic = '';
            for (let i = 0; i < 7; i++) {
                magic += String.fromCharCode(dataView.getUint8(i));
            }

            if (magic !== AUDIO_MAGIC) {
                // Unknown binary format
                console.warn('[AIVG] Unknown binary data format');
                return;
            }

            // Mark speaking session active for visualization
            this.isSpeakingSession = true;
            this._audioSinceComplete = true;
            this._audioCompleteSeen = false;

            // Check version byte to determine header format
            const version = dataView.getUint8(7);
            let pcmData;
            let sampleRate = 24000; // Default

            if (version === 0x02) {
                // Version 2: 12-byte header with sample rate
                // Bytes 8-11: Sample rate (uint32 LE)
                if (arrayBuffer.byteLength < 12) {
                    console.warn('[AIVG] Ignoring truncated v2 audio header');
                    return;
                }
                const declared = dataView.getUint32(8, true); // true = little-endian
                // Web Audio rejects rates outside ~8k-96k; a bad header must not
                // throw inside the async playback path and stall the queue.
                if (declared >= 8000 && declared <= 96000) {
                    sampleRate = declared;
                } else {
                    console.warn(`[AIVG] Implausible sample rate ${declared}Hz in audio header, using ${sampleRate}Hz`);
                }
                pcmData = arrayBuffer.slice(12);
                if ((this._audioFrameLogs = (this._audioFrameLogs || 0) + 1) <= 3) {
                    console.log(`[AIVG] Audio v2: ${pcmData.byteLength} bytes at ${sampleRate}Hz`);
                }
            } else {
                // Version 1: 8-byte header (legacy)
                pcmData = arrayBuffer.slice(8);
                console.log(`[AIVG] Audio v1: ${pcmData.byteLength} bytes at ${sampleRate}Hz (default)`);
            }

            if (pcmData.byteLength < 2) {
                return; // header only, nothing to play
            }
            // Int16 view needs an even byte length; drop a trailing odd byte.
            if (pcmData.byteLength % 2 !== 0) {
                pcmData = pcmData.slice(0, pcmData.byteLength - 1);
            }

            this._playAudio(pcmData, sampleRate).catch((error) => {
                console.error('[AIVG] Audio playback error:', error);
                this.onError({ code: 'PLAYBACK_ERROR', message: error && error.message ? error.message : 'Audio playback failed' });
            });
            this.onAudio(pcmData);
        }

        /**
         * Play PCM audio data
         * @private
         * @param {ArrayBuffer} pcmArrayBuffer - PCM audio data
         * @param {number} sampleRate - Sample rate in Hz
         */
        async _playAudio(pcmArrayBuffer, sampleRate = 24000) {
            // Use device's native sample rate for best quality
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                console.log(`[AIVG] AudioContext created, device sample rate: ${this.audioContext.sampleRate}Hz`);
            }

            // Resume audio context if suspended (browser autoplay policy)
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }

            // Convert Int16 PCM to Float32 for Web Audio API
            const int16Array = new Int16Array(pcmArrayBuffer);
            const float32Array = new Float32Array(int16Array.length);

            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / 32768.0;
            }

            // Calculate expected duration
            const expectedDuration = float32Array.length / sampleRate;
            if (this._audioFrameLogs <= 3) {
                console.log(`[AIVG] Creating audio buffer: ${float32Array.length} samples at ${sampleRate}Hz = ${expectedDuration.toFixed(2)}s`);
            }

            // Create audio buffer at source sample rate (provided by server)
            const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, sampleRate);
            audioBuffer.getChannelData(0).set(float32Array);

            if (this._audioFrameLogs <= 3) {
                console.log(`[AIVG] Audio buffer created: duration=${audioBuffer.duration.toFixed(2)}s, sampleRate=${audioBuffer.sampleRate}Hz`);
            }

            // Queue and schedule on the audio clock
            this.audioQueue.push(audioBuffer);
            this._processAudioQueue();
        }

        /**
         * Process audio playback queue
         * @private
         */
        _processAudioQueue() {
            // Create analyser and gain nodes if not exists
            if (!this.analyserNode) {
                this.analyserNode = this.audioContext.createAnalyser();
                this.analyserNode.fftSize = 256;
                this.gainNode = this.audioContext.createGain();
                this.gainNode.connect(this.audioContext.destination);
                this.analyserNode.connect(this.gainNode);
            }

            // Schedule everything queued, back-to-back on the context clock.
            while (this.audioQueue.length > 0) {
                const audioBuffer = this.audioQueue.shift();
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.analyserNode);

                const now = this.audioContext.currentTime;
                // Small lead on a cold start so the first frame isn't scheduled in the past.
                const startAt = Math.max(now + 0.005, this._nextPlayTime || 0);
                this._nextPlayTime = startAt + audioBuffer.duration;

                this._activeSources.add(source);
                this.currentSource = source;
                this.isPlaying = true;

                source.onended = () => {
                    this._activeSources.delete(source);
                    if (this._activeSources.size === 0 && this.audioQueue.length === 0) {
                        this._onPlaybackDrained();
                    }
                };
                source.start(startAt);
            }
        }

        /**
         * All scheduled audio has finished and nothing is queued.
         * @private
         */
        _onPlaybackDrained() {
            this.isPlaying = false;
            this.currentSource = null;
            this._nextPlayTime = 0;
            // Between sentence frames of a streamed turn the queue runs dry
            // while the server is still synthesising the next sentence. Keep
            // the "speaking" state and don't tell the server we're done until
            // it has sent audio_complete.
            if (this._audioCompleteSeen || !this._audioSinceComplete) {
                this._reportPlaybackComplete();
            }
        }

        /**
         * Turn's audio fully played: reset speaking state, notify server once.
         * @private
         */
        _reportPlaybackComplete() {
            this._audioFrameLogs = 0;
            this.isSpeakingSession = false;  // Reset when all audio finished playing
            this._audioCompleteSeen = false;
            this._audioSinceComplete = false;

            // Notify server that audio playback is complete
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'audio_playback_complete'
                }));
                console.log('[AIVG] Audio playback complete, notified server');
            }
        }

        /**
         * Get the analyser node for audio visualization
         * @returns {AnalyserNode|null}
         */
        getAnalyser() {
            return this.analyserNode;
        }

        /**
         * Get frequency data for visualization
         * @returns {Uint8Array|null}
         */
        getFrequencyData() {
            if (!this.analyserNode || !this.isSpeakingSession) return null;
            const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
            this.analyserNode.getByteFrequencyData(dataArray);
            return dataArray;
        }

        /**
         * Check if audio is currently playing
         * @returns {boolean}
         */
        isAudioPlaying() {
            return this.isPlaying;
        }

        /**
         * Warn about transport choices that leak the key or cannot work.
         * - ws:// from an https page is blocked by browsers (mixed content).
         * - ws:// to a non-local host sends the apiKey (query string) in
         *   plaintext; use wss://.
         * @private
         */
        _checkTransportSecurity() {
            let u;
            try { u = new URL(this.serverUrl); } catch (e) { return; }
            const local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(u.hostname);
            const pageHttps = typeof location !== 'undefined' && location.protocol === 'https:';
            if (u.protocol === 'ws:' && pageHttps && !local) {
                console.warn('[AIVG] serverUrl uses ws:// on an https page — browsers block mixed-content WebSockets. Use wss://.');
            }
            if (u.protocol === 'ws:' && !local && this.apiKey) {
                console.warn('[AIVG] apiKey is sent on a plaintext ws:// connection. Use wss:// so the key is not readable in transit.');
            }
        }

        /**
         * Keys the server strips from metadata (identity is server-owned).
         * @private
         */
        _warnReservedMetadata(metadata) {
            if (!metadata || typeof metadata !== 'object') return;
            const reserved = ['userId', 'user_id', 'sessionId', 'session_id', 'uuid', 'apiKey', 'api_key'];
            const hit = Object.keys(metadata).filter(k => reserved.includes(k));
            if (hit.length) {
                console.warn(`[AIVG] metadata keys ignored by server (reserved): ${hit.join(', ')}. Pass userId via the constructor/query string instead.`);
            }
        }

        /** @private */
        _startKeepAlive() {
            this._stopKeepAlive();
            if (!this.keepAliveMs || this.keepAliveMs <= 0) return;
            this._keepAliveTimer = setInterval(() => this.ping(), this.keepAliveMs);
        }

        /** @private */
        _stopKeepAlive() {
            if (this._keepAliveTimer) {
                clearInterval(this._keepAliveTimer);
                this._keepAliveTimer = null;
            }
        }

        /**
         * Send JSON message
         * @private
         */
        _send(message) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify(message));
            }
        }

        /**
         * Get supported MIME type for MediaRecorder
         * @private
         */
        _getSupportedMimeType() {
            const types = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/mp4'
            ];

            for (const type of types) {
                if (MediaRecorder.isTypeSupported(type)) {
                    return type;
                }
            }

            return '';
        }

        /**
         * Ping the server (keep-alive)
         */
        ping() {
            if (this.isConnected) {
                this._send({ type: 'ping' });
            }
        }
    }

    // Export for different module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = AIVoiceGateway;
    } else if (typeof define === 'function' && define.amd) {
        define([], function() { return AIVoiceGateway; });
    } else {
        global.AIVoiceGateway = AIVoiceGateway;
    }

})(typeof window !== 'undefined' ? window : this);
