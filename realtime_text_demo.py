import os
import asyncio
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv


class RealtimeTextDemo:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-realtime")
        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not found")
        self.credential = DefaultAzureCredential()
    
    async def chat(self):
        print("=" * 60)
        print("GPT-4o Realtime API - Text Mode")
        print("=" * 60)
        print("Type your messages and press Enter")
        print("Type 'quit' to exit\n")
        
        token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )
        token = token_provider()
        base_url = self.endpoint.replace("https://", "wss://").rstrip("/") + "/openai/v1"
        
        client = AsyncOpenAI(websocket_base_url=base_url, api_key=token)
        
        print("🔌 Connecting...")
        async with client.realtime.connect(model=self.deployment) as connection:
            await connection.session.update(session={
                "type": "realtime",
                "instructions": "You are a helpful assistant.",
                "output_modalities": ["text"]
            })
            
            print("✅ Connected!\n")
            
            while True:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "💬 You: ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                if not user_input.strip():
                    continue
                
                await connection.conversation.item.create(
                    item={"type": "message", "role": "user", 
                          "content": [{"type": "input_text", "text": user_input}]}
                )
                await connection.response.create()
                
                print("🤖 Assistant: ", end="", flush=True)
                async for event in connection:
                    if event.type == "response.output_text.delta":
                        print(event.delta, end="", flush=True)
                    elif event.type == "response.output_audio_transcript.delta":
                        print(event.delta, end="", flush=True)
                    elif event.type == "response.text.delta":
                        print(event.delta, end="", flush=True)
                    elif event.type == "response.output_text.done":
                        print()
                    elif event.type == "response.text.done":
                        print()
                    elif event.type == "response.done":
                        print("\n")
                        break
                    elif event.type == "error":
                        print(f"\n❌ Error: {event.error.message}")
                        break


async def main():
    demo = RealtimeTextDemo()
    await demo.chat()


if __name__ == "__main__":
    print("\n🚀 Starting Azure OpenAI Realtime Text Demo...\n")
    asyncio.run(main())
