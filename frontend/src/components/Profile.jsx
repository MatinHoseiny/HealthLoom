import { useState, useEffect } from 'react'
import { User, Mail, Edit2, Save, X, FileText } from 'lucide-react'
import { getCurrentUser, updateUser, getUserPreferences, updateUserPreferences } from '../utils/api'
import './Profile.css'

function Profile({ userId }) {
    const [user, setUser] = useState(null)
    const [preferences, setPreferences] = useState(null)
    const [isEditing, setIsEditing] = useState(false)
    const [editedUser, setEditedUser] = useState({})
    const [isEditingPrefs, setIsEditingPrefs] = useState(false)
    const [editedPrefs, setEditedPrefs] = useState({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [savingPrefs, setSavingPrefs] = useState(false)


    useEffect(() => {
        loadUserData()
    }, [userId])

    const loadUserData = async () => {
        try {
            setLoading(true)
            const [userData, prefsData] = await Promise.all([
                getCurrentUser(userId),
                getUserPreferences(userId)
            ])
            setUser(userData)
            setPreferences(prefsData)
            setEditedUser(userData)
        } catch (error) {
            console.error('Failed to load user data:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleEdit = () => {
        setIsEditing(true)
        setEditedUser({ ...user })
    }

    const handleCancel = () => {
        setIsEditing(false)
        setEditedUser({ ...user })
    }

    const handleSave = async () => {
        try {
            setSaving(true)
            const updated = await updateUser(userId, editedUser)
            setUser(updated)
            setIsEditing(false)
        } catch (error) {
            console.error('Failed to update user:', error)
            alert('Failed to save changes. Please try again.')
        } finally {
            setSaving(false)
        }
    }

    const handleChange = (field, value) => {
        setEditedUser({ ...editedUser, [field]: value })
    }

    const handleEditPrefs = () => {
        setIsEditingPrefs(true)
        setEditedPrefs({
            health_goals: preferences?.health_goals || [],
            dietary_restrictions: preferences?.dietary_restrictions || [],
            exercise_frequency: preferences?.exercise_frequency || 'never',
            health_concerns: preferences?.health_concerns || [],
            questionnaire_completed: true
        })
    }

    const handleCancelPrefs = () => {
        setIsEditingPrefs(false)
    }

    const handleSavePrefs = async () => {
        try {
            setSavingPrefs(true)
            // Ensure array fields are actually arrays (split by comma if they are strings)
            const formattedPrefs = { ...editedPrefs }
            if (typeof formattedPrefs.health_goals === 'string') {
                formattedPrefs.health_goals = formattedPrefs.health_goals.split(',').map(s => s.trim()).filter(Boolean)
            }
            if (typeof formattedPrefs.dietary_restrictions === 'string') {
                formattedPrefs.dietary_restrictions = formattedPrefs.dietary_restrictions.split(',').map(s => s.trim()).filter(Boolean)
            }
            if (typeof formattedPrefs.health_concerns === 'string') {
                formattedPrefs.health_concerns = formattedPrefs.health_concerns.split(',').map(s => s.trim()).filter(Boolean)
            }

            const updated = await updateUserPreferences(userId, formattedPrefs)
            setPreferences(updated)
            setIsEditingPrefs(false)
        } catch (error) {
            console.error('Failed to update preferences:', error)
            alert('Failed to save preferences. Please try again.')
        } finally {
            setSavingPrefs(false)
        }
    }

    const handlePrefChange = (field, value) => {
        setEditedPrefs({ ...editedPrefs, [field]: value })
    }



    const calculateProfileCompletion = () => {
        if (!user) return 0
        const fields = ['name', 'email', 'age', 'gender']
        const completed = fields.filter(f => user[f]).length

        // Add preferences completion
        let prefsScore = 0
        if (preferences?.questionnaire_completed) {
            prefsScore = 40 // 40% for completing questionnaire
        }

        return Math.round((completed / fields.length) * 60 + prefsScore)
    }

    if (loading) {
        return (
            <div className="profile-loading">
                <div className="spinner"></div>
                <p>Loading your profile...</p>
            </div>
        )
    }

    const completion = calculateProfileCompletion()

    return (
        <>
            <div className="profile-container">
                <div className="profile-header">
                    <div className="profile-avatar">
                        <User size={48} />
                    </div>
                    <div className="profile-info">
                        <h1>{user?.name || 'User Profile'}</h1>
                        <p className="text-muted">{user?.email || 'No email set'}</p>
                    </div>
                    {!isEditing && (
                        <button className="btn btn-primary" onClick={handleEdit}>
                            <Edit2 size={18} />
                            Edit Profile
                        </button>
                    )}
                </div>

                {/* Profile Completion */}
                <div className="profile-completion card">
                    <div className="completion-header">
                        <h3>Profile Completion</h3>
                        <span className="completion-percent">{completion}%</span>
                    </div>
                    <div className="completion-bar">
                        <div className="completion-fill" style={{ width: `${completion}%` }} />
                    </div>
                    {completion < 100 && (
                        <p className="completion-hint">
                            {!preferences?.questionnaire_completed && (
                                <span>Complete the health questionnaire to improve personalization!</span>
                            )}
                            {!user?.name && <span>Add your name • </span>}
                            {!user?.email && <span>Add your email</span>}
                        </p>
                    )}
                </div>

                {/* Personal Information */}
                <div className="profile-section card">
                    <h2>Personal Information</h2>

                    <div className="info-grid">
                        <div className="info-item">
                            <label>Name</label>
                            {isEditing ? (
                                <input
                                    type="text"
                                    value={editedUser.name || ''}
                                    onChange={(e) => handleChange('name', e.target.value)}
                                    placeholder="Your name"
                                />
                            ) : (
                                <p>{user?.name || 'Not set'}</p>
                            )}
                        </div>

                        <div className="info-item">
                            <label>Email</label>
                            {isEditing ? (
                                <input
                                    type="email"
                                    value={editedUser.email || ''}
                                    onChange={(e) => handleChange('email', e.target.value)}
                                    placeholder="your@email.com"
                                />
                            ) : (
                                <p>{user?.email || 'Not set'}</p>
                            )}
                        </div>

                        <div className="info-item">
                            <label>Age</label>
                            {isEditing ? (
                                <input
                                    type="number"
                                    value={editedUser.age || ''}
                                    onChange={(e) => handleChange('age', parseInt(e.target.value))}
                                    placeholder="25"
                                    min="1"
                                    max="150"
                                />
                            ) : (
                                <p>{user?.age || 'Not set'}</p>
                            )}
                        </div>

                        <div className="info-item">
                            <label>Gender</label>
                            {isEditing ? (
                                <select
                                    value={editedUser.gender || ''}
                                    onChange={(e) => handleChange('gender', e.target.value)}
                                >
                                    <option value="">Select...</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                </select>
                            ) : (
                                <p>{user?.gender || 'Not set'}</p>
                            )}
                        </div>
                    </div>

                    {isEditing && (
                        <div className="edit-actions">
                            <button className="btn btn-outline" onClick={handleCancel}>
                                <X size={18} />
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={handleSave}
                                disabled={saving}
                            >
                                <Save size={18} />
                                {saving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Health Preferences */}
                <div className="profile-section card">
                    <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h2 style={{ margin: 0 }}>Health Preferences</h2>
                        {!isEditingPrefs && (
                            <button className="btn btn-outline" onClick={handleEditPrefs} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                                <Edit2 size={16} />
                                {preferences?.questionnaire_completed ? 'Edit' : 'Complete Questionnaire'}
                            </button>
                        )}
                    </div>

                    {isEditingPrefs ? (
                        <div className="info-grid">
                            <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                                <label>Health Goals (comma separated)</label>
                                <input
                                    type="text"
                                    value={Array.isArray(editedPrefs.health_goals) ? editedPrefs.health_goals.join(', ') : editedPrefs.health_goals}
                                    onChange={(e) => handlePrefChange('health_goals', e.target.value)}
                                    placeholder="e.g., Lose weight, Build muscle, Better sleep"
                                />
                            </div>
                            <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                                <label>Dietary Restrictions (comma separated)</label>
                                <input
                                    type="text"
                                    value={Array.isArray(editedPrefs.dietary_restrictions) ? editedPrefs.dietary_restrictions.join(', ') : editedPrefs.dietary_restrictions}
                                    onChange={(e) => handlePrefChange('dietary_restrictions', e.target.value)}
                                    placeholder="e.g., Vegetarian, Gluten-free, Keto"
                                />
                            </div>
                            <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                                <label>Exercise Frequency</label>
                                <select
                                    value={editedPrefs.exercise_frequency}
                                    onChange={(e) => handlePrefChange('exercise_frequency', e.target.value)}
                                >
                                    <option value="never">Never</option>
                                    <option value="rarely">Rarely (1-2 times/month)</option>
                                    <option value="occasionally">Occasionally (1-2 times/week)</option>
                                    <option value="regularly">Regularly (3-4 times/week)</option>
                                    <option value="daily">Daily</option>
                                </select>
                            </div>
                            <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                                <label>Health Concerns (comma separated)</label>
                                <input
                                    type="text"
                                    value={Array.isArray(editedPrefs.health_concerns) ? editedPrefs.health_concerns.join(', ') : editedPrefs.health_concerns}
                                    onChange={(e) => handlePrefChange('health_concerns', e.target.value)}
                                    placeholder="e.g., Joint pain, High blood pressure, Anxiety"
                                />
                            </div>

                            <div className="edit-actions" style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                                <button className="btn btn-outline" onClick={handleCancelPrefs}>
                                    <X size={18} />
                                    Cancel
                                </button>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSavePrefs}
                                    disabled={savingPrefs}
                                >
                                    <Save size={18} />
                                    {savingPrefs ? 'Saving...' : 'Save Preferences'}
                                </button>
                            </div>
                        </div>
                    ) : preferences?.questionnaire_completed ? (
                        <div className="preferences-summary">
                            {preferences.health_goals?.length > 0 && (
                                <div className="pref-item">
                                    <strong>Health Goals:</strong>
                                    <p>{preferences.health_goals.join(', ')}</p>
                                </div>
                            )}
                            {preferences.dietary_restrictions?.length > 0 && (
                                <div className="pref-item">
                                    <strong>Dietary Preferences:</strong>
                                    <p>{preferences.dietary_restrictions.join(', ')}</p>
                                </div>
                            )}
                            {preferences.exercise_frequency && (
                                <div className="pref-item">
                                    <strong>Exercise:</strong>
                                    <p>{preferences.exercise_frequency}</p>
                                </div>
                            )}
                            {preferences.health_concerns?.length > 0 && (
                                <div className="pref-item">
                                    <strong>Health Concerns:</strong>
                                    <p>{preferences.health_concerns.join(', ')}</p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="empty-preferences">
                            <FileText size={48} className="text-muted" />
                            <p>You haven't completed the health questionnaire yet.</p>
                            <p className="text-muted">
                                Complete it to get more personalized health insights and recommendations.
                            </p>
                        </div>
                    )}
                </div>
            </div>


        </>
    )
}

export default Profile
