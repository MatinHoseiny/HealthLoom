import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPortal } from 'react-dom'
import { uploadDocument, getUploadHistory, deleteUpload, getUploadDetails } from '../utils/api'
import { Upload, FileText, Image, CheckCircle, AlertCircle, Clock, Activity, Eye, Trash2 } from 'lucide-react'
import './UploadInterface.css'

function UploadInterface({ userId }) {
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [history, setHistory] = useState([])
    const [loadingHistory, setLoadingHistory] = useState(true)
    const [deleteModal, setDeleteModal] = useState(null)
    const navigate = useNavigate()

    useEffect(() => {
        loadHistory()
    }, [userId])

    const loadHistory = async () => {
        try {
            const data = await getUploadHistory(userId)
            setHistory(data)
        } catch (err) {
            console.error("Failed to load history:", err)
        } finally {
            setLoadingHistory(false)
        }
    }

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0]
        if (selectedFile) {
            setFile(selectedFile)
            setResult(null)
            setError(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return

        try {
            setUploading(true)
            setError(null)
            setProgress(0)

            const response = await uploadDocument(userId, file, (percent) => {
                setProgress(percent)
                if (percent === 100) {
                    setAnalyzing(true)
                }
            })

            setResult(response)
            setFile(null)
            await new Promise(resolve => setTimeout(resolve, 14000))
            navigate('/')

        } catch (err) {
            console.error("Upload error:", err)
            setError(err.response?.data?.detail || err.message || "Upload failed. Please try again.")
        } finally {
            setUploading(false)
            setAnalyzing(false)
            setProgress(0)
        }
    }

    const handleView = async (filePath, filename) => {
        try {
            const fileUrl = `/api/upload/file/${userId}?file_path=${encodeURIComponent(filePath)}`
            window.open(fileUrl, '_blank')
        } catch (err) {
            console.error("Failed to view file:", err)
            setError("Failed to open file")
        }
    }

    const handleDelete = (filePath) => {
        console.log("🗑️ Request to delete:", filePath)
        setDeleteModal(filePath)
    }

    const confirmDelete = async () => {
        if (!deleteModal) return

        const filePath = deleteModal
        console.log("✅ User confirmed delete for:", filePath)

        try {
            const response = await deleteUpload(userId, filePath)
            console.log("✅ DELETE SUCCESS:", response)

            await loadHistory()

            if (result && result.file_path === filePath) {
                setResult(null)
            }

            setDeleteModal(null) // Close modal
        } catch (err) {
            console.error("❌ DELETE FAILED:", err)
            alert(`Delete failed: ${err.response?.data?.detail || err.message}`)
            setDeleteModal(null)
        }
    }

    const getFileIcon = (filename) => {
        if (filename.match(/\.(jpg|jpeg|png)$/i)) {
            return <Image size={24} />
        }
        return <FileText size={24} />
    }

    const [analysisStage, setAnalysisStage] = useState({ text: "Initializing...", percent: 0 })

    useEffect(() => {
        let interval
        if (analyzing) {
            let step = 0
            const stages = [
                { text: "Scanning Document Structure...", percent: 15 },
                { text: "Extracting Medical Values...", percent: 40 },
                { text: "Cross-referencing Reference Ranges...", percent: 65 },
                { text: "Generating Health Insights...", percent: 90 },
                { text: "Finalizing Analysis...", percent: 98 }
            ]

            interval = setInterval(() => {
                if (step < stages.length) {
                    setAnalysisStage({ ...stages[step], stepIndex: step })
                    step++
                }
            }, 2000)
        } else {
            setAnalysisStage({ text: "Initializing...", percent: 0 })
        }
        return () => clearInterval(interval)
    }, [analyzing])

    return (
        <div className="upload-container">
            <div className="page-header" style={{ marginBottom: '2rem' }}>
                <div>
                    <h1>Upload Medical Records</h1>
                    <p className="text-muted" style={{ marginTop: '0.25rem' }}>Upload your test results for instant AI analysis</p>
                </div>
            </div>
            {analyzing && createPortal(
                <div className="analyzing-overlay">
                    <div className="analyzing-content" style={{ width: '400px' }}>
                        <div className="brain-pulse">
                            <Activity size={64} />
                        </div>
                        <h2>AI Analysis in Progress</h2>

                        <div className="analysis-steps-list">
                            {[
                                "Scanning Document Structure...",
                                "Extracting Medical Values...",
                                "Cross-referencing Reference Ranges...",
                                "Generating Health Insights...",
                                "Finalizing Analysis..."
                            ].map((step, index) => {
                                const isCompleted = index < (analysisStage.stepIndex || 0);
                                const isCurrent = index === (analysisStage.stepIndex || 0);

                                return (
                                    <div
                                        key={index}
                                        className={`analysis-step-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}
                                    >
                                        <div className="step-indicator-circle">
                                            <div className="circle-inner"></div>
                                        </div>
                                        <span className="step-label">{step}</span>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>,
                document.body
            )
            }

            {
                error && createPortal(
                    <div className="analyzing-overlay">
                        <div className="analyzing-content" style={{ width: '400px', padding: '2rem' }}>
                            <div style={{ marginBottom: '1.5rem', color: '#ef4444' }}>
                                <AlertCircle size={64} />
                            </div>
                            <h3 style={{ marginBottom: '1rem', color: '#fca5a5' }}>Upload Error</h3>
                            <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                                {error}
                            </p>
                            <button
                                className="btn btn-primary full-width"
                                onClick={() => setError(null)}
                            >
                                Got it
                            </button>
                        </div>
                    </div>,
                    document.body
                )
            }

            <div className="upload-split">
                <div className="upload-history">
                    <div className="section-header">
                        <h2>Recent Uploads</h2>
                    </div>

                    <div className="history-list">
                        {loadingHistory ? (
                            <div className="history-loading">
                                <div className="spinner-small"></div>
                                <p>Finding your documents...</p>
                            </div>
                        ) : history.length === 0 ? (
                            <div className="empty-history">
                                <div className="empty-icon-wrapper">
                                    <Clock size={32} />
                                </div>
                                <h3>No uploads yet</h3>
                                <p>Upload your first medical record to get started</p>
                            </div>
                        ) : (
                            history.map((item, index) => (
                                <div key={index} className="history-item">
                                    <div className="history-icon">
                                        {getFileIcon(item.filename)}
                                    </div>
                                    <div className="history-details">
                                        <div className="history-filename" title={item.filename}>{item.filename}</div>
                                        <div className="history-summary">{item.summary}</div>
                                        <span className="upload-date">
                                            {(() => {
                                                const d = item.upload_date.split('T')[0].split('-');
                                                return `${d[2]}/${d[1]}/${d[0]}`;
                                            })()}
                                        </span>
                                    </div>
                                    <div className="history-actions">
                                        <button
                                            className="action-btn view"
                                            title="View Original File"
                                            onClick={() => handleView(item.file_path, item.filename)}
                                        >
                                            <Eye size={18} />
                                        </button>
                                        <button
                                            className="action-btn delete"
                                            title="Delete Upload"
                                            onClick={() => handleDelete(item.file_path)}
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="upload-main">
                    <div className="upload-card">
                        {!result ? (
                            <>
                                <div className="upload-zone drop-zone">
                                    <input
                                        type="file"
                                        id="file-input"
                                        accept="image/*,.pdf"
                                        onChange={handleFileChange}
                                        className="file-input"
                                        disabled={uploading}
                                        style={{ display: 'none' }}
                                    />

                                    <label htmlFor="file-input" className="file-label" style={{ width: '100%', cursor: 'pointer' }}>
                                        <div className="upload-icon-wrapper">
                                            {file ? <CheckCircle size={48} className="text-success" /> : <Upload size={48} />}
                                        </div>

                                        <div className="upload-text">
                                            {file ? (
                                                <>
                                                    <h3>{file.name}</h3>
                                                    <p>{(file.size / 1024).toFixed(2)} KB</p>
                                                </>
                                            ) : (
                                                <>
                                                    <h3>Click to Upload</h3>
                                                    <p>PDF, JPG, PNG (Max 10MB)</p>
                                                </>
                                            )}
                                        </div>
                                    </label>
                                </div>

                                {file && !uploading && (
                                    <button
                                        className="btn btn-primary upload-btn full-width"
                                        onClick={handleUpload}
                                        disabled={uploading}
                                        style={{ marginTop: '1rem' }}
                                    >
                                        Analyze Document
                                    </button>
                                )}

                                {uploading && !analyzing && (
                                    <div className="upload-progress-compact">
                                        <div className="progress-bar">
                                            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                                        </div>
                                        <span>Uploading... {progress}%</span>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="upload-result success slide-up">
                                <div className="result-header">
                                    <div className="result-title">
                                        <CheckCircle size={32} className="text-success" />
                                        <div>
                                            <h3>Analysis Results</h3>
                                            <p>Extracted {result.extracted_tests?.length || 0} test results</p>
                                        </div>
                                    </div>
                                    <button className="btn-close" onClick={() => setResult(null)}>×</button>
                                </div>

                                {result.extracted_tests && result.extracted_tests.length > 0 && (
                                    <div className="extracted-tests">
                                        {result.extracted_tests.map((test, index) => (
                                            <div key={index} className="extracted-test-item">
                                                <div>
                                                    <strong>{test.test_name}</strong>
                                                    <span className="test-category">{test.category}</span>
                                                </div>
                                                <div className="test-result-value">
                                                    <span className={test.is_abnormal ? 'text-warning' : 'text-success'}>
                                                        {test.value} {test.unit}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <button className="btn btn-primary full-width" onClick={() => window.location.href = '/'}>
                                    Go to Dashboard
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            {
                deleteModal && createPortal(
                    <div className="analyzing-overlay" style={{ zIndex: 2000 }}>
                        <div className="analyzing-content" style={{ padding: '2rem', maxWidth: '400px' }}>
                            <div style={{ marginBottom: '1.5rem', color: '#ef4444' }}>
                                <Trash2 size={48} />
                            </div>
                            <h3 style={{ marginBottom: '1rem' }}>Delete this upload?</h3>
                            <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
                                This action cannot be undone. The file and its analysis will be permanently removed.
                            </p>
                            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                                <button
                                    className="btn"
                                    style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }}
                                    onClick={() => setDeleteModal(null)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="btn"
                                    style={{ background: '#ef4444', color: 'white', border: 'none' }}
                                    onClick={confirmDelete}
                                >
                                    Delete Forever
                                </button>
                            </div>
                        </div>
                    </div>,
                    document.body
                )
            }
        </div >
    )
}

export default UploadInterface
