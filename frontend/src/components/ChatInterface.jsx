import { useState, useEffect, useRef } from 'react'
import { sendChatMessage, getChatHistory } from '../utils/api'
import { SendHorizontal, Bot, User, Sparkles } from 'lucide-react'
import './ChatInterface.css'

function ChatInterface({ userId }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [loadingHistory, setLoadingHistory] = useState(true)
    const messagesEndRef = useRef(null)

    useEffect(() => {
        loadHistory()
    }, [userId])

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const loadHistory = async () => {
        try {
            const history = await getChatHistory(userId, 20)
            setMessages(history.messages || [])
        } catch (err) {
            console.error('Failed to load history:', err)
        } finally {
            setLoadingHistory(false)
        }
    }

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    const handleSend = async () => {
        if (!input.trim() || loading) return

        const userMessage = input.trim()
        setInput('')

        const tempUserMsg = {
            role: 'user',
            content: userMessage,
            timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, tempUserMsg])

        try {
            setLoading(true)
            const response = await sendChatMessage(userId, userMessage, true)

            const aiMessage = {
                role: 'assistant',
                content: response.message,
                timestamp: new Date().toISOString(),
                context_used: response.context_used
            }
            setMessages(prev => [...prev, aiMessage])
        } catch (err) {
            const errorMsg = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
                timestamp: new Date().toISOString()
            }
            setMessages(prev => [...prev, errorMsg])
        } finally {
            setLoading(false)
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    if (loadingHistory) {
        return (
            <div className="chat-loading">
                <div className="spinner"></div>
                <p>Loading chat history...</p>
            </div>
        )
    }

    return (
        <div className="chat-interface">
            <div className="chat-container">
                <div className="chat-top-bar">
                    <div className="chat-title">
                        <Sparkles className="sparkle-icon" size={20} />
                        <div>
                            <h2>AI Health Assistant</h2>
                            <p className="text-muted">Ask me anything about your health data</p>
                        </div>
                    </div>
                </div>

                <div className="messages-container">
                    {messages.length === 0 && (
                        <div className="empty-chat">
                            <Bot size={64} className="text-muted" />
                            <h3>Start a Conversation</h3>
                            <p className="text-muted">
                                I have access to your complete health profile. Ask me about your test results, medications, or health trends.
                            </p>
                            <div className="suggestion-chips">
                                <button className="chip" onClick={() => setInput('What are my latest test results?')}>
                                    Latest test results
                                </button>
                                <button className="chip" onClick={() => setInput('Do I have any abnormal values?')}>
                                    Abnormal values
                                </button>
                                <button className="chip" onClick={() => setInput('Tell me about my medications')}>
                                    My medications
                                </button>
                            </div>
                        </div>
                    )}

                    {messages.map((msg, index) => (
                        <div key={index} className={`message ${msg.role}`}>
                            <div className="message-avatar">
                                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                            </div>
                            <div className="message-content">
                                <div className="message-bubble">
                                    {msg.role === 'user' ? (
                                        msg.content
                                    ) : (
                                        msg.content.split('\n').map((paragraph, pIndex) => (
                                            <p key={pIndex} style={{ minHeight: paragraph.trim() ? 'auto' : '1em', marginBottom: '0.5em' }}>
                                                {paragraph.split(/(\*\*.*?\*\*)/).map((part, i) => {
                                                    if (part.startsWith('**') && part.endsWith('**')) {
                                                        return <strong key={i}>{part.slice(2, -2)}</strong>
                                                    }
                                                    return part
                                                })}
                                            </p>
                                        ))
                                    )}
                                </div>
                                <span className="message-time">
                                    {new Date(msg.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="message assistant">
                            <div className="message-avatar">
                                <Bot size={20} />
                            </div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-container">
                    <textarea
                        className="chat-input"
                        placeholder="Ask about your health data..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        rows={1}
                        disabled={loading}
                    />
                    <button
                        className="btn btn-primary send-btn"
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                    >
                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: (loading || !input.trim()) ? 0.5 : 1 }}>
                            <SendHorizontal size={24} strokeWidth={2.5} color={loading || !input.trim() ? "var(--text-muted)" : "#ffffff"} />
                        </span>
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ChatInterface
