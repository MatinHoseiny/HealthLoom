import { NavLink } from 'react-router-dom'
import { Activity, Upload, MessageCircle, Pill, Clock, User, Moon, Sun } from 'lucide-react'
import { motion } from 'framer-motion'
import BlurInText from './motion/BlurInText'
import { useTheme } from '../context/ThemeContext'
import './Header.css'

function Header({ user }) {
    const { theme, toggleTheme } = useTheme()

    return (
        <header className="header">
            <div className="header-content">
                <div className="header-logo">
                    <motion.div
                        whileHover={{ rotate: 180 }}
                        transition={{ duration: 0.5 }}
                        className="logo-icon-wrapper"
                    >
                        <Activity className="logo-icon" />
                    </motion.div>
                    <BlurInText
                        word="HealthLoom"
                        className="logo-text bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent"
                    />
                    <span className="logo-badge">AI</span>
                </div>

                <nav className="header-nav">
                    <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        <Activity size={20} />
                        <span>Dashboard</span>
                    </NavLink>

                    <NavLink to="/upload" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        <Upload size={20} />
                        <span>Upload</span>
                    </NavLink>

                    <NavLink to="/chat" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        <MessageCircle size={20} />
                        <span>AI Chat</span>
                    </NavLink>

                    <NavLink to="/medications" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        <Pill size={20} />
                        <span>Medications</span>
                    </NavLink>

                    <NavLink to="/history" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        <Clock size={20} />
                        <span>History</span>
                    </NavLink>
                </nav>

                <div className="header-user">
                    <button
                        className="theme-toggle-btn"
                        onClick={toggleTheme}
                        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                    >
                        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                    </button>

                    <NavLink to="/profile" className="user-profile-link" title="View Profile">
                        <div className="user-avatar">
                            {user?.name ? (
                                <span>{user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}</span>
                            ) : (
                                <User size={20} />
                            )}
                        </div>
                    </NavLink>
                </div>
            </div>
        </header>
    )
}

export default Header
