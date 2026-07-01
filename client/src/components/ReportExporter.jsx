import { Document, Page, Text, View, Image, StyleSheet, pdf, Font } from '@react-pdf/renderer'
import { Download } from 'lucide-react'
import { useState } from 'react'

// ── PDF Styles ────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  page:       { padding: 40, fontFamily: 'Helvetica', backgroundColor: '#ffffff' },
  // Cover
  coverBand:  { backgroundColor: '#6366f1', padding: '32 40', marginBottom: 32, marginHorizontal: -40, marginTop: -40 },
  coverTitle: { fontSize: 26, fontFamily: 'Helvetica-Bold', color: '#ffffff', marginBottom: 6 },
  coverSub:   { fontSize: 11, color: 'rgba(255,255,255,0.75)' },
  coverMeta:  { fontSize: 10, color: 'rgba(255,255,255,0.6)', marginTop: 4 },

  // Section
  section:    { marginBottom: 24 },
  sectionHead:{ fontSize: 13, fontFamily: 'Helvetica-Bold', color: '#1e293b', marginBottom: 10,
                borderBottomWidth: 1, borderBottomColor: '#e2e8f0', paddingBottom: 6 },

  // Score block
  scoreRow:   { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  scoreBig:   { fontSize: 52, fontFamily: 'Helvetica-Bold', color: '#6366f1', marginRight: 20 },
  scoreLabel: { fontSize: 11, color: '#64748b' },
  gradeBadge: { backgroundColor: '#ede9fe', color: '#6366f1', fontSize: 14, fontFamily: 'Helvetica-Bold',
                paddingVertical: 4, paddingHorizontal: 12, borderRadius: 20, alignSelf: 'flex-start', marginTop: 6 },

  // Sub-score table
  table:      { width: '100%' },
  tableHead:  { flexDirection: 'row', backgroundColor: '#f8fafc', paddingVertical: 8, paddingHorizontal: 12, borderRadius: 6 },
  tableRow:   { flexDirection: 'row', paddingVertical: 8, paddingHorizontal: 12, borderBottomWidth: 1, borderBottomColor: '#f1f5f9' },
  colName:    { flex: 2, fontSize: 10 },
  colVal:     { flex: 1, fontSize: 10, textAlign: 'right' },
  colHead:    { fontFamily: 'Helvetica-Bold', fontSize: 10, color: '#64748b', textTransform: 'uppercase' },

  // Heatmap
  heatmapImg: { width: '100%', borderRadius: 8, marginTop: 8 },

  // Recommendations
  recItem:    { flexDirection: 'row', gap: 8, marginBottom: 8 },
  bullet:     { fontSize: 10, color: '#6366f1', marginTop: 1 },
  recText:    { fontSize: 10, color: '#334155', flex: 1, lineHeight: 1.5 },

  // Footer
  footer:     { position: 'absolute', bottom: 30, left: 40, right: 40, textAlign: 'center',
                fontSize: 9, color: '#94a3b8', borderTopWidth: 1, borderTopColor: '#e2e8f0', paddingTop: 10 },
})

// ── Score colour helper ───────────────────────────────────────────────────────
function scoreColor(s) {
  return s >= 80 ? '#22c55e' : s >= 55 ? '#f59e0b' : '#ef4444'
}

