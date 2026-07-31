import { useEffect, useState } from 'react'
import { expenses } from './api'
import type { Expense, Sector } from './api'

const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value)
const dateFormatter = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' })
const dateTimeFormatter = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
const parseCreatedAt = (value: string) => new Date(`${value}${value.endsWith('Z') ? '' : 'Z'}`)

export default function History({ sectors }: { sectors: Sector[] }) {
  const [selectedSector, setSelectedSector] = useState<number | ''>('')
  const [items, setItems] = useState<Expense[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { if (!selectedSector && sectors[0]) setSelectedSector(sectors[0].id) }, [sectors, selectedSector])
  useEffect(() => { if (!selectedSector) return; setLoading(true); setError(''); expenses.list(selectedSector).then((response) => setItems(response.data.map((item) => ({ ...item, amount: Number(item.amount) })))).catch(() => { setItems([]); setError('Could not load expenses for this sector.') }).finally(() => setLoading(false)) }, [selectedSector])
  const sector = sectors.find((item) => item.id === selectedSector)
  return <section className="history-page"><div className="section-heading"><div><p className="eyebrow">Transaction history</p><h2>Expenses by sector</h2></div><label className="history-filter">Sector<select value={selectedSector} onChange={(event) => setSelectedSector(Number(event.target.value))}>{sectors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div>{sector && <div className="history-summary"><strong>{sector.name}</strong><span>{money(sector.current_month_spent)} spent this month</span><span>{items.length} recorded expense{items.length === 1 ? '' : 's'}</span></div>}{error && <div className="notice" role="status">{error}</div>}{loading && <p className="loading">Loading expenses...</p>}{!loading && !items.length && <p className="empty-state">No expenses recorded for this sector yet.</p>}{!loading && items.length > 0 && <div className="full-history-table-wrap"><table className="expense-history-table"><thead><tr><th>Amount</th><th>Note</th><th>Expense date</th><th>Recorded date & time</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td className="expense-amount">{money(item.amount)}</td><td className="expense-note-cell">{item.note?.trim() || 'No note added'}</td><td>{dateFormatter.format(new Date(`${item.date}T00:00:00`))}</td><td>{dateTimeFormatter.format(parseCreatedAt(item.created_at))}</td></tr>)}</tbody></table></div>}</section>
}
