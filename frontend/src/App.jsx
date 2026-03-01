import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Header from './components/Header'
import MainLayout from './components/MainLayout'
import Profile from './components/Profile'
import { getCurrentUser, createUser } from './utils/api'
import { ThemeProvider } from './context/ThemeContext'

function App() {
    const [currentUser, setCurrentUser] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        initializeUser()
    }, [])

    const initializeUser = async () => {
        try {
            const userId = localStorage.getItem('healthloom_user_id')

            if (userId) {
                try {
                    const user = await getCurrentUser(userId)
                    setCurrentUser(user)
                } catch (error) {
                    console.warn('Stored user ID invalid, creating new guest user:', error.message)
                    await createGuestUser()
                }
            } else {
                await createGuestUser()
            }
        } catch (error) {
            console.error('Error initializing user:', error)
        } finally {
            setLoading(false)
        }
    }

    const createGuestUser = async () => {
        try {
            const guestData = {
                age: 30,
                gender: "prefer_not_to_say",
                limitations_json: [],
                conditions_json: [],
                language_preference: "en"
            }
            const newUser = await createUser(guestData)
            localStorage.setItem('healthloom_user_id', newUser.id)
            setCurrentUser(newUser)
        } catch (error) {
            console.error('Failed to create guest user:', error)
        }
    }

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="spinner"></div>
                <p>Loading HealthLoom...</p>
            </div>
        )
    }

    if (!currentUser) {
        return (
            <div className="loading-screen">
                <p>Connection failed. Please refresh.</p>
                <button onClick={() => window.location.reload()}>Retry</button>
            </div>
        )
    }

    return (
        <ThemeProvider>
            <Router>
                <div className="app">
                    <main className="main-content">
                        <Routes>
                            <Route path="/" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="/upload" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="/chat" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="/medications" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="/history" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="/profile" element={<MainLayout userId={currentUser.id} />} />
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </main>
                </div>
            </Router>
        </ThemeProvider>
    )
}

export default App
