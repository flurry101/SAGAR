export type VoiceState = 'idle' | 'connecting' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VexylClientOptions {
  wsUrl: string;
  onStateChange: (state: VoiceState) => void;
  onError: (error: Error) => void;
}

export class VexylClient {
  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private playQueue: AudioBuffer[] = [];
  private isPlaying = false;
  private sourceNode: AudioBufferSourceNode | null = null;

  constructor(private options: VexylClientOptions) {}

  public async start() {
    try {
      this.options.onStateChange('connecting');
      this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      this.ws = new WebSocket(this.options.wsUrl);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        try {
          this.ws?.send(JSON.stringify({ type: 'start', language: 'en-IN', metadata: {} }));
          this.startRecording();
          this.options.onStateChange('listening');
        } catch (e: any) {
          console.error('[VEXYL] Failed to start recording on socket open:', e);
          this.options.onError(e);
          this.stop();
        }
      };

      this.ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'state') {
              if (msg.state === 'listening' || msg.state === 'processing' || msg.state === 'speaking') {
                this.options.onStateChange(msg.state as VoiceState);
              }
            } else if (msg.type === 'audio' && msg.data) {
               // Decode base64 audio and queue it for playback
               const binaryString = window.atob(msg.data);
               const len = binaryString.length;
               const bytes = new Uint8Array(len);
               for (let i = 0; i < len; i++) {
                   bytes[i] = binaryString.charCodeAt(i);
               }
               
               if (this.audioContext) {
                 const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);
                 this.playQueue.push(audioBuffer);
                 this.processPlayQueue();
               }
            }
          } catch (err) {
            console.error('[VEXYL] Failed to parse message:', err);
          }
        }
      };

      this.ws.onerror = (e) => {
        console.error('[VEXYL] WebSocket error', e);
        this.options.onError(new Error("WebSocket error"));
        this.stop();
      };
      
      this.ws.onclose = () => {
        this.stop();
        this.options.onStateChange('idle');
      };

    } catch (e: any) {
      console.error('[VEXYL] Start failed:', e);
      this.options.onError(e);
      this.stop();
    }
  }

  private _getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus', 
        'audio/webm', 
        'audio/ogg;codecs=opus', 
        'audio/mp4'
    ];
    for (const type of types) {
       if (MediaRecorder.isTypeSupported(type)) return type;
    }
    return undefined;
  }

  private startRecording() {
    if (!this.audioStream) return;
    const mimeType = this._getSupportedMimeType();
    
    const options: MediaRecorderOptions = { audioBitsPerSecond: 64000 };
    if (mimeType) {
      options.mimeType = mimeType;
    }
    
    this.mediaRecorder = new MediaRecorder(this.audioStream, options);
    
    this.mediaRecorder.ondataavailable = (event) => {
       if (event.data.size > 0 && this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(event.data);
       }
    };
    
    // Chunk every 100ms
    this.mediaRecorder.start(100);
  }

  private processPlayQueue() {
    if (this.isPlaying || this.playQueue.length === 0 || !this.audioContext) return;
    this.isPlaying = true;
    
    const buffer = this.playQueue.shift()!;
    this.sourceNode = this.audioContext.createBufferSource();
    this.sourceNode.buffer = buffer;
    this.sourceNode.connect(this.audioContext.destination);
    
    this.sourceNode.onended = () => {
      this.isPlaying = false;
      this.processPlayQueue();
    };
    
    this.sourceNode.start(0);
  }

  public stop() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try { this.mediaRecorder.stop(); } catch(e) {}
    }
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
    }
    if (this.sourceNode) {
       try { this.sourceNode.stop(); } catch (e) {}
       this.sourceNode.disconnect();
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
       this.audioContext.close();
    }
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      this.ws.close();
    }
    
    this.ws = null;
    this.audioStream = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.sourceNode = null;
    this.playQueue = [];
    this.isPlaying = false;
  }
}
