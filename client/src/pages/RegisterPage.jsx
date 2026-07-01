import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Mail, Lock, User, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { register } from '../services/api'
import './AuthPage.css'

function getPasswordStrength(pwd) {
  if (!pwd) return { score: 0, label: '', color: 'transparent' }
  let score = 0
  if (pwd.length >= 8) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[0-9]/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong']
  const colors = ['transparent', 'var(--danger)', 'var(--warning)', '#84cc16', 'var(--success)']
  return { score, label: labels[score], color: colors[score], width: `${score * 25}%` }
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { login: saveAuth } = useAuth()

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [showPwd, setShowPwd] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const strength = getPasswordStrength(form.password)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    setError('')
  }

  const validate = () => {
    if (!form.name.trim() || form.name.trim().length < 2)
      return 'Name must be at least 2 characters.'
    if (!form.email) return 'Email is required.'
    if (form.password.length < 8) return 'Password must be at least 8 characters.'
    if (form.password !== form.confirm) return 'Passwords do not match.'
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationError = validate()
    if (validationError) { setError(validationError); return }

    setLoading(true)
    setError('')
    try {
      const res = await register({ name: form.name, email: form.email, password: form.password })
      saveAuth(res.data.token, res.data.user)
      navigate('/analyze')
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-orb auth-orb-1" />
      <div className="auth-orb auth-orb-2" />

      <div className="auth-card glass-card animate-fadeInUp">
        <div className="auth-header">
          <div className="auth-icon-wrap">
            <UserPlus size={28} color="var(--accent-primary)" />
          </div>
          <h1 className="auth-title">Create account</h1>
          <p className="auth-subtitle">Start analysing your UX for free</p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label">Full name</label>
            <div className="input-wrapper">
              <User size={16} className="input-icon" />
              <input
                id="register-name"
                type="text"
                name="name"
                className="form-input with-icon"
                placeholder="Jane Smith"
                value={form.name}
                onChange={handleChange}
                autoComplete="name"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email address</label>
            <div className="input-wrapper">
              <Mail size={16} className="input-icon" />
              <input
                id="register-email"
                type="email"
                name="email"
                className="form-input with-icon"
                placeholder="jane@example.com"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="input-wrapper">
              <Lock size={16} className="input-icon" />
              <input
                id="register-password"
                type={showPwd ? 'text' : 'password'}
                name="password"
                className="form-input with-icon with-icon-right"
                placeholder="At least 8 characters"
                value={form.password}
                onChange={handleChange}
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                className="toggle-pwd"
                onClick={() => setShowPwd(!showPwd)}
                aria-label={showPwd ? 'Hide password' : 'Show password'}
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {form.password && (
              <div className="pwd-strength">
                <div className="pwd-strength-bar">
                  <div
                    className="pwd-strength-fill"
                    style={{ width: strength.width, background: strength.color }}
                  />
                </div>
                <span className="pwd-strength-label" style={{ color: strength.color }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Confirm password</label>
            <div className="input-wrapper">
              <Lock size={16} className="input-icon" />
              <input
                id="register-confirm"
                type={showPwd ? 'text' : 'password'}
                name="confirm"
                className="form-input with-icon with-icon-right"
                placeholder="Repeat password"
                value={form.confirm}
                onChange={handleChange}
                autoComplete="new-password"
                required
              />
              {form.confirm && (
                <span style={{ position: 'absolute', right: 12 }}>
                  {form.password === form.confirm
                    ? <CheckCircle size={16} color="var(--success)" />
                    : <AlertCircle size={16} color="var(--danger)" />}
                </span>
              )}
            </div>
          </div>

          <button
            id="register-submit"
            type="submit"
            className="btn btn-primary auth-submit"
            disabled={loading}
          >
            {loading ? (
              <><span className="btn-spinner" /> Creating account…</>
            ) : (
              <><UserPlus size={16} /> Create Account</>
            )}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{' '}
          <Link to="/login" className="auth-link">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
