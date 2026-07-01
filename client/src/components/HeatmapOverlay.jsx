import { useEffect, useRef, useState } from 'react'
import { Eye, EyeOff, SlidersHorizontal } from 'lucide-react'
import './HeatmapOverlay.css'

/**
 * Renders the original screenshot with the saliency heatmap overlaid on an
 * HTML5 Canvas element. The user can control opacity via a slider and toggle
 * the overlay on/off.
 */
export default function HeatmapOverlay({ screenshotBase64, heatmapBase64 }) {
  const canvasRef   = useRef(null)
  const [opacity, setOpacity]     = useState(55)   // 0-100
  const [showOverlay, setShowOverlay] = useState(true)
  const [loaded, setLoaded]       = useState(false)

  // Redraw whenever opacity, showOverlay, or images change
  useEffect(() => {
    if (!screenshotBase64 && !heatmapBase64) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const bg = new Image()
    const prefix = (src) =>
      src.startsWith('data:') ? src : `data:image/png;base64,${src}`

    bg.onload = () => {
      canvas.width  = bg.naturalWidth
      canvas.height = bg.naturalHeight
      ctx.drawImage(bg, 0, 0)
      setLoaded(true)

      if (heatmapBase64 && showOverlay) {
        const overlay = new Image()
        overlay.onload = () => {
          ctx.globalAlpha = opacity / 100
          ctx.drawImage(overlay, 0, 0, canvas.width, canvas.height)
          ctx.globalAlpha = 1
        }
        overlay.src = prefix(heatmapBase64)
      }
    }
    bg.src = screenshotBase64
      ? prefix(screenshotBase64)
      : `data:image/png;base64,${heatmapBase64}` // fallback: show heatmap alone
  }, [screenshotBase64, heatmapBase64, opacity, showOverlay])

  if (!screenshotBase64 && !heatmapBase64) {
    return (
      <div className="heatmap-placeholder glass-card">
        <Eye size={40} color="var(--text-subtle)" />
        <p>No saliency data available</p>
      </div>
    )
  }

  return (
    <div className="heatmap-wrap glass-card">
      <div className="heatmap-toolbar">
        <h3 className="section-title" style={{ margin: 0 }}>Saliency Heatmap</h3>
        <div className="heatmap-controls">
          {/* Opacity slider */}
          <div className="opacity-control">
            <SlidersHorizontal size={14} color="var(--text-subtle)" />
            <input
              id="heatmap-opacity"
              type="range"
              min={0}
              max={100}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              className="opacity-slider"
              aria-label="Heatmap opacity"
            />
            <span className="opacity-label">{opacity}%</span>
          </div>

          {/* Toggle overlay */}
          <button
            id="heatmap-toggle"
            className={`btn btn-sm ${showOverlay ? 'btn-secondary' : 'btn-ghost'}`}
            onClick={() => setShowOverlay(!showOverlay)}
            aria-pressed={showOverlay}
          >
            {showOverlay ? <Eye size={14} /> : <EyeOff size={14} />}
            {showOverlay ? 'Overlay On' : 'Overlay Off'}
          </button>
        </div>
      </div>

      <div className="canvas-container">
        {!loaded && <div className="skeleton canvas-skeleton" />}
        <canvas
          ref={canvasRef}
          className="heatmap-canvas"
          style={{ opacity: loaded ? 1 : 0 }}
          aria-label="Saliency heatmap overlay"
        />
      </div>

      <div className="heatmap-legend">
        <span className="legend-label">Low attention</span>
        <div className="legend-gradient" />
        <span className="legend-label">High attention</span>
      </div>
    </div>
  )
}
