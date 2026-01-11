import os
import asyncio
import pyaudio
import base64
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv


class RealtimeAudioDemo:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-realtime")
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not found")
        self.credential = DefaultAzureCredential()
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.rate = 24000  # 24kHz for GPT-4o Realtime
        self.chunk = 1024
        self.format = pyaudio.paInt16
    
    async def send_audio(self, connection, stream):
        """Send audio from microphone to the model."""
        try:
            print("🎤 Listening... (Speak naturally)")
            while True:
                data = stream.read(self.chunk, exception_on_overflow=False)
                if data:
                    audio_b64 = base64.b64encode(data).decode('utf-8')
                    await connection.input_audio_buffer.append(audio=audio_b64)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
    
    async def receive_audio(self, connection, stream):
        """Receive audio responses and events from the model."""
        try:
            async for event in connection:
                if event.type == "response.audio.delta":
                    audio_data = base64.b64decode(event.delta)
                    stream.write(audio_data)
                elif event.type == "conversation.item.input_audio_transcription.completed":
                    print(f"\n👤 You: {event.transcript}")
                elif event.type == "response.output_audio_transcript.delta":
                    print(event.delta, end="", flush=True)
                elif event.type == "response.output_audio_transcript.done":
                    print()
                elif event.type == "input_audio_buffer.speech_started":
                    print("🎤 Speech detected...")
                elif event.type == "input_audio_buffer.speech_stopped":
                    print("🎤 Processing...")
                elif event.type == "response.done":
                    print("✅ Response complete\n")
                elif event.type == "error":
                    print(f"\n❌ Error: {event.error.message}")
        except asyncio.CancelledError:
            pass
    
    async def run(self):
        """Run the audio demo."""
        print("=" * 60)
        print("GPT-4o Realtime API - Audio Mode")
        print("=" * 60)
        print("🎤 Speak into your microphone")
        print("⌨️  Press Ctrl+C to exit\n")
        
        # Get auth token
        token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )
        token = token_provider()
        base_url = self.endpoint.replace("https://", "wss://").rstrip("/") + "/openai/v1"
        
        client = AsyncOpenAI(websocket_base_url=base_url, api_key=token)
        
        print("🔌 Connecting...")
        
        try:
            async with client.realtime.connect(model=self.deployment) as connection:
                # Configure session for audio
                await connection.session.update(session={
                    "type": "realtime",
                    "instructions": "You are a helpful assistant. Keep responses brief and conversational.",
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "transcription": {
                                "model": "whisper-1",
                            },
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000,
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                                "prefix_padding_ms": 300,
                                "silence_duration_ms": 500,
                                "create_response": True,
                            }
                        },
                        "output": {
                            "voice": "alloy",
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000,
                            }
                        }
                    }
                })
                
                print("✅ Connected!\n")
                
                # Open audio streams
                input_stream = self.audio.open(
                    format=self.format,
                    channels=1,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                
                output_stream = self.audio.open(
                    format=self.format,
                    channels=1,
                    rate=self.rate,
                    output=True,
                    frames_per_buffer=self.chunk
                )
                
                # Run send and receive tasks concurrently
                send_task = asyncio.create_task(self.send_audio(connection, input_stream))
                receive_task = asyncio.create_task(self.receive_audio(connection, output_stream))
                
                await asyncio.gather(send_task, receive_task)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        finally:
            try:
                input_stream.stop_stream()
                input_stream.close()
                output_stream.stop_stream()
                output_stream.close()
            except:
                pass
            self.audio.terminate()
            self.credential.close()


async def main():
    demo = RealtimeAudioDemo()
    await demo.run()


if __name__ == "__main__":
    print("\n🚀 Starting Azure OpenAI Realtime Audio Demo...\n")
    asyncio.run(main())
