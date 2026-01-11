# Real-Time Chat Application

A full-stack application featuring real-time text and voice chat powered by Azure OpenAI Realtime API.

## Features

- **Real-Time Text Chat**: Streaming text responses with full conversation context
- **Voice Chat**: Direct audio input/output with automatic transcription
- **Chat History**: Auto-saved conversations with AI-generated captions
- **Seamless Mode Switching**: Switch between text and voice mid-conversation
- **Modern UI**: Clean, responsive interface with Contoso branding
- **WebSocket Communication**: Low-latency bidirectional streaming

## Architecture

- **Backend**: FastAPI with WebSocket support (`/api`)
- **Frontend**: React with Vite (`/app`)
- **AI**: Azure OpenAI Realtime API (gpt-realtime) + GPT-4o/GPT-5.1 for captions

---

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Azure OpenAI resource with:
  - Realtime API deployment (gpt-realtime)
  - Chat completions deployment (gpt-4o or gpt-5.1)
- Azure CLI (for authentication) or service principal

### 1. Backend Setup (API)

```bash
# Navigate to API folder
cd api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run the API server
python main.py
```

The API will start on `http://localhost:8001`

**api/.env configuration:**
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-realtime
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-5.1
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
```

### 2. Frontend Setup (App)

```bash
# Navigate to app folder
cd app

# Install dependencies
npm install

# (Optional) Configure environment
copy .env.example .env
# Default API URL is http://localhost:8001

# Run development server
npm run dev
```

The app will start on `http://localhost:5173` (or next available port)

**app/.env configuration (optional):**
```env
VITE_API_URL=http://localhost:8001
```

---

## Usage

### Text Chat
1. Type your message in the input box
2. Press Enter or click Send
3. Receive streaming responses in real-time

### Voice Chat
1. Click the microphone button
2. Speak naturally (voice activity detection enabled)
3. AI responds with voice and text transcription
4. Click microphone again to stop

### Chat History
- Conversations auto-save with AI-generated captions
- Click any chat to load it
- Hover over a chat to see the delete button
- Click "+" to start a new conversation

---

## API Endpoints

### WebSocket Endpoints
- `ws://localhost:8001/ws/text` - Text chat
- `ws://localhost:8001/ws/audio` - Audio chat

### REST Endpoints
- `GET /chat-history` - List all chats
- `POST /chat-history` - Create new chat
- `PUT /chat-history/{id}` - Update chat
- `DELETE /chat-history/{id}` - Delete chat
- `POST /generate-caption` - Generate AI caption

---

## Deployment Notes

### Backend
- Set environment variables in production
- Use production ASGI server (Uvicorn with workers)
- Enable HTTPS for WebSocket security (wss://)
- Update CORS origins to production URLs

### Frontend
- Build for production: `npm run build`
- Set `VITE_API_URL` to production API URL
- Serve static files from `dist/` folder

---

## Project Structure

```
├── api/                    # FastAPI backend
│   ├── main.py            # WebSocket server & routes
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment template
├── app/                   # React frontend
│   ├── src/
│   │   ├── App.jsx       # Main component
│   │   └── App.css       # Styles
│   ├── package.json      # Node dependencies
│   └── .env.example      # Environment template
├── DEMO_SCRIPT.md        # Technical demo script
├── DEMO_SCRIPT_RETAIL.md # Retail demo script
└── README.md             # This file
```

---

## Authentication

The application uses **Azure DefaultAzureCredential** which supports:
- Azure CLI login (`az login`)
- Managed Identity (in Azure)
- Environment variables
- Service Principal

For local development, run `az login` before starting the API.

---

## Troubleshooting

**WebSocket connection fails:**
- Ensure API server is running on port 8001
- Check CORS_ORIGINS includes your frontend URL

**Audio not working:**
- Allow microphone permissions in browser
- Check browser console for errors
- Verify Azure OpenAI Realtime deployment is active

**Chat history not saving:**
- Check API logs for errors
- Verify GPT deployment for caption generation exists

---

## License

MIT License
