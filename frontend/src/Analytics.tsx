import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { analytics } from './api'
import type { BreakdownItem, BudgetVsActualItem, HeatmapDay, MonthlyTrendItem, TrendPoint } from './api'

const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value)
const colors = ['#e78249', '#587c65', '#d2a84b', '#6b8f9d', '#b86655', '#8a9a70']

export default function Analytics() {
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [breakdown, setBreakdown] = useState<BreakdownItem[]>([])
  const [budgetActual, setBudgetActual] = useState<BudgetVsActualItem[]>([])
  const [heatmap, setHeatmap] = useState<HeatmapDay[]>([])
  const [monthly, setMonthly] = useState<MonthlyTrendItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([analytics.trend(), analytics.breakdown(), analytics.budgetVsActual(), analytics.heatmap(), analytics.monthlyTrend()])
      .then(([trendResponse, breakdownResponse, budgetResponse, heatmapResponse, monthlyResponse]) => {
        setTrend(trendResponse.data); setBreakdown(breakdownResponse.data); setBudgetActual(budgetResponse.data); setHeatmap(heatmapResponse.data); setMonthly(monthlyResponse.data)
      })
      .catch(() => setError('Could not load analytics right now.'))
      .finally(() => setLoading(false))
  }, [])

  const monthData = monthly.reduce<Record<string, Record<string, number | string>>>((result, item) => {
    result[item.month] ??= { month: item.month }
    result[item.month][item.name] = item.total_spent
    return result
  }, {})
  const sectorNames = [...new Set(monthly.map((item) => item.name))]
  const maxHeat = Math.max(...heatmap.map((item) => item.amount), 1)

  return <section className="analytics-page">
    <div className="section-heading"><div><p className="eyebrow">Your patterns</p><h2>Analytics</h2></div><span>Current month</span></div>
    {loading && <p className="loading">Crunching the numbers...</p>}{error && <div className="form-error">{error}</div>}
    {!loading && !error && <>
      <div className="chart-grid">
        <article className="chart-card chart-wide"><div className="chart-heading"><h3>Spend pace</h3><span>Daily actual vs projected</span></div><ResponsiveContainer width="100%" height={280}><LineChart data={trend}><CartesianGrid stroke="#deded4" vertical={false} /><XAxis dataKey="date" tickFormatter={(value) => value.slice(8)} /><YAxis tickFormatter={(value) => money(value)} width={72} /><Tooltip formatter={(value) => money(Number(value))} /><Legend /><Line type="monotone" dataKey="actual_spend" name="Daily spend" stroke="#e78249" strokeWidth={3} dot={false} /><Line type="monotone" dataKey="ideal_spend" name="Pace projection" stroke="#587c65" strokeDasharray="5 5" dot={false} /></LineChart></ResponsiveContainer></article>
        <article className="chart-card"><div className="chart-heading"><h3>Where it goes</h3><span>Share of spending</span></div>{breakdown.length ? <ResponsiveContainer width="100%" height={280}><PieChart><Pie data={breakdown} dataKey="spent" nameKey="name" innerRadius={62} outerRadius={94} paddingAngle={3}>{breakdown.map((item, index) => <Cell key={item.sector_id} fill={colors[index % colors.length]} />)}</Pie><Tooltip formatter={(value) => money(Number(value))} /><Legend /></PieChart></ResponsiveContainer> : <p className="empty-state">No expenses this month yet.</p>}</article>
        <article className="chart-card chart-wide"><div className="chart-heading"><h3>Budget vs actual</h3><span>Monthly limits by budget</span></div><ResponsiveContainer width="100%" height={280}><BarChart data={budgetActual} layout="vertical" margin={{ left: 12, right: 18 }}><CartesianGrid stroke="#deded4" horizontal={false} /><XAxis type="number" tickFormatter={(value) => money(value)} /><YAxis type="category" dataKey="name" width={85} /><Tooltip formatter={(value) => money(Number(value))} /><Legend /><Bar dataKey="budget" fill="#d9ddd3" name="Budget" radius={[0, 4, 4, 0]} /><Bar dataKey="spent" fill="#e78249" name="Spent" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></article>
        <article className="chart-card"><div className="chart-heading"><h3>Spending days</h3><span>Intensity this month</span></div><div className="heatmap">{heatmap.map((item) => <span key={item.date} title={`${item.date}: ${money(item.amount)}`} style={{ opacity: .25 + item.amount / maxHeat * .75 }} />)}</div><p className="heatmap-caption">{heatmap.length} active spending days</p></article>
      </div>
      {monthly.length > 0 && <article className="chart-card monthly-chart"><div className="chart-heading"><h3>Month over month</h3><span>Sector totals over time</span></div><ResponsiveContainer width="100%" height={280}><LineChart data={Object.values(monthData)}><CartesianGrid stroke="#deded4" vertical={false} /><XAxis dataKey="month" /><YAxis tickFormatter={(value) => money(value)} width={72} /><Tooltip formatter={(value) => money(Number(value))} /><Legend />{sectorNames.map((name, index) => <Line key={name} type="monotone" dataKey={name} stroke={colors[index % colors.length]} strokeWidth={2} dot={false} />)}</LineChart></ResponsiveContainer></article>}
    </>}
  </section>
}