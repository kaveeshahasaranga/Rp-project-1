import { useState, useEffect } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  Scan,
  BarChart3,
  Home,
  LogIn,
  UserPlus,
  LogOut,
  Menu,
  X,
  ChevronDown,
  User,
} from 'lucide-react'
import './Navbar.css'

function getInitials(name = '') {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [scrolled, setScrolled]       = useState(false)
  const [mobileOpen, setMobileOpen]   = useState(false)
  const [dropdownOpen, setDropdown]   = useState(false)

  // Shadow on scroll
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false)
    setDropdown(false)
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navLinks = [
    { to: '/',        label: 'Home',     icon: <Home size={16} /> },
    { to: '/analyze', label: 'Analyze',  icon: <Scan size={16} /> },
    { to: '/reports', label: 'Reports',  icon: <BarChart3 size={16} /> },
  ]

  return (
    <header className={`navbar${scrolled ? ' navbar--scrolled' : ''}`}>
      <div className="navbar__inner container">
        {/* ── LOGO ── */}
        <NavLink to="/" className="navbar__logo">
          <div className="navbar__logo-icon">
            <Scan size={20} strokeWidth={2.5} />
          </div>
          <span className="navbar__logo-text">
            UX<span className="gradient-text">Lens</span>
          </span>
        </NavLink>

        {/* ── DESKTOP NAV ── */}
        <nav className="navbar__links" aria-label="Main navigation">
          {navLinks.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `navbar__link${isActive ? ' navbar__link--active' : ''}`
              }
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </nav>

        {/* ── RIGHT ACTIONS ── */}
        <div className="navbar__actions">
          {isAuthenticated ? (
            <div className="navbar__user">
              <button
                className="navbar__avatar-btn"
                onClick={() => setDropdown((v) => !v)}
                aria-expanded={dropdownOpen}
                aria-label="User menu"
              >
                <div className="navbar__avatar">
                  {getInitials(user?.name || user?.email)}
                </div>
                <span className="navbar__user-name">{user?.name || 'User'}</span>
                <ChevronDown
                  size={14}
                  className={`navbar__chevron${dropdownOpen ? ' navbar__chevron--open' : ''}`}
                />
              </button>

              {dropdownOpen && (
                <div className="navbar__dropdown">
                  <div className="navbar__dropdown-header">
                    <div className="navbar__avatar navbar__avatar--lg">
                      {getInitials(user?.name || user?.email)}
                    </div>
                    <div>
                      <p className="navbar__dropdown-name">{user?.name}</p>
                      <p className="navbar__dropdown-email">{user?.email}</p>
                    </div>
                  </div>
                  <hr className="divider" style={{ margin: '8px 0' }} />
                  <NavLink to="/reports" className="navbar__dropdown-item">
                    <BarChart3 size={14} />
                    My Reports
                  </NavLink>
                  <button
                    className="navbar__dropdown-item navbar__dropdown-item--danger"
                    onClick={handleLogout}
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="navbar__auth">
              <NavLink to="/login" className="btn btn-ghost btn-sm">
                <LogIn size={15} />
                Sign In
              </NavLink>
              <NavLink to="/register" className="btn btn-primary btn-sm">
                <UserPlus size={15} />
                Get Started
              </NavLink>
            </div>
          )}

          {/* ── HAMBURGER ── */}
          <button
            className="navbar__hamburger"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle mobile menu"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* ── MOBILE MENU ── */}
      <div className={`navbar__mobile${mobileOpen ? ' navbar__mobile--open' : ''}`}>
        <nav className="navbar__mobile-links">
          {navLinks.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `navbar__mobile-link${isActive ? ' navbar__mobile-link--active' : ''}`
              }
            >
              {icon}
              {label}
            </NavLink>
          ))}

          <hr className="divider" style={{ margin: '8px 0' }} />

          {isAuthenticated ? (
            <>
              <div className="navbar__mobile-user">
                <div className="navbar__avatar">{getInitials(user?.name)}</div>
                <div>
                  <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>{user?.name}</p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{user?.email}</p>
                </div>
              </div>
              <button
                className="navbar__mobile-link navbar__mobile-link--danger"
                onClick={handleLogout}
              >
                <LogOut size={16} />
                Sign Out
              </button>
            </>
          ) : (
            <div className="navbar__mobile-auth">
              <NavLink to="/login" className="btn btn-secondary btn-full">
                <LogIn size={15} />
                Sign In
              </NavLink>
              <NavLink to="/register" className="btn btn-primary btn-full">
                <UserPlus size={15} />
                Get Started
              </NavLink>
            </div>
          )}
        </nav>
      </div>

      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="navbar__backdrop"
          onClick={() => setMobileOpen(false)}
        />
      )}
    </header>
  )
}
