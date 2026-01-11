# Realtime Chat React App

Chat interface for Azure OpenAI Realtime API with text and audio support.

## Setup

1. Install dependencies:
```bash
cd app
npm install
```

2. Start development server:
```bash
npm run dev
```

App runs on `http://localhost:3000`

## Features

- Text chat with real-time streaming responses
- Voice chat with microphone button
- Auto-switches to audio mode when using microphone
- Chat history sidebar with suggested prompts

## Usage

- Type messages and press Enter or click send button
- Click microphone icon to start voice recording (red = recording)
- Click microphone again to stop recording
- AI responses stream in real-time
