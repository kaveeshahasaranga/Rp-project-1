import { useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, ChevronUp, ChevronDown } from 'lucide-react'
import './ViolationsList.css'

const COLUMNS = ['Element', 'Size', 'WCAG AA', 'WCAG AAA', 'Issue']

export default function ViolationsList({ violations = [], wcagAaRate = 0, wcagAaaRate = 0, totalElements = 0 }) {
  const [sortBy, setSortBy]   = useState('wcag_aa_pass')
  const [sortDir, setSortDir] = useState('asc')   // asc = failures first
  const [page, setPage]       = useState(0)
  const PER_PAGE = 10

  const handleSort = (col) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('asc') }
    setPage(0)
  }

  const sorted = [...violations].sort((a, b) => {
    let av, bv
    switch (sortBy) {
      case 'width':   av = a.width;  bv = b.width;  break
      case 'wcag_aa_pass':  av = a.wcag_aa_pass  ? 1 : 0; bv = b.wcag_aa_pass  ? 1 : 0; break
      case 'wcag_aaa_pass': av = a.wcag_aaa_pass ? 1 : 0; bv = b.wcag_aaa_pass ? 1 : 0; break
      default: av = (a.tag || ''); bv = (b.tag || '')
    }
    if (av < bv) return sortDir === 'asc' ? -1 : 1
    if (av > bv) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  const paginated  = sorted.slice(page * PER_PAGE, (page + 1) * PER_PAGE)
  const totalPages = Math.ceil(sorted.length / PER_PAGE)

  const SortIcon = ({ col }) =>
    sortBy === col
      ? sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
      : null

  if (!violations.length) {
    return (
      <div className="violations-empty glass-card">
        <CheckCircle size={40} color="var(--success)" />
        <h4>No violations detected</h4>
        <p>All interactive elements meet WCAG 2.5.8 (AA) minimum requirements.</p>
      </div>
    )
  }

  return (
    <div className="violations-wrap glass-card">
      <div className="violations-header">
        <h3 className="section-title" style={{ margin: 0 }}>WCAG Touch Target Violations</h3>
        <div className="compliance-pills">
          <div className="compliance-pill">
            <span className="pill-label">WCAG AA</span>
            <span className={`pill-rate ${wcagAaRate >= 80 ? 'pill-success' : wcagAaRate >= 50 ? 'pill-warn' : 'pill-danger'}`}>
              {wcagAaRate.toFixed(1)}%
            </span>
          </div>
          <div className="compliance-pill">
            <span className="pill-label">WCAG AAA</span>
            <span className={`pill-rate ${wcagAaaRate >= 80 ? 'pill-success' : wcagAaaRate >= 50 ? 'pill-warn' : 'pill-danger'}`}>
              {wcagAaaRate.toFixed(1)}%
            </span>
          </div>
          <div className="compliance-pill">
            <span className="pill-label">Elements</span>
            <span className="pill-rate" style={{ color: 'var(--text-muted)' }}>{totalElements}</span>
          </div>
        </div>
      </div>

      <div className="table-scroll">
        <table className="violations-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('tag')} className="sortable">
                Element <SortIcon col="tag" />
              </th>
              <th onClick={() => handleSort('width')} className="sortable">
                Size <SortIcon col="width" />
              </th>
              <th onClick={() => handleSort('wcag_aa_pass')} className="sortable">
                WCAG AA <SortIcon col="wcag_aa_pass" />
              </th>
              <th onClick={() => handleSort('wcag_aaa_pass')} className="sortable">
                WCAG AAA <SortIcon col="wcag_aaa_pass" />
              </th>
              <th>Issues</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((el, i) => (
              <tr key={i} className={el.wcag_aa_pass ? '' : 'row-fail'}>
                <td>
                  <code className="el-tag">{el.tag}</code>
                  {el.text && <span className="el-text"> {el.text.slice(0, 30)}{el.text.length > 30 ? '…' : ''}</span>}
                </td>
                <td className="size-cell">
                  <span className={`size-badge ${Math.min(el.width,el.height) < 24 ? 'size-danger' : Math.min(el.width,el.height) < 44 ? 'size-warn' : 'size-ok'}`}>
                    {Math.round(el.width)}×{Math.round(el.height)}px
                  </span>
                </td>
                <td className="check-cell">
                  {el.wcag_aa_pass
                    ? <CheckCircle size={16} color="var(--success)" />
                    : <XCircle size={16} color="var(--danger)" />}
                </td>
                <td className="check-cell">
                  {el.wcag_aaa_pass
                    ? <CheckCircle size={16} color="var(--success)" />
                    : el.wcag_aa_pass
                      ? <AlertTriangle size={16} color="var(--warning)" />
                      : <XCircle size={16} color="var(--danger)" />}
                </td>
                <td>
                  {el.issues && el.issues.length > 0
                    ? <span className="issue-text">{el.issues[0]}</span>
                    : <span className="issue-ok">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>
            Previous
          </button>
          <span className="page-info">{page + 1} / {totalPages}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1}>
            Next
          </button>
        </div>
      )}
    </div>
  )
}
