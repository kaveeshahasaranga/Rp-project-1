import { useEffect, useState } from 'react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip
} from 'recharts'
import { Brain, Eye, MousePointer, Award } from 'lucide-react'
import './ScoreDashboard.css'

/** Return severity class + label based on 0-100 score */
function severity(score) {
  if (score >= 80) return { cls: 'score-high',   badge: 'badge-success', label: 'Excellent' }
  if (score >= 55) return { cls: 'score-medium',  badge: 'badge-warning', label: 'Moderate'  }
  return              { cls: 'score-low',    badge: 'badge-danger',  label: 'Needs Work' }
}

/** Animated count-up hook */
function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!target && target !== 0) return
    let start = 0
    const step = target / (duration / 16)
    const timer = setInterval(() => {
      start = Math.min(start + step, target)
      setValue(Math.round(start))
      if (start >= target) clearInterval(timer)
    }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return value
}

/** Grade colour map */
const GRADE_COLOR = { A: '#22c55e', B: '#84cc16', C: '#f59e0b', D: '#f97316', F: '#ef4444' }

const METRIC_CARDS = [
  { key: 'cognitive_load',   label: 'Cognitive Load',    Icon: Brain,         desc: 'Visual complexity & clutter level' },
  { key: 'visual_hierarchy', label: 'Visual Hierarchy',  Icon: Eye,           desc: 'Attention prediction & focus score' },
  { key: 'touch_target',     label: 'Touch Targets',     Icon: MousePointer,  desc: 'WCAG compliance & Fitts\'s Law' },
]

/** Individual metric card — extracted so useCountUp hook is at top level */
function MetricCard({ metricKey, label, Icon, desc, scores }) {
  const val = Math.round(scores[metricKey] ?? 0)
  const { cls, badge, label: sevLabel } = severity(val)
  const animated = useCountUp(val)
  return (
    <div className="metric-card glass-card">
      <div className="metric-card-header">
        <div className="metric-icon-wrap">
          <Icon size={20} color="var(--accent-primary)" />
        </div>
        <span className={`badge ${badge}`}>{sevLabel}</span>
      </div>
      <div className={`metric-score ${cls}`}>{animated}</div>
      <div className="metric-bar-wrap">
        <div className="metric-bar">
          <div
            className="metric-bar-fill"
            style={{ width: `${val}%`, background: val >= 80 ? 'var(--success)' : val >= 55 ? 'var(--warning)' : 'var(--danger)' }}
          />
        </div>
      </div>
      <p className="metric-label">{label}</p>
      <p className="metric-desc">{desc}</p>
    </div>
  )
}

export default function ScoreDashboard({ scores = {}, compositeScore = 0, grade = 'F' }) {
  const animatedComposite = useCountUp(compositeScore)
  const { cls: compositeClass } = severity(compositeScore)

  const radarData = METRIC_CARDS.map(({ key, label }) => ({
    metric: label,
    value: Math.round(scores[key] ?? 0),
    fullMark: 100
  }))

  const gradeColor = GRADE_COLOR[grade] || '#ef4444'
  const circumference = 2 * Math.PI * 54   // r=54
  const strokeDashoffset = circumference - (compositeScore / 100) * circumference

  return (
    <div className="score-dashboard">
      {/* ── Composite Score Hero ─────────────────────────────────────── */}
      <div className="composite-hero glass-card">
        <div className="composite-ring-wrap">
          <svg className="composite-ring" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54" className="ring-track" />
            <circle
              cx="60" cy="60" r="54"
              className="ring-fill"
              style={{
                stroke: gradeColor,
                strokeDasharray: circumference,
                strokeDashoffset,
                filter: `drop-shadow(0 0 8px ${gradeColor}60)`
              }}
            />
          </svg>
          <div className="composite-inner">
            <span className={`composite-number ${compositeClass}`}>{animatedComposite}</span>
            <span className="composite-denom">/100</span>
          </div>
        </div>

        <div className="composite-meta">
          <div className="grade-badge" style={{ color: gradeColor, borderColor: `${gradeColor}40`, background: `${gradeColor}12` }}>
            <Award size={16} />
            Grade {grade}
          </div>
          <h2 className="composite-label">Overall UX Score</h2>
          <p className="composite-hint">
            Weighted AHP composite · CR = 0.009
          </p>
        </div>
      </div>

      {/* ── 3 Metric Cards ───────────────────────────────────────────── */}
      <div className="metric-cards">
        {METRIC_CARDS.map(({ key, label, Icon, desc }) => (
          <MetricCard key={key} metricKey={key} label={label} Icon={Icon} desc={desc} scores={scores} />
        ))}
      </div>

      {/* ── Radar Chart ──────────────────────────────────────────────── */}
      <div className="radar-wrap glass-card">
        <h3 className="section-title">Score Breakdown</h3>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
            <PolarGrid stroke="rgba(99,102,241,0.2)" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: '#94a3b8', fontSize: 13, fontFamily: 'Inter' }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fill: '#475569', fontSize: 11 }}
              tickCount={5}
            />
            <Radar
              name="UX Score"
              dataKey="value"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.35}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{
                background: '#1e293b',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: 10,
                color: '#f1f5f9',
                fontSize: 13
              }}
              formatter={(val) => [`${val}/100`, 'Score']}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
