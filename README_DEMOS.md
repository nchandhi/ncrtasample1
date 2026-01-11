# GPT-4o Realtime API Demos

Three demonstration scripts showing different ways to use Azure OpenAI's GPT-4o Realtime API.

## Scripts Overview

### 1. `voice_foundry_agent.py` - Full Voice Agent
The complete voice-enabled agent with clean code structure.

**Features:**
- Voice input and output
- Real-time conversation
- Voice Activity Detection (VAD)
- Automatic transcription display

**Usage:**
```bash
python voice_foundry_agent.py
```

### 2. `realtime_demo.py` - Detailed Voice Demo
Shows all the events and stages of the Realtime API in action.

**Features:**
- Detailed event logging
- Shows all API events (speech detection, transcription, response stages)
- Visual indicators for each stage
- Great for understanding how the API works

**Usage:**
```bash
python realtime_demo.py
```

**Sample Output:**
```
🎤 Speech detected...
🎤 Speech ended, processing...
👤 You: What's the weather like today?
🤖 Generating response...
🎵 Audio response incoming...
🎵 Audio playback complete
✓ Response complete
```

### 3. `realtime_text_demo.py` - Text-Only Demo
No microphone needed! Test the Realtime API with text input/output.

**Features:**
- Text-based chat interface
- No audio hardware required
- Great for testing API connectivity
- Shows streaming text responses

**Usage:**
```bash
python realtime_text_demo.py
```

**Sample Interaction:**
```
💬 You: Tell me a joke
🤖 Assistant: Why don't scientists trust atoms? 
Because they make up everything!
```

## Setup

All demos use the same configuration:

1. Set environment variables in `.env`:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-realtime-preview
```

2. Authenticate with Azure:
```bash
az login
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Choosing a Demo

- **Want a production-ready agent?** → `voice_foundry_agent.py`
- **Want to see how it works internally?** → `realtime_demo.py`
- **No microphone or want to test quickly?** → `realtime_text_demo.py`

## Requirements

- Python 3.8+
- Azure OpenAI resource with GPT-4o Realtime deployment
- Azure authentication (via `az login`)
- Microphone (for voice demos only)

## Troubleshooting

**No audio devices found:**
- Check microphone permissions
- Try `realtime_text_demo.py` instead

**Connection errors:**
- Verify `AZURE_OPENAI_ENDPOINT` in `.env`
- Check Azure authentication: `az account show`
- Ensure GPT-4o Realtime is deployed

**Import errors:**
- Run `pip install -r requirements.txt`
- Ensure virtual environment is activated
