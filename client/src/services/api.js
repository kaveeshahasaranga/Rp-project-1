import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ── Request interceptor: auto-attach JWT ──────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ux_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor: handle 401 globally ────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear stale credentials
      localStorage.removeItem('ux_token')
      localStorage.removeItem('ux_user')
      // Only redirect if not already on auth pages
      if (!window.location.pathname.includes('/login') &&
          !window.location.pathname.includes('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────────────────────────────────────────
// AUTH ENDPOINTS
// ─────────────────────────────────────────────────────────────────────────────

/** POST /api/auth/login — { email, password } */
export const login = (data) => api.post('/auth/login', data)

/** POST /api/auth/register — { name, email, password } */
export const register = (data) => api.post('/auth/register', data)

/** GET /api/auth/me — returns current user from JWT */
export const getMe = () => api.get('/auth/me')

// ─────────────────────────────────────────────────────────────────────────────
// ANALYSIS ENDPOINTS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * POST /api/analyze
 * Accepts FormData with optional fields:
 *   - url       (string)
 *   - screenshot (File — PNG/JPG)
 *
 * Returns full analysis payload including cognitiveLoad, visualHierarchy,
 * touchTargets, compositeScore, heatmapBase64, violations, recommendations
 */
export const startAnalysis = (formData) =>
  api.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000, // 3 minutes — ML analysis can be slow
  })

// ─────────────────────────────────────────────────────────────────────────────
// REPORT ENDPOINTS
// ─────────────────────────────────────────────────────────────────────────────

/** GET /api/reports — list all reports for current user */
export const getReports = () => api.get('/reports')

/** GET /api/reports/:id — get single report by ID */
export const getReport = (id) => api.get(`/reports/${id}`)

/** DELETE /api/reports/:id — delete a report */
export const deleteReport = (id) => api.delete(`/reports/${id}`)

/** GET /api/reports/export/:id — export report as PDF blob */
export const exportReport = (id) =>
  api.get(`/reports/export/${id}`, { responseType: 'blob' })

export default api
