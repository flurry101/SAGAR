export type VoiceState = 'idle' | 'connecting' | 'listening' | 'processing' | 'speaking' | 'error';

export interface GroqVoiceClientOptions {
  apiUrl: string;
  onStateChange: (state: VoiceState) => void;
  onError: (error: Error) => void;
  onResponse: (text: string) => void;
}

export class GroqVoiceClient {
  private mediaRecorder: MediaRecorder | null = null;
  private audioStream: MediaStream | null = null;
  private audioChunks: Blob[] = [];

  constructor(private options: GroqVoiceClientOptions) {}

  public async startRecording() {
    try {
      this.options.onStateChange('connecting');
      this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mimeType = this._getSupportedMimeType();
      const options: MediaRecorderOptions = { audioBitsPerSecond: 64000 };
      if (mimeType) {
        options.mimeType = mimeType;
      }
      
      this.mediaRecorder = new MediaRecorder(this.audioStream, options);
      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: mimeType || 'audio/webm' });
        await this.sendAudio(audioBlob);
      };

      this.mediaRecorder.start(100);
      this.options.onStateChange('listening');
    } catch (e: any) {
      console.error('[GROQ_VOICE] Start failed:', e);
      this.options.onError(e instanceof Error ? e : new Error(String(e)));
      this.stopRecording(false);
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

  public async sendAudio(audioBlob: Blob) {
    this.options.onStateChange('processing');
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');
      // Optionally append history or session ID if needed later

      const response = await fetch(this.options.apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const textResponse = data.response;
      
      if (textResponse) {
        this.options.onResponse(textResponse);
      } else {
        this.options.onStateChange('idle');
      }
    } catch (e: any) {
      console.error('[GROQ_VOICE] Send audio failed:', e);
      this.options.onError(e instanceof Error ? e : new Error(String(e)));
      this.options.onStateChange('idle');
    }
  }

  public stopRecording(processAudio: boolean = true) {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      if (!processAudio) {
        this.mediaRecorder.onstop = null; // Prevent sending
      }
      try { this.mediaRecorder.stop(); } catch(e) {}
    }
    if (this.audioStream) {
      this.audioStream.getTracks().forEach(track => track.stop());
    }
    
    this.audioStream = null;
    this.mediaRecorder = null;
    
    if (!processAudio) {
      this.options.onStateChange('idle');
    }
  }
}
