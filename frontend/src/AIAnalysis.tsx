import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ai } from './api'
import type { AIAnalysis, AITotals } from './api'

const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value)

export default function AIAnalysisPanel() {
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null)
  const [totals, setTotals] = useState<AITotals | null>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [asking, setAsking] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ai.insights().then((response) => { setAnalysis(response.data.analysis); setTotals(response.data.totals) }).catch(() => undefined).finally(() => setLoading(false))
  }, [])

  const ask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!question.trim()) return
    setAsking(true)
    try { const response = await ai.ask(question); setAnswer(response.data.answer) } catch { setAnswer('I could not complete that analysis right now.') } finally { setAsking(false) }
  }

  return <section className="analysis-panel">
    <div className="analysis-header"><div><p className="eyebrow">Decision support</p><h2>Monthly expenditure analysis</h2><p className="analysis-subtitle">A clear review of where your money went and what to consider next.</p></div>{totals && <div className="analysis-period">{totals.period}</div>}</div>
    {loading && <p className="loading">Preparing your analysis...</p>}
    {analysis && <>
      <div className="analysis-overview"><span>Overview</span><strong>{analysis.overview}</strong></div>
      <div className="analysis-columns">
        <article className="analysis-section"><div className="analysis-section-title"><span className="analysis-icon">01</span><div><h3>Sector breakdown</h3><p>Compare actual spending with each budget.</p></div></div><div className="analysis-table"><div className="analysis-table-head"><span>Sector</span><span>Spent</span><span>Budget use</span></div>{analysis.sector_breakdown.map((sector, index) => <div className="analysis-table-row" key={`${sector.name}-${sector.budget}-${index}`}><strong>{sector.name}</strong><span>{money(Number(sector.spent))}</span><span><i className={`analysis-status ${sector.status.replace(' ', '-')}`}>{sector.status}</i>{Number(sector.percent_used).toFixed(1)}%</span></div>)}</div></article>
        <article className="analysis-section"><div className="analysis-section-title"><span className="analysis-icon">02</span><div><h3>Watch closely</h3><p>Areas that may need a spending decision.</p></div></div><div className="analysis-advice-list">{analysis.warnings.map((item) => <p className="advice warning" key={item}>{item}</p>)}{!analysis.warnings.length && <p className="advice">No warning signals this month.</p>}</div></article>
      </div>
      <div className="analysis-columns"><article className="analysis-section"><div className="analysis-section-title"><span className="analysis-icon">03</span><div><h3>Where to save</h3><p>Practical ways to protect your remaining budget.</p></div></div><div className="analysis-advice-list">{analysis.save_suggestions.map((item) => <p className="advice save" key={item}>{item}</p>)}</div></article><article className="analysis-section"><div className="analysis-section-title"><span className="analysis-icon">04</span><div><h3>Where to spend intentionally</h3><p>Planned priorities, not pressure to spend.</p></div></div><div className="analysis-advice-list">{analysis.spend_suggestions.map((item) => <p className="advice spend" key={item}>{item}</p>)}</div></article></div>
    </>}
    <div className="ask-ai"><form onSubmit={ask}><label>Ask a follow-up question<input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. Should I reduce my food budget?" /></label><button className="primary-button" type="submit" disabled={asking}>{asking ? 'Reviewing...' : 'Ask AI'}</button></form>{answer && <p className="ask-answer"><strong>AI answer:</strong> {answer}</p>}</div>
  </section>
}
