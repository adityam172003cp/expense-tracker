import { useEffect, useState } from 'react'
import { reports } from './api'
import type { MonthlyReport } from './api'

const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value)
const currentMonth = new Date().toISOString().slice(0, 7)

export default function Reports() {
  const [items, setItems] = useState<MonthlyReport[]>([])
  const [selected, setSelected] = useState<MonthlyReport | null>(null)
  const [month, setMonth] = useState(currentMonth)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  useEffect(() => { reports.list().then((response) => setItems(response.data)).catch(() => setMessage('Could not load reports.')).finally(() => setLoading(false)) }, [])
  const generate = async () => { setLoading(true); setMessage(''); try { const response = await reports.generate(month); setSelected(response.data); setItems((current) => [response.data, ...current.filter((item) => item.month !== response.data.month)]) } catch { setMessage('Could not generate this report.')} finally { setLoading(false) } }
  return <section className="reports-page"><div className="section-heading"><div><p className="eyebrow">Look back clearly</p><h2>Monthly reports</h2></div><div className="report-actions"><input type="month" value={month} onChange={(event) => setMonth(event.target.value)} /><button className="primary-button" onClick={() => void generate()} disabled={loading}>{loading ? 'Working...' : 'Generate now'}</button></div></div>{message && <div className="notice">{message}</div>}{selected && <article className="report-detail"><div><p className="eyebrow">{selected.month}</p><h3>{money(selected.total_spent)} spent</h3><p>{selected.summary ?? 'Your report is ready for review.'}</p></div><button className="text-button" onClick={() => window.print()}>Print report</button></article>}<div className="report-list">{items.map((item) => <button className="report-row" key={item.month} onClick={() => { setSelected(item); setMonth(item.month) }}><span><strong>{item.month}</strong><small>{item.summary ?? 'Monthly spending report'}</small></span><span>{money(item.total_spent)} <small>of {money(item.total_budget)}</small></span></button>)}{!loading && !items.length && <p className="empty-state">No reports yet. Generate the first one above.</p>}</div></section>
}