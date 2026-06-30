import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Brain,
  Target,
  Eye,
  ArrowRight,
  Zap,
  Shield,
  TrendingUp,
  CheckCircle,
  Upload,
  Cpu,
  FileText,
  Star,
  ChevronRight,
} from 'lucide-react'
import './HomePage.css'

/* ── Animated score counter ── */
function AnimatedScore({ target, label, color }) {
  const elRef = useRef(null)
  useEffect(() => {
    const el = elRef.current
    if (!el) return
    let start = 0
    const step = () => {
      start = Math.min(start + Math.ceil(target / 40), target)
      el.textContent = start
      if (start < target) requestAnimationFrame(step)
    }
    const timer = setTimeout(() => requestAnimationFrame(step), 400)
    return () => clearTimeout(timer)
  }, [target])
  return (
    <div className="hero-score-card">
      <span ref={elRef} className="hero-score-number" style={{ color }}>0</span>
      <span className="hero-score-label">{label}</span>
    </div>
  )
}

const features = [
  {
    icon: <Brain size={28} />,
    title: 'Cognitive Load',
    subtitle: 'Neural-Based Complexity',
    color: 'var(--accent-primary)',
    colorBg: 'rgba(99,102,241,0.12)',
    metrics: [
      { label: 'Feature Congestion', desc: 'Count of interactive elements per viewport zone' },
      { label: 'Edge Density', desc: 'Sobel-filtered visual noise score' },
      { label: 'Subband Entropy', desc: 'Wavelet-decomposed information entropy' },
    ],
  },
  {
    icon: <Target size={28} />,
    title: 'Touch Target Analysis',
    subtitle: 'WCAG Compliance Engine',
    color: 'var(--accent-cyan)',
    colorBg: 'rgba(34,211,238,0.1)',
    metrics: [
      { label: 'WCAG 2.5.5 (AA)', desc: '44×44 px minimum target size validation' },
      { label: 'WCAG 2.5.8 (AAA)', desc: '24×24 px enhanced spacing requirements' },
      { label: "Fitts's Law Model", desc: 'Acquisition time prediction per target' },
    ],
  },
  {
    icon: <Eye size={28} />,
    title: 'Visual Hierarchy',
    subtitle: 'AI Saliency Mapping',
    color: 'var(--accent-violet)',
    colorBg: 'rgba(167,139,250,0.1)',
    metrics: [
      { label: 'TranSalNet Saliency', desc: 'Transformer-based gaze prediction model' },
      { label: 'Focus Efficiency Score', desc: 'Ratio of key-element saliency to total' },
      { label: 'Visual Flow Analysis', desc: 'Scanpath simulation and entropy mapping' },
    ],
  },
]

const steps = [
  {
    step: '01',
    icon: <Upload size={24} />,
    title: 'Upload or Enter URL',
    desc: 'Paste your website URL or drag-and-drop a screenshot. Our system accepts PNG, JPG, or live URLs.',
    color: 'var(--accent-primary)',
  },
  {
    step: '02',
    icon: <Cpu size={24} />,
    title: 'AI Analysis Engine',
    desc: 'Three specialized ML microservices run in parallel: cognitive load quantification, saliency mapping, and WCAG auditing.',
    color: 'var(--accent-cyan)',
  },
  {
    step: '03',
    icon: <FileText size={24} />,
    title: 'Actionable Report',
    desc: 'Receive a comprehensive PDF report with scored metrics, heatmap overlays, violation details, and prioritized recommendations.',
    color: 'var(--accent-violet)',
  },
]

const mockScores = [
  { label: 'Cognitive Load',    score: 74, grade: 'B', color: 'var(--warning)' },
  { label: 'Visual Hierarchy',  score: 88, grade: 'A', color: 'var(--success)' },
  { label: 'Touch Targets',     score: 52, grade: 'D', color: 'var(--danger)' },
]

