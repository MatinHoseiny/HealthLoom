import { useState, useEffect } from 'react'
import { getDashboardData, getUserPreferences } from '../utils/api'
import { AlertCircle, CheckCircle, TrendingUp, Activity, MessageCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import SpotlightCard from './motion/SpotlightCard'
import BlurInText from './motion/BlurInText'
import GradientText from './motion/GradientText'
import ShimmerButton from './motion/ShimmerButton'
import './Dashboard.css'

function Dashboard({ userId }) {
    const [loading, setLoading] = useState(true)
    const [dashboardData, setDashboardData] = useState(null)
    const [error, setError] = useState(null)
    const [expandedAlerts, setExpandedAlerts] = useState({})
    const navigate = useNavigate()

    useEffect(() => {
        loadDashboard()
    }, [userId])

    const loadDashboard = async () => {
        try {
            setLoading(true)
            const [data, prefs] = await Promise.all([
                getDashboardData(userId),
                getUserPreferences(userId)
            ])
            setDashboardData(data)

            setDashboardData(data)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const toggleAlert = (index) => {
        setExpandedAlerts(prev => ({
            ...prev,
            [index]: !prev[index]
        }))
    }

    const handleGetAdvice = (testName, testValue) => {
        navigate(`/chat?question=Tell me more about my ${testName} level of ${testValue}`)
    }

    if (loading) {
        return (
            <div className="dashboard-loading">
                <div className="spinner"></div>
                <p>Loading your health dashboard...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="dashboard-error card">
                <AlertCircle size={48} />
                <h2>Unable to Load Dashboard</h2>
                <p>{error}</p>
                <button className="btn btn-primary" onClick={loadDashboard}>
                    Try Again
                </button>
            </div>
        )
    }

    const getStatusConfig = (status) => {
        switch (status) {
            case 'good':
                return {
                    class: 'status-good',
                    icon: <CheckCircle size={48} className="icon-success" />,
                    title: '✓ Overall Health Status: Good',
                    color: 'var(--success-color)'
                }
            case 'fair':
                return {
                    class: 'status-fair',
                    icon: <Activity size={48} className="icon-warning" style={{ color: '#f59e0b' }} />,
                    title: 'Overall Health Status: Fair',
                    color: '#f59e0b'
                }
            case 'no_data':
                return {
                    class: 'status-neutral',
                    icon: <Activity size={48} className="icon-info" style={{ color: '#6366f1' }} />,
                    title: '👋 Welcome to HealthLoom',
                    color: '#6366f1'
                }
            default:
                return {
                    class: 'status-attention',
                    icon: <AlertCircle size={48} className="icon-danger" />,
                    title: '⚠️ Attention Needed',
                    color: 'var(--error-color)'
                }
        }
    }

    const statusConfig = getStatusConfig(dashboardData?.health_status)
    const hasAbnormalResults = dashboardData?.abnormal_results?.length > 0

    const getGreeting = () => {
        const hour = new Date().getHours()
        const userName = dashboardData?.user?.name ? dashboardData.user.name.split(' ')[0] : 'User'

        if (hour >= 5 && hour < 12) {
            return `Good morning, ${userName}!`;
        } else if (hour >= 12 && hour < 17) {
            return `Good afternoon, ${userName}!`;
        } else if (hour >= 17 && hour < 21) {
            return `Good evening, ${userName}!`;
        } else {
            return `Good night, ${userName}!`;
        }
    }

    return (
        <>
            <div className="dashboard-header">
                <BlurInText
                    word={getGreeting()}
                    className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent"
                />
                <p className="text-muted mt-2">Here's your health snapshot</p>
            </div>

            <div className={`health-summary-card card ${statusConfig.class}`}>
                <div className="summary-header">
                    <div className="summary-icon">
                        {statusConfig.icon}
                    </div>
                    <div className="summary-title">
                        <h2>{statusConfig.title}</h2>
                        <div className="health-badge">
                            {dashboardData?.total_tests || 0} tests analyzed
                        </div>
                    </div>
                </div>
                <div className="summary-content">
                    <p className="summary-text">{dashboardData?.overall_health_summary}</p>
                </div>
            </div>

            <div className="stats-grid">
                <SpotlightCard>
                    <div className="stat-card">
                        <div className="stat-icon" style={{ background: 'var(--info-gradient)' }}>
                            <Activity size={24} />
                        </div>
                        <div className="stat-content">
                            <h3>{dashboardData?.total_tests || 0}</h3>
                            <p>Total Tests</p>
                        </div>
                    </div>
                </SpotlightCard>

                <SpotlightCard>
                    <div className="stat-card">
                        <div className="stat-icon" style={{ background: hasAbnormalResults ? 'var(--warning-gradient)' : 'var(--success-gradient)' }}>
                            <TrendingUp size={24} />
                        </div>
                        <div className="stat-content">
                            <h3>{dashboardData?.total_abnormal || 0}</h3>
                            <p>Items Needing Attention</p>
                        </div>
                    </div>
                </SpotlightCard>

                <SpotlightCard>
                    <div className="stat-card">
                        <div className="stat-icon" style={{ background: 'var(--primary-gradient)' }}>
                            <MessageCircle size={24} />
                        </div>
                        <div className="stat-content">
                            <h3>{dashboardData?.active_medications_count || 0}</h3>
                            <p>Active Medications</p>
                        </div>
                    </div>
                </SpotlightCard>
            </div>

            {hasAbnormalResults && (
                <div className="health-alerts-section">
                    <h2>Health Alerts & Recommendations</h2>
                    <p className="section-subtitle">Review these results that need attention</p>

                    <div className="alerts-list">
                        {dashboardData.abnormal_results.map((alert, index) => (
                            <div key={index} className="alert-card card">
                                <div className="alert-header" onClick={() => toggleAlert(index)}>
                                    <div className="alert-main-info">
                                        <div className="alert-icon">
                                            <AlertCircle className={alert.is_high ? 'text-warning' : 'text-info'} />
                                        </div>
                                        <div className="alert-title">
                                            <h3>{alert.test_name}</h3>
                                            <p className="alert-value">
                                                {alert.value} {alert.unit}
                                                <span className={`badge ${alert.is_high ? 'badge-high' : 'badge-low'}`}>
                                                    {alert.is_high ? 'High' : 'Low'}
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                    <button className="expand-btn">
                                        {expandedAlerts[index] ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                    </button>
                                </div>

                                <div className="alert-interpretation">
                                    <p>{alert.interpretation}</p>
                                </div>

                                {expandedAlerts[index] && (
                                    <div className="alert-details">
                                        {alert.possible_causes && alert.possible_causes.length > 0 && (
                                            <div className="alert-section">
                                                <h4>🔍 Possible Causes:</h4>
                                                <ul>
                                                    {alert.possible_causes.map((cause, i) => (
                                                        <li key={i}>{cause}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        <div className="alert-section">
                                            <h4>⚠️ Potential Risks:</h4>
                                            <ul>
                                                {alert.risks.map((risk, i) => (
                                                    <li key={i}>{risk}</li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div className="alert-section">
                                            <h4>💡 Recommendations:</h4>
                                            <ul>
                                                {alert.recommendations.map((rec, i) => (
                                                    <li key={i}>{rec}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                )}

                                <div className="alert-actions">
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => handleGetAdvice(alert.test_name, `${alert.value} ${alert.unit}`)}
                                    >
                                        <MessageCircle size={16} />
                                        Get AI Advice
                                    </button>
                                    <button
                                        className="btn btn-outline btn-sm"
                                        onClick={() => toggleAlert(index)}
                                    >
                                        {expandedAlerts[index] ? 'Show Less' : 'Learn More'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {dashboardData?.total_tests === 0 && (
                <div className="empty-state card">
                    <Activity size={64} className="text-muted" />
                    <h2>No Health Data Yet</h2>
                    <p className="text-muted">
                        Upload your first medical test to get started with AI-powered health insights!
                    </p>
                    <button className="btn btn-primary" onClick={() => navigate('/upload')}>
                        Upload Test Results
                    </button>
                </div>
            )}


        </>
    )
}

export default Dashboard
