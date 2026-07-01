import { CheckCircle, Circle, Loader } from 'lucide-react'
import './ProgressIndicator.css'

const STEPS = [
  { id: 'screenshot', label: 'Capturing Screenshot',      desc: 'Loading page in headless browser' },
  { id: 'cognitive',  label: 'Cognitive Load Analysis',   desc: 'Running OpenCV & wavelet algorithms' },
  { id: 'saliency',   label: 'Visual Hierarchy Analysis', desc: 'Predicting attention with TranSalNet' },
  { id: 'touch',      label: 'Touch Target Evaluation',   desc: 'Extracting DOM & checking WCAG' },
  { id: 'scoring',    label: 'Computing AHP Score',       desc: 'Aggregating weighted results' },
]

/**
 * activeStep: index of the currently running step (0-based)
 * Pass -1 when idle, STEPS.length when complete
 */
export default function ProgressIndicator({ activeStep = 0 }) {
  return (
    <div className="progress-wrap glass-card" role="status" aria-label="Analysis progress">
      <h3 className="section-title" style={{ marginBottom: 24 }}>Analysing your interface…</h3>
      <div className="progress-steps">
        {STEPS.map((step, i) => {
          const done    = i < activeStep
          const active  = i === activeStep
          const pending = i > activeStep

          return (
            <div key={step.id} className={`progress-step ${done ? 'step-done' : active ? 'step-active' : 'step-pending'}`}>
              {/* Connector line */}
              {i < STEPS.length - 1 && (
                <div className={`step-connector ${done ? 'connector-done' : ''}`} />
              )}

              {/* Icon */}
              <div className="step-icon-wrap">
                {done   && <CheckCircle size={22} color="var(--success)" />}
                {active && <Loader size={22} color="var(--accent-primary)" className="animate-spin" />}
                {pending && <Circle size={22} color="var(--text-subtle)" />}
              </div>

              {/* Text */}
              <div className="step-text">
                <span className="step-label">{step.label}</span>
                <span className="step-desc">{step.desc}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Overall progress bar */}
      <div className="overall-bar">
        <div
          className="overall-bar-fill"
          style={{ width: `${Math.round((activeStep / STEPS.length) * 100)}%` }}
        />
      </div>
      <p className="progress-pct">
        {Math.round((activeStep / STEPS.length) * 100)}% complete
      </p>
    </div>
  )
}
