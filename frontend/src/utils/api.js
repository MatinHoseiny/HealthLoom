import axios from 'axios'

// API Base URL - will use Vite proxy in development
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// ==================================================
// User API
// ==================================================

export const createUser = async (userData) => {
    const response = await api.post('/users', userData)
    return response.data
}

export const getCurrentUser = async (userId) => {
    const response = await api.get(`/users/${userId}`)
    return response.data
}

export const updateUser = async (userId, userData) => {
    const response = await api.put(`/users/${userId}`, userData)
    return response.data
}

// ==================================================
// Upload API
// ==================================================

export const uploadDocument = async (userId, file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', userId)

    const response = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
            if (onProgress) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                onProgress(percentCompleted)
            }
        },
    })
    return response.data
}

export const getUploadHistory = async (userId) => {
    const response = await api.get(`/upload/history/${userId}`)
    return response.data
}

export const getUploadDetails = async (userId, filePath) => {
    const response = await api.get(`/upload/details/${userId}`, {
        params: { file_path: filePath }
    })
    return response.data
}

export const deleteUpload = async (userId, filePath) => {
    const response = await api.delete(`/upload/history/${userId}`, {
        params: { file_path: filePath }
    })
    return response.data
}

// ==================================================
// Chat API
// ==================================================

export const sendChatMessage = async (userId, message, includeContext = true) => {
    const response = await api.post('/chat', {
        user_id: userId,
        message,
        include_context: includeContext,
    })
    return response.data
}

export const getChatHistory = async (userId, limit = 50) => {
    const response = await api.get(`/chat/history/${userId}`, {
        params: { limit },
    })
    return response.data
}

// ==================================================
// Medications API
// ==================================================

export const addMedication = async (medicationData) => {
    const response = await api.post('/medications', medicationData)
    return response.data
}

export const getUserMedications = async (userId, activeOnly = true) => {
    const response = await api.get(`/medications/${userId}`, {
        params: { active_only: activeOnly },
    })
    return response.data
}

export const updateMedication = async (medicationId, updates) => {
    const response = await api.put(`/medications/${medicationId}`, updates)
    return response.data
}

export const deleteMedication = async (medicationId) => {
    const response = await api.delete(`/medications/${medicationId}`)
    return response.data
}

// ==================================================
// Health Data API
// ==================================================

export const getUserTests = async (userId, filters = {}) => {
    const response = await api.get(`/health/tests/${userId}`, {
        params: filters,
    })
    return response.data
}

export const getTestsGrouped = async (userId) => {
    const response = await api.get(`/health/tests/grouped/${userId}`)
    return response.data
}

export const getTestTrend = async (userId, testType, days = 365) => {
    const response = await api.get(`/health/trends/${userId}/${testType}`, {
        params: { days },
    })
    return response.data
}

export const getDashboardData = async (userId) => {
    const response = await api.get(`/health/dashboard/${userId}`)
    return response.data
}

export const getUserPreferences = async (userId) => {
    const response = await api.get(`/users/${userId}/preferences`)
    return response.data
}

export const updateUserPreferences = async (userId, preferences) => {
    const response = await api.put(`/users/${userId}/preferences`, preferences)
    return response.data
}

// ==================================================
// Error Handling
// ==================================================

api.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred'
        console.error('API Error:', message)
        throw new Error(message)
    }
)

export default api
