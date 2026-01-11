"""
Text In Audio Out - Official Microsoft Sample
Based on: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-quickstart
Uses OpenAI Python SDK with Azure OpenAI Realtime API
"""

import os
import base64
import asyncio
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv


async def main() -> None:
    """
    When prompted for user input, type a message and hit enter to send it to the model.
    Enter "q" to quit the conversation.
    """
    
    # Load environment variables
    load_dotenv()
    
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    token = token_provider()

    # The endpoint of your Azure OpenAI resource
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]

    # The deployment name of the model you want to use
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-realtime")

    base_url = endpoint.replace("https://", "wss://").rstrip("/") + "/openai/v1"

    # Create OpenAI client with Azure endpoint
    client = AsyncOpenAI(
        websocket_base_url=base_url,
        api_key=token
    )
    
    async with client.realtime.connect(
        model=deployment_name,
    ) as connection:
        # Configure the session
        await connection.session.update(session={
            "type": "realtime",
            "instructions": "You are a helpful assistant. You respond by voice and text.",
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
                        "silence_duration_ms": 200,
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

        print("\n" + "="*60)
        print("Azure OpenAI Realtime API - Text In Audio Out")
        print("="*60)
        print("Type your message and press Enter to send.")
        print("Type 'q' to quit.\n")

        # Start conversation loop
        while True:
            user_input = input("Enter a message: ")
            if user_input == "q":
                print("Stopping the conversation.")
                break

            await connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_input}],
                }
            )
            await connection.response.create()
            
            async for event in connection:
                if event.type == "response.output_text.delta":
                    print(event.delta, flush=True, end="")
                elif event.type == "session.created":
                    print(f"Session ID: {event.session.id}")
                elif event.type == "response.output_audio.delta":
                    audio_data = base64.b64decode(event.delta)
                    print(f"Received {len(audio_data)} bytes of audio data.")
                elif event.type == "response.output_audio_transcript.delta":
                    print(f"Received text delta: {event.delta}")
                elif event.type == "response.output_text.done":
                    print()
                elif event.type == "error":
                    print("Received an error event.")
                    print(f"Error code: {event.error.code}")
                    print(f"Error Event ID: {event.error.event_id}")
                    print(f"Error message: {event.error.message}")
                elif event.type == "response.done":
                    break

    print("Conversation ended.")
    credential.close()


if __name__ == "__main__":
    print("\n🚀 Starting Azure OpenAI Realtime API Demo...")
    asyncio.run(main())
