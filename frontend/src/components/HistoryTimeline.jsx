import { useState, useEffect } from 'react'
import { getUserTests } from '../utils/api'
import { Calendar, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp, Beaker } from 'lucide-react'
import './HistoryTimeline.css'

function HistoryTimeline({ userId }) {
    const [tests, setTests] = useState([])
    const [loading, setLoading] = useState(true)
    const [expandedGroups, setExpandedGroups] = useState({}) // Stores composite keys like "date-category"

    useEffect(() => {
        loadTests()
    }, [userId])

    const loadTests = async () => {
        try {
            const allTests = await getUserTests(userId, { limit: 100 })
            setTests(allTests)
        } catch (err) {
            console.error('Failed to load tests:', err)
        } finally {
            setLoading(false)
        }
    }

    const groupByDateAndCategory = (tests) => {
        const grouped = {}
        tests.forEach(test => {
            const isoDate = test.test_date.split('T')[0]
            const category = test.category || 'Other'
            if (!grouped[isoDate]) {
                grouped[isoDate] = {}
            }
            if (!grouped[isoDate][category]) {
                grouped[isoDate][category] = []
            }
            grouped[isoDate][category].push(test)
        })
        return grouped
    }

    const toggleGroup = (date, category) => {
        const key = `${date}-${category}`
        setExpandedGroups(prev => ({
            ...prev,
            [key]: !prev[key]
        }))
    }

    if (loading) {
        return (
            <div className="history-loading">
                <div className="spinner"></div>
                <p>Loading history...</p>
            </div>
        )
    }

    const groupedTests = groupByDateAndCategory(tests)
    const dates = Object.keys(groupedTests).sort((a, b) => new Date(b) - new Date(a))

    return (
        <div className="history-timeline">
            <div className="history-header">
                <h1>Health History</h1>
                <p className="text-muted">Your complete medical test timeline</p>
            </div>

            {dates.length === 0 ? (
                <div className="empty-state card">
                    <Calendar size={64} className="text-muted" />
                    <h2>No History Yet</h2>
                    <p className="text-muted">Upload test results to build your health timeline</p>
                </div>
            ) : (
                <div className="timeline">
                    {dates.map(date => {
                        const categoriesForDate = Object.keys(groupedTests[date]).sort()
                        const totalTestsForDate = categoriesForDate.reduce((sum, cat) => sum + groupedTests[date][cat].length, 0)

                        const [year, month, day] = date.split('-');

                        return (
                            <div key={date} className="timeline-section">
                                <div className="timeline-date">
                                    <Calendar size={20} />
                                    <h3>{`${day}/${month}/${year}`}</h3>
                                    <span className="test-count">{totalTestsForDate} tests</span>
                                </div>
                                <div className="timeline-categories">
                                    {categoriesForDate.map(category => {
                                        const categoryTests = groupedTests[date][category]
                                        const key = `${date}-${category}`
                                        const isExpanded = expandedGroups[key]
                                        const abnormalCount = categoryTests.filter(t => t.is_abnormal).length

                                        return (
                                            <div key={category} className="category-group card">
                                                <div
                                                    className={`category-header ${isExpanded ? 'expanded' : ''}`}
                                                    onClick={() => toggleGroup(date, category)}
                                                >
                                                    <div className="category-header-left">
                                                        <Beaker size={18} className="category-icon" />
                                                        <h4>{category}</h4>
                                                        <span className="category-count">{categoryTests.length} tests</span>
                                                        {abnormalCount > 0 && (
                                                            <span className="category-abnormal-badge">{abnormalCount} Abnormal</span>
                                                        )}
                                                    </div>
                                                    <div className="category-header-right">
                                                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                                    </div>
                                                </div>

                                                {isExpanded && (
                                                    <div className="category-content">
                                                        <div className="timeline-tests">
                                                            {categoryTests.map(test => (
                                                                <div key={test.id} className="timeline-test card">
                                                                    <div className="test-header">
                                                                        <div>
                                                                            <h4>{test.test_name}</h4>
                                                                        </div>
                                                                        <div className="test-value-container">
                                                                            <span className={`test-value ${test.is_abnormal ? 'abnormal' : 'normal'}`}>
                                                                                {test.value} {test.unit}
                                                                            </span>
                                                                            {test.is_abnormal && (
                                                                                <span className="abnormal-badge">Abnormal</span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                    {test.reference_range && (
                                                                        <p className="reference-range text-muted">
                                                                            Normal range: {test.reference_range}
                                                                        </p>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export default HistoryTimeline
