import { useState, useEffect } from 'react'
import { getUserMedications, addMedication, deleteMedication, updateMedication } from '../utils/api'
import { Plus, Pill, AlertTriangle, X, Edit2, Check, XCircle } from 'lucide-react'
import './MedicationManager.css'

function MedicationManager({ userId }) {
    const [medications, setMedications] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        brand_name: '',
        dosage: '',
        frequency: ''
    })
    const [submitting, setSubmitting] = useState(false)
    const [editingId, setEditingId] = useState(null)
    const [editData, setEditData] = useState({
        dosage: '',
        frequency: ''
    })
    const [updating, setUpdating] = useState(false)

    useEffect(() => {
        loadMedications()
    }, [userId])

    const loadMedications = async () => {
        try {
            const meds = await getUserMedications(userId, true)
            setMedications(meds)
        } catch (err) {
            console.error('Failed to load medications:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.brand_name.trim()) return

        try {
            setSubmitting(true)
            await addMedication({
                user_id: userId,
                brand_name: formData.brand_name,
                dosage: formData.dosage || null,
                frequency: formData.frequency || null
            })

            setFormData({ brand_name: '', dosage: '', frequency: '' })
            setShowForm(false)
            loadMedications()
        } catch (err) {
            console.error('Failed to add medication:', err)
        } finally {
            setSubmitting(false)
        }
    }

    const handleDelete = async (medId) => {
        if (confirm('Stop taking this medication?')) {
            try {
                await deleteMedication(medId)
                loadMedications()
            } catch (err) {
                console.error('Failed to delete medication:', err)
            }
        }
    }

    const handleEdit = (med) => {
        setEditingId(med.id)
        setEditData({
            dosage: med.dosage || '',
            frequency: med.frequency || ''
        })
    }

    const handleCancelEdit = () => {
        setEditingId(null)
        setEditData({ dosage: '', frequency: '' })
    }

    const handleUpdateMedication = async (medId) => {
        try {
            setUpdating(true)
            await updateMedication(medId, {
                dosage: editData.dosage,
                frequency: editData.frequency
            })
            setEditingId(null)
            loadMedications()
        } catch (err) {
            console.error('Failed to update medication:', err)
        } finally {
            setUpdating(false)
        }
    }

    if (loading) {
        return (
            <div className="medication-loading">
                <div className="spinner"></div>
                <p>Loading medications...</p>
            </div>
        )
    }

    return (
        <div className="medication-manager">
            <div className="medication-header">
                <div>
                    <h1>Medication Management</h1>
                    <p className="text-muted">Track your medications and check for conflicts</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowForm(true)}>
                    <Plus size={20} />
                    Add Medication
                </button>
            </div>

            {showForm && (
                <div className="medication-form card slide-up">
                    <div className="card-header">
                        <h3>Add New Medication</h3>
                        <button className="close-btn" onClick={() => setShowForm(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Medication Name *</label>
                            <input
                                type="text"
                                placeholder="e.g. Aspirin, Metformin"
                                value={formData.brand_name}
                                onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Dosage</label>
                            <input
                                type="text"
                                placeholder="e.g. 500mg"
                                value={formData.dosage}
                                onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                            />
                        </div>
                        <div className="form-group">
                            <label>Frequency</label>
                            <input
                                type="text"
                                placeholder="e.g. Twice daily"
                                value={formData.frequency}
                                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                            />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            {submitting ? 'Analyzing...' : 'Add & Check Conflicts'}
                        </button>
                    </form>
                </div>
            )}

            {medications.length === 0 ? (
                <div className="empty-state card">
                    <Pill size={64} className="text-muted" />
                    <h2>No Medications Yet</h2>
                    <p className="text-muted">Add your medications to check for interactions and conflicts</p>
                </div>
            ) : (
                <div className="medications-grid grid grid-2">
                    {medications.map((med) => {
                        const validInteractions = med.conflict_data?.drug_interactions?.filter(i => {
                            if (!i.interacting_medication || i.interacting_medication.toLowerCase().includes('none') || i.interacting_medication.toLowerCase().includes('n/a')) return false;

                            const severity = (i.severity || '').toLowerCase();
                            return severity === 'high' || severity === 'critical' || severity === 'major';
                        }) || [];

                        return (
                            <div key={med.id} className="medication-card card">
                                <div className="med-header">
                                    <div>
                                        <h3>{med.brand_name}</h3>
                                        <p className="text-muted">{med.active_molecule || 'Active molecule detected by AI'}</p>
                                        {med.conflict_data?.brief_description && (
                                            <p className="med-description text-muted">
                                                {med.conflict_data.brief_description}
                                            </p>
                                        )}
                                    </div>
                                    <div className="med-actions">
                                        <button className="edit-btn" onClick={() => handleEdit(med)}>
                                            <Edit2 size={18} />
                                        </button>
                                        <button className="delete-btn" onClick={() => handleDelete(med.id)}>
                                            <X size={18} />
                                        </button>
                                    </div>
                                </div>

                                <div className="med-details">
                                    {editingId === med.id ? (
                                        <div className="inline-edit-form">
                                            <div className="edit-group">
                                                <label>Dosage</label>
                                                <input
                                                    type="text"
                                                    value={editData.dosage}
                                                    onChange={(e) => setEditData({ ...editData, dosage: e.target.value })}
                                                    placeholder="e.g. 500mg"
                                                    autoFocus
                                                />
                                            </div>
                                            <div className="edit-group">
                                                <label>Frequency</label>
                                                <input
                                                    type="text"
                                                    value={editData.frequency}
                                                    onChange={(e) => setEditData({ ...editData, frequency: e.target.value })}
                                                    placeholder="e.g. Once daily"
                                                />
                                            </div>
                                            <div className="edit-actions">
                                                <button
                                                    className="save-btn"
                                                    onClick={() => handleUpdateMedication(med.id)}
                                                    disabled={updating}
                                                >
                                                    <Check size={16} /> Save
                                                </button>
                                                <button className="cancel-btn" onClick={handleCancelEdit}>
                                                    <XCircle size={16} /> Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            {med.dosage && <p><strong>Dosage:</strong> {med.dosage}</p>}
                                            {med.frequency && <p><strong>Frequency:</strong> {med.frequency}</p>}
                                        </>
                                    )}
                                </div>

                                {validInteractions.length > 0 && (
                                    <div className="conflict-warning">
                                        <AlertTriangle size={20} />
                                        <div>
                                            <strong>Interactions Detected</strong>
                                            {validInteractions.map((interaction, idx) => (
                                                <div key={idx} className="interaction-item">
                                                    <p className="text-muted">
                                                        <strong>{interaction.interacting_medication}</strong>: <span style={{ textTransform: 'capitalize' }}>{interaction.severity}</span>
                                                    </p>
                                                    {interaction.mechanism && (
                                                        <p className="text-muted" style={{ fontSize: '0.85em', marginTop: '2px', lineHeight: '1.3' }}>
                                                            {interaction.mechanism}
                                                        </p>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    )
}

export default MedicationManager
