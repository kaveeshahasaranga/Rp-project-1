import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReports, deleteReport } from '../services/api'
import { FileText, Trash2, ExternalLink, AlertCircle, Plus } from 'lucide-react'
import ReportExporter from '../components/ReportExporter'
import './ReportPage.css'

const GRADE_COLOR = { A: '#22c55e', B: '#84cc16', C: '#f59e0b', D: '#f97316', F: '#ef4444' }

function ScoreBadge({ score }) {
  const color = score >= 80 ? 'var(--success)' : score >= 55 ? 'var(--warning)' : 'var(--danger)'
  return (
    <span className="score-badge" style={{ color, borderColor: `${color}30`, background: `${color}10` }}>
      {Math.round(score)}/100
    </span>
  )
}

export default function ReportPage() {
  const [reports, setReports]     = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [selected, setSelected]   = useState(null)   // expanded report
  const [deleting, setDeleting]   = useState(null)   // id being deleted

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const res = await getReports()
      setReports(res.data.reports || [])
    } catch {
      setError('Failed to load reports. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Delete this report permanently?')) return
    setDeleting(id)
    try {
      await deleteReport(id)
      setReports(r => r.filter(rep => rep._id !== id))
      if (selected?._id === id) setSelected(null)
    } catch {
      setError('Delete failed. Please try again.')
    } finally {
      setDeleting(null)
    }
  }

  const formatDate = (iso) => new Date(iso).toLocaleString(undefined, {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })

  /* ─── Loading skeleton ────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="report-page">
        <div className="container">
          <h1 className="report-page-title">Your Audit Reports</h1>
          <div className="reports-grid">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="report-card-skeleton glass-card skeleton" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  /* ─── Empty state ─────────────────────────────────────────────────── */
  if (!reports.length) {
    return (
      <div className="report-page">
        <div className="container">
          <div className="reports-empty glass-card">
            <FileText size={52} color="var(--text-subtle)" />
            <h2>No reports yet</h2>
            <p>Run your first UI/UX analysis to generate a report.</p>
            <Link to="/analyze" className="btn btn-primary">
              <Plus size={16} /> Start an Analysis
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="report-page">
      <div className="container">
        <div className="report-page-header">
          <h1 className="report-page-title">Your Audit Reports</h1>
          <Link to="/analyze" className="btn btn-primary">
            <Plus size={16} /> New Analysis
          </Link>
        </div>

        {error && (
          <div className="analysis-error" style={{ marginBottom: 20 }}>
            <AlertCircle size={16} /><span>{error}</span>
          </div>
        )}

        <div className="reports-grid">
          {reports.map(rep => (
            <div
              key={rep._id}
              id={`report-card-${rep._id}`}
              className={`report-card glass-card ${selected?._id === rep._id ? 'report-card-active' : ''}`}
              onClick={() => setSelected(selected?._id === rep._id ? null : rep)}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && setSelected(selected?._id === rep._id ? null : rep)}
            >
              <div className="report-card-top">
                <div className="report-grade" style={{ color: GRADE_COLOR[rep.grade] || '#ef4444' }}>
                  {rep.grade}
                </div>
                <div className="report-meta">
                  <span className="report-url" title={rep.url}>{rep.url}</span>
                  <span className="report-date">{formatDate(rep.createdAt)}</span>
                </div>
                <div className="report-actions">
                  <button
                    className="btn btn-ghost btn-sm report-delete"
                    onClick={e => handleDelete(rep._id, e)}
                    disabled={deleting === rep._id}
                    aria-label="Delete report"
                  >
                    {deleting === rep._id
                      ? <span className="btn-spinner" style={{ width: 12, height: 12 }} />
                      : <Trash2 size={14} />}
                  </button>
                </div>
              </div>

              <div className="report-scores">
                <ScoreBadge score={rep.composite_score} />
                {rep.scores && (
                  <>
                    <span className="score-breakdown-item">
                      CL: <strong>{Math.round(rep.scores.cognitive_load ?? 0)}</strong>
                    </span>
                    <span className="score-breakdown-item">
                      VH: <strong>{Math.round(rep.scores.visual_hierarchy ?? 0)}</strong>
                    </span>
                    <span className="score-breakdown-item">
                      TT: <strong>{Math.round(rep.scores.touch_target ?? 0)}</strong>
                    </span>
                  </>
                )}
              </div>

              {/* Expanded view */}
              {selected?._id === rep._id && (
                <div className="report-expanded" onClick={e => e.stopPropagation()}>
                  {rep.recommendations?.length > 0 && (
                    <div className="expanded-recs">
                      <p className="expanded-label">Recommendations</p>
                      <ul className="mini-recs">
                        {rep.recommendations.slice(0, 4).map((r, i) => (
                          <li key={i}><span className="rec-bullet">→</span>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="expanded-actions">
                    <ReportExporter data={rep} />
                    <a
                      href={rep.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-ghost btn-sm"
                    >
                      <ExternalLink size={14} /> Open Site
                    </a>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
