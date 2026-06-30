import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('ux_token') || null)
  const [loading, setLoading] = useState(true)

  // Set / remove axios default auth header whenever token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete api.defaults.headers.common['Authorization']
    }
  }, [token])

  // On mount: if we have a stored token, restore user from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('ux_token')
    const storedUser  = localStorage.getItem('ux_user')

    if (storedToken && storedUser) {
      try {
        const parsed = JSON.parse(storedUser)
        setToken(storedToken)
        setUser(parsed)
      } catch {
        localStorage.removeItem('ux_token')
        localStorage.removeItem('ux_user')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback((newToken, newUser) => {
    localStorage.setItem('ux_token', newToken)
    localStorage.setItem('ux_user', JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('ux_token')
    localStorage.removeItem('ux_user')
    setToken(null)
    setUser(null)
  }, [])

  const updateUser = useCallback((updatedUser) => {
    localStorage.setItem('ux_user', JSON.stringify(updatedUser))
    setUser(updatedUser)
  }, [])

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token,
    login,
    logout,
    updateUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}

export default AuthContext
