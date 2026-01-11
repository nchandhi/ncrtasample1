import { useState, useRef, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
const WEBSOCKET_URL_TEXT = API_URL.replace('http', 'ws') + '/ws/text'
const WEBSOCKET_URL_AUDIO = API_URL.replace('http', 'ws') + '/ws/audio'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [mode, setMode] = useState('text') // 'text' or 'audio'
  const [chatHistory, setChatHistory] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    
    // Auto-save when messages change (after a short delay to batch updates)
    if (messages.length > 0) {
      const timer = setTimeout(() => {
        saveCurrentChat()
      }, 2000) // Save 2 seconds after last message
      return () => clearTimeout(timer)
    }
  }, [messages])

  useEffect(() => {
    loadChatHistory()
  }, [])

  const loadChatHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/chat-history`)
      const data = await response.json()
      setChatHistory(data.history)
    } catch (err) {
      console.error('Failed to load chat history:', err)
    }
  }

  const saveCurrentChat = async () => {
    if (messages.length === 0) return
    
    try {
      // Generate caption using AI
      const captionResponse = await fetch(`${API_URL}/generate-caption`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      })
      const { caption } = await captionResponse.json()
      
      if (currentChatId) {
        // Update existing chat
        await fetch(`${API_URL}/chat-history/${currentChatId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ summary: caption, messages })
        })
      } else {
        // Create new chat
        const response = await fetch(`${API_URL}/chat-history`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ summary: caption, messages })
        })
        const data = await response.json()
        setCurrentChatId(data.id)
      }
      await loadChatHistory()
    } catch (err) {
      console.error('Failed to save chat:', err)
    }
  }

  const startNewChat = async () => {
    if (messages.length > 0) {
      await saveCurrentChat()
    }
    setMessages([])
    setCurrentChatId(null)
  }

  const loadChat = (chat) => {
    setMessages(chat.messages)
    setCurrentChatId(chat.id)
  }

  const deleteChat = async (chatId, e) => {
    e.stopPropagation() // Prevent triggering loadChat
    try {
      await fetch(`${API_URL}/chat-history/${chatId}`, {
        method: 'DELETE'
      })
      await loadChatHistory()
      // If deleted chat was active, start new chat
      if (currentChatId === chatId) {
        setMessages([])
        setCurrentChatId(null)
      }
    } catch (err) {
      console.error('Failed to delete chat:', err)
    }
  }

  const connectWebSocket = (audioMode = false) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const url = audioMode ? WEBSOCKET_URL_AUDIO : WEBSOCKET_URL_TEXT
    const ws = new WebSocket(url)
    
    ws.onopen = () => {
      setIsConnected(true)
      setMode(audioMode ? 'audio' : 'text')
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'text_delta') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant' && !last.complete) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.delta }]
          }
          return [...prev, { role: 'assistant', content: data.delta, complete: false }]
        })
      } else if (data.type === 'audio_delta') {
        playAudioChunk(data.delta)
      } else if (data.type === 'user_transcript') {
        setMessages(prev => [...prev, { role: 'user', content: data.text }])
      } else if (data.type === 'assistant_transcript_delta') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant' && !last.complete) {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.delta }]
          }
          return [...prev, { role: 'assistant', content: data.delta, complete: false }]
        })
      } else if (data.type === 'response_done') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, complete: true }]
          }
          return prev
        })
      }
    }
    
    ws.onclose = () => {
      setIsConnected(false)
    }
    
    wsRef.current = ws
  }

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current || mode === 'audio') return
    
    // Wait for WebSocket to be open
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not ready, waiting...')
      setTimeout(() => sendMessage(), 100)
      return
    }
    
    setMessages(prev => [...prev, { role: 'user', content: input }])
    wsRef.current.send(JSON.stringify({ type: 'message', text: input }))
    setInput('')
  }

  const startRecording = async () => {
    try {
      if (!wsRef.current || mode !== 'audio') {
        connectWebSocket(true)
        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      audioContextRef.current = new AudioContext({ sampleRate: 24000 })
      const source = audioContextRef.current.createMediaStreamSource(stream)
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1)
      
      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        const pcm16 = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768))
        }
        
        const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)))
        wsRef.current.send(JSON.stringify({ type: 'audio', audio: base64 }))
      }
      
      source.connect(processor)
      processor.connect(audioContextRef.current.destination)
      
      mediaRecorderRef.current = { stream, source, processor }
      setIsRecording(true)
    } catch (err) {
      console.error('Recording failed:', err)
      alert('Microphone access denied or not available')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      const { stream, source, processor } = mediaRecorderRef.current
      processor.disconnect()
      source.disconnect()
      stream.getTracks().forEach(track => track.stop())
      mediaRecorderRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    setIsRecording(false)
    
    // Reconnect to text mode
    connectWebSocket(false)
  }

  const playAudioChunk = (base64Audio) => {
    const binary = atob(base64Audio)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    
    const pcm16 = new Int16Array(bytes.buffer)
    const float32 = new Float32Array(pcm16.length)
    for (let i = 0; i < pcm16.length; i++) {
      float32[i] = pcm16[i] / 32768
    }
    
    const audioContext = new AudioContext({ sampleRate: 24000 })
    const buffer = audioContext.createBuffer(1, float32.length, 24000)
    buffer.copyToChannel(float32, 0)
    
    const source = audioContext.createBufferSource()
    source.buffer = buffer
    source.connect(audioContext.destination)
    source.start()
  }

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (wsRef.current) wsRef.current.close()
      stopRecording()
    }
  }, [])

  return (
    <div className="app">
      <div className="chat-container">
        <header className="header">
          <div className="header-content">
            <div className="logo">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <rect width="32" height="32" rx="8" fill="#323130"/>
                <path d="M16 8L20 12L16 16L12 12L16 8Z" fill="white"/>
                <path d="M16 16L20 20L16 24L12 20L16 16Z" fill="white"/>
                <path d="M8 12L12 16L8 20L4 16L8 12Z" fill="white"/>
                <path d="M24 12L28 16L24 20L20 16L24 12Z" fill="white"/>
              </svg>
            </div>
            <h1>Contoso</h1>
          </div>
        </header>
        
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content}
                {msg.role === 'assistant' && (
                  <div className="ai-disclaimer">AI-generated content may be incorrect</div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          <button 
            className="new-chat-button"
            onClick={startNewChat}
            title="Start new chat"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
            </svg>
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message"
            disabled={isRecording}
          />
          <button 
            className={`mic-button ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </button>
          <button onClick={sendMessage} disabled={!input.trim() || isRecording}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
      
      <aside className="sidebar">
        <h2>Chat History</h2>
        <div className="prompts">
          {chatHistory.map((chat) => (
            <div 
              key={chat.id} 
              className={`prompt-item ${currentChatId === chat.id ? 'active' : ''}`}
              onClick={() => loadChat(chat)}
            >
              <span className="chat-summary">{chat.summary}</span>
              <button 
                className="delete-chat-btn"
                onClick={(e) => deleteChat(chat.id, e)}
                title="Delete chat"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}

export default App