export default function HomePage() {
  return (
    <div className="home">
      {/* ════════════════════════════════════════
          HERO SECTION
          ════════════════════════════════════════ */}
      <section className="hero">
        {/* Animated background orbs */}
        <div className="hero__orb hero__orb--1" />
        <div className="hero__orb hero__orb--2" />
        <div className="hero__orb hero__orb--3" />
        <div className="hero__grid" />

        <div className="container hero__inner">
          {/* Pill badge */}
          <div className="hero__badge animate-fadeInUp">
            <Star size={13} fill="currentColor" />
            ML-Powered Heuristic Evaluation
            <ChevronRight size={13} />
          </div>

          {/* Headline */}
          <h1 className="hero__title animate-fadeInUp delay-100">
            AI-Powered UI/UX<br />
            <span className="gradient-text">Heuristic Analysis</span>
          </h1>

          {/* Subtext */}
          <p className="hero__subtitle animate-fadeInUp delay-200">
            Objectively quantify your design quality using Computer Vision,
            Deep Learning, and Mathematical Layout Analysis — powered by
            three specialized ML microservices.
          </p>

          {/* CTAs */}
          <div className="hero__ctas animate-fadeInUp delay-300">
            <Link to="/analyze" className="btn btn-primary btn-lg hero__cta-primary">
              <Zap size={18} />
              Start Free Analysis
              <ArrowRight size={16} />
            </Link>
            <a
              href="#features"
              className="btn btn-secondary btn-lg"
            >
              <Eye size={18} />
              Explore Features
            </a>
          </div>

          {/* Floating tags */}
          <div className="hero__tags animate-fadeInUp delay-400">
            {['Computer Vision', 'Deep Learning', 'WCAG Compliance', 'AHP Scoring', 'PDF Reports'].map(
              (tag) => (
                <span key={tag} className="hero__tag">
                  <CheckCircle size={12} />
                  {tag}
                </span>
              )
            )}
          </div>

          {/* Score preview cards */}
          <div className="hero__scores animate-fadeInUp delay-500">
            <AnimatedScore target={71} label="Composite Score" color="var(--warning)" />
            <AnimatedScore target={88} label="Visual Hierarchy" color="var(--success)" />
            <AnimatedScore target={52} label="Touch Targets"   color="var(--danger)" />
          </div>
        </div>

        {/* Scroll hint */}
        <div className="hero__scroll-hint">
          <div className="hero__scroll-dot" />
        </div>
      </section>

      {/* ════════════════════════════════════════
          FEATURES SECTION
          ════════════════════════════════════════ */}
      <section className="home-section home-section--features" id="features">
        <div className="container">
          <div className="section-header">
            <span className="section-eyebrow">Evaluation Modules</span>
            <h2 className="section-title">
              Three-Axis Heuristic <span className="gradient-text">Analysis Engine</span>
            </h2>
            <p className="section-subtitle">
              Each module applies a distinct ML methodology. Scores are aggregated
              using the Analytic Hierarchy Process (AHP) into a single composite metric.
            </p>
          </div>

          <div className="features-grid">
            {features.map((f, i) => (
              <div
                key={f.title}
                className="feature-card glass-card animate-fadeInUp"
                style={{ animationDelay: `${i * 0.15}s` }}
              >
                <div className="feature-card__icon" style={{ background: f.colorBg, color: f.color }}>
                  {f.icon}
                </div>
                <h3 className="feature-card__title">{f.title}</h3>
                <p className="feature-card__subtitle">{f.subtitle}</p>
                <ul className="feature-card__metrics">
                  {f.metrics.map((m) => (
                    <li key={m.label} className="feature-metric">
                      <div className="feature-metric__dot" style={{ background: f.color }} />
                      <div>
                        <span className="feature-metric__label">{m.label}</span>
                        <span className="feature-metric__desc">{m.desc}</span>
                      </div>
                    </li>
                  ))}
                </ul>
                <Link to="/analyze" className="btn btn-ghost btn-sm feature-card__cta" style={{ color: f.color }}>
                  Analyze Now <ArrowRight size={14} />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          SCORE PREVIEW (Mockup)
          ════════════════════════════════════════ */}
      <section className="home-section home-section--scores" id="scores">
        <div className="container">
          <div className="section-header">
            <span className="section-eyebrow">Sample Output</span>
            <h2 className="section-title">
              Comprehensive Score <span className="gradient-text">Dashboard</span>
            </h2>
            <p className="section-subtitle">
              Every analysis produces a rich visual report with detailed breakdowns
              and actionable improvement recommendations.
            </p>
          </div>

          <div className="score-preview">
            {/* Big composite ring mockup */}
            <div className="score-preview__ring glass-card">
              <div className="score-ring-container">
                <svg viewBox="0 0 120 120" className="score-ring-svg">
                  <circle cx="60" cy="60" r="54" className="score-ring-bg" />
                  <circle
                    cx="60"
                    cy="60"
                    r="54"
                    className="score-ring-fill"
                    style={{ stroke: 'var(--warning)', strokeDasharray: '339', strokeDashoffset: '97' }}
                  />
                </svg>
                <div className="score-ring-label">
                  <span className="score-ring-number" style={{ color: 'var(--warning)' }}>71</span>
                  <span className="score-ring-sub">/ 100</span>
                  <span className="badge badge-warning badge-lg" style={{ marginTop: 8 }}>Grade B</span>
                </div>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', marginTop: 8 }}>
                Composite AHP Score
              </p>
            </div>

            {/* Sub-score cards */}
            <div className="score-preview__cards">
              {mockScores.map((s) => (
                <div key={s.label} className="score-mini-card glass-card">
                  <div className="score-mini-card__header">
                    <span className="score-mini-card__label">{s.label}</span>
                    <span className="badge" style={{
                      background: `${s.color}20`,
                      color: s.color,
                      border: `1px solid ${s.color}40`,
                    }}>
                      {s.grade}
                    </span>
                  </div>
                  <span className="score-mini-card__number" style={{ color: s.color }}>
                    {s.score}
                  </span>
                  <div className="progress-bar-wrapper" style={{ marginTop: 8 }}>
                    <div
                      className={`progress-bar-fill ${s.score >= 80 ? 'high' : s.score >= 55 ? 'medium' : 'low'}`}
                      style={{ width: `${s.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          HOW IT WORKS
          ════════════════════════════════════════ */}
      <section className="home-section home-section--how" id="how">
        <div className="container">
          <div className="section-header">
            <span className="section-eyebrow">Process</span>
            <h2 className="section-title">
              How <span className="gradient-text">It Works</span>
            </h2>
            <p className="section-subtitle">
              Three simple steps to receive a comprehensive UI/UX heuristic evaluation.
            </p>
          </div>

          <div className="steps-grid">
            {steps.map((s, i) => (
              <div key={s.step} className="step-card animate-fadeInUp" style={{ animationDelay: `${i * 0.15}s` }}>
                {i < steps.length - 1 && <div className="step-connector" />}
                <div className="step-card__badge" style={{ background: s.color }}>
                  {s.icon}
                </div>
                <div className="step-card__number">{s.step}</div>
                <h3 className="step-card__title">{s.title}</h3>
                <p className="step-card__desc">{s.desc}</p>
              </div>
            ))}
          </div>

          <div className="steps-cta animate-fadeInUp delay-400">
            <Link to="/analyze" className="btn btn-primary btn-lg">
              <Zap size={18} />
              Start Your Free Analysis
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          FOOTER
          ════════════════════════════════════════ */}
      <footer className="home-footer">
        <div className="container home-footer__inner">
          <div className="home-footer__brand">
            <div className="navbar__logo-icon" style={{ width: 32, height: 32 }}>
              <Zap size={16} />
            </div>
            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1.1rem' }}>
              UX<span className="gradient-text">Lens</span>
            </span>
          </div>
          <p className="home-footer__copy">
            © {new Date().getFullYear()} UXLens — ML-Driven UI/UX Heuristic Evaluation System.
            Built with Computer Vision &amp; Deep Learning.
          </p>
          <div className="home-footer__links">
            <Link to="/analyze" className="home-footer__link">Analyze</Link>
            <Link to="/reports" className="home-footer__link">Reports</Link>
            <Link to="/login"   className="home-footer__link">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
