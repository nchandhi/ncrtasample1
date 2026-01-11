# Voice-Enabled Foundry Agent with GPT-4o Realtime

A Python script that creates a real-time voice conversation agent using Microsoft Azure AI Foundry and GPT-4o Realtime model.

## Features

- **Real-Time Voice Conversation**: Direct audio streaming to/from GPT-4o Realtime model
- **Voice Activity Detection**: Automatically detects when you start and stop speaking
- **Natural Conversation**: No button presses needed - just speak naturally
- **Low Latency**: Direct audio processing without intermediate text conversion
- **Azure AI Foundry Integration**: Uses Azure AI Foundry project connections

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note for Windows users**: If you encounter issues installing `pyaudio`, you may need to:
- Install it via conda: `conda install pyaudio`
- Or download a precompiled wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your Azure AI Foundry project connection string:

```bash
cp .env.example .env
```

Edit `.env` with your actual Azure AI Foundry project connection string. You can find this in the Azure AI Foundry portal under your project settings.

### 3. Run the Agent

```bash
python voice_foundry_agent.py
```

## Usage

1. Start the script - it connects to GPT-4o Realtime
2. Start speaking naturally - no need to press any buttons
3. The model automatically detects when you finish speaking
4. The agent responds in real-time with voice
5. Press Ctrl+C to exit
How It Works

1. The script creates an Azure AI Foundry agent using the `gpt-4o` model
2. A conversation thread is created to maintain context
3. When you speak, your voice is converted to text
4. The text is sent to the agent as a message in the thread
5. The agent processes the message and responds
6. The response is converted to speech
7. The conversation continues with full context awareness

## Customization

You can customize the agent by modifying the agent creation in `_initialize_agent()`:

```python
self.agent = self.client.agents.create_agent(
    model="gpt-4o",  # Change to your deployed model
    name=self.agent_name,
    instructions="Your custom instructions here"
)
```

You can also add tools, functions, or file search capabilities to the agent for more advanced features.nections = self.client.connections.list()
```

## Requirements

- Python 3.8+
- Working microphone
- Azure AI Foundry project with connection string
- Azure authentication (Azure CLI login or service principal)
- Internet connection for speech recognition
