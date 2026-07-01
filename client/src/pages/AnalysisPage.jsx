import { useState, useRef } from 'react'
import { Link2, Upload, X, AlertCircle, Lightbulb, ChevronDown, ChevronUp } from 'lucide-react'
import { startAnalysis } from '../services/api'
import ScoreDashboard from '../components/ScoreDashboard'
import HeatmapOverlay from '../components/HeatmapOverlay'
import ViolationsList from '../components/ViolationsList'
import ProgressIndicator from '../components/ProgressIndicator'
import ReportExporter from '../components/ReportExporter'
import './AnalysisPage.css'

export default function AnalysisPage() {
  const [url, setUrl]               = useState('')
  const [imageFile, setImageFile]   = useState(null)
  const [imagePreview, setPreview]  = useState(null)
  const [dragging, setDragging]     = useState(false)
  const [analyzing, setAnalyzing]   = useState(false)
  const [step, setStep]             = useState(0)
  const [results, setResults]       = useState(null)
  const [error, setError]           = useState('')
  const [showRecs, setShowRecs]     = useState(false)
  const fileRef                     = useRef(null)
  const resultsRef                  = useRef(null)

  /* ── File handling ─────────────────────────────────────────────────── */
  const acceptFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      setError('Please upload a PNG, JPEG, or WebP image.')
      return
    }
    setImageFile(file)
    setPreview(URL.createObjectURL(file))
    setError('')
  }

  const onFileChange = (e) => acceptFile(e.target.files[0])

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false)
    acceptFile(e.dataTransfer.files[0])
  }

  const clearImage = () => {
    setImageFile(null)
    if (imagePreview) URL.revokeObjectURL(imagePreview)
    setPreview(null)
  }

  /* ── Simulate step progression ─────────────────────────────────────── */
  const simulateProgress = () => {
    const delays = [0, 1200, 3000, 5000, 7000]
    delays.forEach((d, i) => setTimeout(() => setStep(i), d))
  }

  /* ── Submit analysis ───────────────────────────────────────────────── */
  const handleAnalyze = async () => {
    if (!url && !imageFile) {
      setError('Please enter a URL or upload a screenshot.')
      return
    }
    if (url && !/^https?:\/\/.+/.test(url)) {
      setError('Please enter a valid URL starting with http:// or https://')
      return
    }

    setAnalyzing(true)
    setResults(null)
    setError('')
    setStep(0)
    simulateProgress()

    const formData = new FormData()
    if (url)       formData.append('url',   url)
    if (imageFile) formData.append('image', imageFile)

    try {
      const res = await startAnalysis(formData)
      setResults(res.data)
      setStep(5)
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    } catch (err) {
      setError(err.response?.data?.error || 'Analysis failed. Please try again.')
      setStep(0)
    } finally {
      setAnalyzing(false)
    }
  }

  /* ── Derived data ─────────────────────────────────────────────────── */
  const violations   = results?.details?.touch?.violations_detail       || []
  const wcagAaRate   = results?.details?.touch?.wcag_aa_compliance_rate  ?? 0
  const wcagAaaRate  = results?.details?.touch?.wcag_aaa_compliance_rate ?? 0
  const totalEl      = results?.details?.touch?.total_interactive_elements ?? 0
  const heatmapB64   = results?.heatmap_base64 || results?.details?.saliency?.heatmap_base64
  const recs         = results?.recommendations || []
  const allRecs      = [
    ...(results?.details?.cognitive?.recommendations || []),
    ...(results?.details?.saliency?.recommendations  || []),
    ...(results?.details?.touch?.recommendations     || []),
    ...recs,
  ].filter((r, i, a) => a.indexOf(r) === i)   // deduplicate

  return (
    <div className="analysis-page">
      <div className="container">

        {/* ── Hero header ─────────────────────────────────────────────── */}
        <div className="analysis-header animate-fadeInUp">
          <h1 className="analysis-title">
            Analyse Your <span className="gradient-text">Interface</span>
          </h1>
          <p className="analysis-subtitle">
            Enter a URL or upload a screenshot — we'll score it across cognitive load,
            visual hierarchy, and touch target compliance.
          </p>
        </div>

        {/* ── Input panel ─────────────────────────────────────────────── */}
        <div className="input-panel glass-card animate-fadeInUp" style={{ animationDelay: '0.1s' }}>

          {/* URL input */}
          <div className="form-group">
            <label className="form-label" htmlFor="analyze-url">
              <Link2 size={14} style={{ display: 'inline', marginRight: 6 }} />
              Website URL
            </label>
            <input
              id="analyze-url"
              type="url"
              className="form-input url-input"
              placeholder="https://example.com"
              value={url}
              onChange={e => { setUrl(e.target.value); setError('') }}
              onKeyDown={e => e.key === 'Enter' && !analyzing && handleAnalyze()}
              disabled={analyzing}
            />
          </div>

          <div className="input-divider">
            <span>or upload a screenshot</span>
          </div>

          {/* Drop zone */}
          {!imagePreview ? (
            <div
              id="drop-zone"
              className={`drop-zone ${dragging ? 'drop-zone-active' : ''}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
              aria-label="Upload screenshot"
            >
              <Upload size={32} color="var(--text-subtle)" />
              <p className="drop-label">Drag & drop a screenshot here</p>
              <p className="drop-sub">PNG, JPEG, WebP · Max 20MB</p>
              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                style={{ display: 'none' }}
                onChange={onFileChange}
              />
            </div>
          ) : (
            <div className="image-preview-wrap">
              <img src={imagePreview} alt="Preview" className="image-preview" />
              <button className="remove-image btn btn-ghost btn-sm" onClick={clearImage} aria-label="Remove image">
                <X size={14} /> Remove
              </button>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="analysis-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* CTA */}
          <button
            id="analyze-btn"
            className="btn btn-primary analyze-btn"
            onClick={handleAnalyze}
            disabled={analyzing || (!url && !imageFile)}
          >
            {analyzing ? (
              <><span className="btn-spinner" /> Analysing…</>
            ) : '🔍 Analyse Now'}
          </button>
        </div>

        {/* ── Progress ─────────────────────────────────────────────────── */}
        {analyzing && (
          <div className="animate-fadeInUp" style={{ animationDelay: '0.05s' }}>
            <ProgressIndicator activeStep={step} />
          </div>
        )}

        {/* ── Results ─────────────────────────────────────────────────── */}
        {results && (
          <div ref={resultsRef} className="results-section animate-fadeInUp">

            {/* Score dashboard */}
            <ScoreDashboard
              scores={results.scores}
              compositeScore={results.composite_score}
              grade={results.grade}
            />

            {/* Heatmap */}
            {heatmapB64 && (
              <HeatmapOverlay
                screenshotBase64={null}
                heatmapBase64={heatmapB64}
              />
            )}

            {/* Violations */}
            <ViolationsList
              violations={violations}
              wcagAaRate={wcagAaRate}
              wcagAaaRate={wcagAaaRate}
              totalElements={totalEl}
            />

            {/* Recommendations */}
            {allRecs.length > 0 && (
              <div className="recs-panel glass-card">
                <button
                  className="recs-toggle"
                  onClick={() => setShowRecs(!showRecs)}
                  aria-expanded={showRecs}
                >
                  <div className="recs-toggle-left">
                    <Lightbulb size={18} color="var(--warning)" />
                    <span className="section-title" style={{ margin: 0 }}>
                      Recommendations ({allRecs.length})
                    </span>
                  </div>
                  {showRecs ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>

                {showRecs && (
                  <ul className="recs-list">
                    {allRecs.map((rec, i) => (
                      <li key={i} className="rec-item">
                        <span className="rec-bullet">→</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Export */}
            <div className="export-row">
              <ReportExporter data={results} />
              {results.errors?.length > 0 && (
                <div className="partial-notice">
                  <AlertCircle size={14} />
                  <span>
                    {results.errors.length} service(s) had errors — partial results shown.
                  </span>
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