// ── PDF Document component ────────────────────────────────────────────────────
function UXReportDocument({ data }) {
  const { url, composite_score, grade, scores = {}, details = {}, heatmap_base64, recommendations = [], timestamp } = data

  const metricRows = [
    { label: 'Cognitive Load',    key: 'cognitive_load',   weight: '54.0%' },
    { label: 'Visual Hierarchy',  key: 'visual_hierarchy', weight: '29.7%' },
    { label: 'Touch Targets',     key: 'touch_target',     weight: '16.3%' },
  ]

  const violations = details?.touch?.violations_detail || []

  return (
    <Document title="UX Lens Audit Report" author="UX Lens">
      <Page size="A4" style={styles.page}>

        {/* Cover band */}
        <View style={styles.coverBand}>
          <Text style={styles.coverTitle}>UX Lens — Audit Report</Text>
          <Text style={styles.coverSub}>{url}</Text>
          <Text style={styles.coverMeta}>Generated: {new Date(timestamp || Date.now()).toLocaleString()}</Text>
        </View>

        {/* Composite Score */}
        <View style={styles.section}>
          <Text style={styles.sectionHead}>Overall UX Score</Text>
          <View style={styles.scoreRow}>
            <Text style={[styles.scoreBig, { color: scoreColor(composite_score) }]}>
              {Math.round(composite_score)}
            </Text>
            <View>
              <Text style={styles.scoreLabel}>out of 100</Text>
              <Text style={styles.scoreLabel}>AHP Weighted Score (CR = 0.009)</Text>
              <Text style={[styles.gradeBadge, { color: scoreColor(composite_score), backgroundColor: `${scoreColor(composite_score)}18` }]}>
                Grade {grade}
              </Text>
            </View>
          </View>
        </View>

        {/* Sub-scores */}
        <View style={styles.section}>
          <Text style={styles.sectionHead}>Score Breakdown</Text>
          <View style={styles.table}>
            <View style={styles.tableHead}>
              <Text style={[styles.colName, styles.colHead]}>Criterion</Text>
              <Text style={[styles.colVal, styles.colHead]}>Score</Text>
              <Text style={[styles.colVal, styles.colHead]}>Weight</Text>
            </View>
            {metricRows.map(({ label, key, weight }) => (
              <View style={styles.tableRow} key={key}>
                <Text style={styles.colName}>{label}</Text>
                <Text style={[styles.colVal, { color: scoreColor(scores[key] ?? 0), fontFamily: 'Helvetica-Bold' }]}>
                  {Math.round(scores[key] ?? 0)}/100
                </Text>
                <Text style={[styles.colVal, { color: '#94a3b8' }]}>{weight}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Saliency Heatmap */}
        {heatmap_base64 && (
          <View style={styles.section}>
            <Text style={styles.sectionHead}>Saliency Heatmap</Text>
            <Image
              src={heatmap_base64.startsWith('data:') ? heatmap_base64 : `data:image/png;base64,${heatmap_base64}`}
              style={styles.heatmapImg}
            />
          </View>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionHead}>Recommendations</Text>
            {recommendations.slice(0, 10).map((rec, i) => (
              <View key={i} style={styles.recItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.recText}>{rec}</Text>
              </View>
            ))}
          </View>
        )}

        {/* WCAG Violations summary */}
        {violations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionHead}>Top WCAG Violations ({violations.length} total)</Text>
            <View style={styles.table}>
              <View style={styles.tableHead}>
                <Text style={[styles.colName, styles.colHead]}>Element</Text>
                <Text style={[styles.colVal, styles.colHead]}>Size</Text>
                <Text style={[styles.colVal, styles.colHead]}>WCAG AA</Text>
              </View>
              {violations.slice(0, 8).map((v, i) => (
                <View key={i} style={styles.tableRow}>
                  <Text style={styles.colName}>{v.tag} {v.text ? `"${v.text.slice(0,30)}"` : ''}</Text>
                  <Text style={styles.colVal}>{Math.round(v.width)}×{Math.round(v.height)}px</Text>
                  <Text style={[styles.colVal, { color: v.wcag_aa_pass ? '#22c55e' : '#ef4444' }]}>
                    {v.wcag_aa_pass ? 'Pass' : 'Fail'}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Footer */}
        <Text style={styles.footer}>
          Generated by UX Lens · ML-Driven UI/UX Heuristic Evaluation System · {url}
        </Text>
      </Page>
    </Document>
  )
}

// ── Download trigger ──────────────────────────────────────────────────────────
export async function downloadPDFReport(data) {
  const blob = await pdf(<UXReportDocument data={data} />).toBlob()
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `ux-report-${Date.now()}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Button component ──────────────────────────────────────────────────────────
export default function ReportExporter({ data }) {
  const [generating, setGenerating] = useState(false)

  const handleExport = async () => {
    if (!data) return
    setGenerating(true)
    try {
      await downloadPDFReport(data)
    } catch (err) {
      console.error('PDF export error:', err)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <button
      id="export-pdf-btn"
      className="btn btn-primary"
      onClick={handleExport}
      disabled={generating || !data}
    >
      {generating
        ? <><span className="btn-spinner" /> Generating PDF…</>
        : <><Download size={16} /> Download PDF Report</>}
    </button>
  )
}
