import { useState, useEffect } from 'react'
import { useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Activity, FileText, Pill, Upload as UploadIcon, MessageCircle, User, Moon, Sun } from 'lucide-react'
import BlurInText from './motion/BlurInText'
import Aurora from './Aurora'
import Dashboard from './Dashboard'
import UploadInterface from './UploadInterface'
import ChatInterface from './ChatInterface'
import MedicationManager from './MedicationManager'
import HistoryTimeline from './HistoryTimeline'
import Profile from './Profile'
import { getCurrentUser } from '../utils/api'
import { useTheme } from '../context/ThemeContext'
import './MainLayout.css'

function MainLayout({ userId }) {
    const location = useLocation()
    const navigate = useNavigate()
    const { theme, toggleTheme } = useTheme()
    const [currentUser, setCurrentUser] = useState(null)
    const [activeTab, setActiveTab] = useState('dashboard')

    const { scrollY } = useScroll()

    const scrollRange = [0, 80]

    const logoLeft = useTransform(scrollY, scrollRange, ['50%', '0%'])
    const logoTranslateX = useTransform(scrollY, scrollRange, ['-50%', '0%'])
    const logoMarginLeft = useTransform(scrollY, scrollRange, ['0px', '24px'])

    const logoScale = useTransform(scrollY, scrollRange, [1.8, 1])
    const headerHeight = useTransform(scrollY, scrollRange, ['120px', '70px'])
    const headerBgOpacity = useTransform(scrollY, scrollRange, [0, 0.95])
    const headerBgColor = useTransform(headerBgOpacity, (opacity) =>
        theme === 'dark' ? `rgba(15, 23, 42, ${opacity})` : `rgba(255, 255, 255, ${opacity})`
    )


    useEffect(() => {
        const loadUser = async () => {
            try {
                const user = await getCurrentUser(userId)
                setCurrentUser(user)
            } catch (error) {
                console.error('Failed to load user:', error)
            }
        }
        loadUser()
    }, [userId])

    useEffect(() => {
        const path = location.pathname
        if (path === '/') setActiveTab('dashboard')
        else if (path.includes('/upload')) setActiveTab('upload')
        else if (path.includes('/medications')) setActiveTab('medications')
        else if (path.includes('/history')) setActiveTab('tests')
        else if (path.includes('/chat')) setActiveTab('chat')
        else if (path.includes('/profile')) setActiveTab('profile')
    }, [location.pathname])

    const handleTabChange = (tab) => {
        setActiveTab(tab)
        const routes = {
            dashboard: '/',
            tests: '/history',
            medications: '/medications',
            upload: '/upload',
            chat: '/chat',
            profile: '/profile'
        }
        navigate(routes[tab])
    }

    return (
        <div className="modern-container">
            <Aurora />

            <motion.header
                className="modern-header"
                initial={{
                    height: '120px',
                    backgroundColor: theme === 'dark' ? 'rgba(15, 23, 42, 0)' : 'rgba(255, 255, 255, 0)'
                }}
                style={{
                    height: headerHeight,
                    backgroundColor: headerBgColor,
                    willChange: 'height, background-color'
                }}
            >
                <div className="header-container" style={{ position: 'relative', height: '100%' }}>

                    <motion.div
                        className="header-logo-section"
                        initial={{
                            left: '50%',
                            x: '-50%',
                            marginLeft: '0px',
                            scale: 1.8
                        }}
                        style={{
                            position: 'absolute',
                            left: logoLeft,
                            x: logoTranslateX,
                            marginLeft: logoMarginLeft,
                            scale: logoScale,
                            top: '50%',
                            y: '-50%',
                            transformOrigin: 'center center',
                            zIndex: 60,
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            whiteSpace: 'nowrap',
                            willChange: 'transform, left'
                        }}
                    >
                        <div className="logo-text-section" style={{ marginTop: '0.5rem' }}>
                            <h1 className="logo-title-big">HEALTHLOOM</h1>
                            <p
                                className="logo-subtitle"
                            >
                                Advanced Medical Intelligence
                            </p>
                        </div>
                    </motion.div>

                    <div className="header-actions" style={{ marginLeft: 'auto' }}>
                        <button
                            className="theme-toggle-btn"
                            onClick={toggleTheme}
                            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
                        >
                            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                        </button>
                        <div
                            className="user-avatar"
                            onClick={() => navigate('/profile')}
                        >
                            {currentUser?.name ? (
                                <span className="user-avatar-text">
                                    {currentUser.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                                </span>
                            ) : (
                                <User size={20} />
                            )}
                        </div>
                    </div>
                </div >
            </motion.header >

            < div className="main-content" >
                < div className="modern-tabs" >
                    <div className="tabs-list">
                        <button
                            className={`tab-trigger ${activeTab === 'dashboard' ? 'active' : ''}`}
                            onClick={() => handleTabChange('dashboard')}
                        >
                            <Activity className="tab-icon" />
                            Dashboard
                        </button>
                        <button
                            className={`tab-trigger ${activeTab === 'tests' ? 'active' : ''}`}
                            onClick={() => handleTabChange('tests')}
                        >
                            <FileText className="tab-icon" />
                            Test Results
                        </button>
                        <button
                            className={`tab-trigger ${activeTab === 'medications' ? 'active' : ''}`}
                            onClick={() => handleTabChange('medications')}
                        >
                            <Pill className="tab-icon" />
                            Medications
                        </button>
                        <button
                            className={`tab-trigger ${activeTab === 'upload' ? 'active' : ''}`}
                            onClick={() => handleTabChange('upload')}
                        >
                            <UploadIcon className="tab-icon" />
                            Upload
                        </button>
                        <button
                            className={`tab-trigger ${activeTab === 'chat' ? 'active' : ''}`}
                            onClick={() => handleTabChange('chat')}
                        >
                            <MessageCircle className="tab-icon" />
                            AI Assistant
                        </button>
                    </div>
                </div >

                < div className="tab-content" >
                    {activeTab === 'dashboard' && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                        >
                            <Dashboard userId={userId} />
                        </motion.div>
                    )
                    }

                    {
                        activeTab === 'tests' && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <HistoryTimeline userId={userId} />
                            </motion.div>
                        )
                    }

                    {
                        activeTab === 'medications' && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <MedicationManager userId={userId} />
                            </motion.div>
                        )
                    }

                    {
                        activeTab === 'upload' && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <UploadInterface userId={userId} />
                            </motion.div>
                        )
                    }

                    {
                        activeTab === 'chat' && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <ChatInterface userId={userId} />
                            </motion.div>
                        )
                    }

                    {
                        activeTab === 'profile' && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <Profile userId={userId} />
                            </motion.div>
                        )
                    }
                </div >
            </div >
        </div >
    )
}

export default MainLayout

