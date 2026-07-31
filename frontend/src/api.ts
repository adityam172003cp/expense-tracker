const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
async function request<T>(path: string, options: RequestInit = {}): Promise<{ data: T }> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  const token = localStorage.getItem('expense_tracker_token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${baseUrl}${path}`, { ...options, headers })
  if (response.status === 401) { localStorage.removeItem('expense_tracker_token'); window.dispatchEvent(new Event('auth-expired')) }
  if (!response.ok) { const error = new Error((await response.json().catch(() => ({}))).detail ?? 'Request failed') as Error & { response?: { data?: { detail?: string } } }; error.response = { data: { detail: error.message } }; throw error }
  return { data: response.status === 204 ? undefined as T : await response.json() as T }
}
const post = <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) })
const put = <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) })
const remove = (path: string) => request<void>(path, { method: 'DELETE' })

export type AlertLevel = 'ok' | 'warning' | 'critical' | 'exceeded'
export interface Summary { total_budget: number; total_spent: number; total_remaining: number; days_left_in_month: number }
export interface Sector { id: number; name: string; monthly_budget: number; color_tag?: string; current_month_spent: number; remaining_budget: number; alert_level: AlertLevel; percent_used?: number }
interface DashboardSector { sector_id: number; name: string; monthly_budget: number; color_tag?: string; spent: number; remaining: number; alert_level: AlertLevel; percent_used?: number }
export interface Expense { id: number; sector_id: number; amount: number; note?: string; date: string; created_at: string }
export interface User { id: number; email: string; full_name?: string | null; created_at: string }
export interface TrendPoint { date: string; actual_spend: number; ideal_spend: number }
export interface BreakdownItem { sector_id: number; name: string; spent: number; share_percent: number }
export interface BudgetVsActualItem { sector_id: number; name: string; budget: number; spent: number; percent_used: number }
export interface HeatmapDay { date: string; amount: number }
export interface MonthlyTrendItem { month: string; sector_id: number; name: string; total_spent: number }
export interface MonthlyReport { month: string; total_spent: number; total_budget: number; summary?: string; details?: unknown }
export interface AITotals { period: string; total_budget: number; total_spent: number; total_remaining: number }
export interface AIAnalysisSector { name: string; spent: string; budget: string; percent_used: string; status: string }
export interface AIAnalysis { overview: string; sector_breakdown: AIAnalysisSector[]; warnings: string[]; save_suggestions: string[]; spend_suggestions: string[] }
export const auth = {
  login: (email: string, password: string) => post<{ access_token: string }>('/auth/login', { email, password }),
  register: (email: string, password: string, full_name: string) => post('/auth/register', { email, password, full_name }),
  me: () => request<User>('/auth/me'),
}
export const dashboard = {
  summary: () => request<Summary>('/dashboard/summary'),
  sectors: async () => { const response = await request<DashboardSector[]>('/dashboard/sectors'); return { data: response.data.map((sector) => ({ id: sector.sector_id, name: sector.name, monthly_budget: Number(sector.monthly_budget), color_tag: sector.color_tag, current_month_spent: Number(sector.spent), remaining_budget: Number(sector.remaining), alert_level: sector.alert_level, percent_used: Number(sector.percent_used ?? 0) })) } },
}
export const analytics = {
  trend: () => request<TrendPoint[]>('/analytics/trend?range=month'),
  breakdown: () => request<BreakdownItem[]>('/analytics/breakdown'),
  budgetVsActual: () => request<BudgetVsActualItem[]>('/analytics/budget-vs-actual'),
  heatmap: () => request<HeatmapDay[]>('/analytics/heatmap'),
  monthlyTrend: () => request<MonthlyTrendItem[]>('/analytics/monthly-trend'),
}
export const ai = {
  insights: () => request<{ insights: string; totals: AITotals; analysis: AIAnalysis }>('/ai/insights'),
  ask: (question: string) => request<{ answer: string }>(`/ai/ask?question=${encodeURIComponent(question)}`, { method: 'POST' }),
}
export const reports = {
  list: () => request<MonthlyReport[]>('/reports/'),
  get: (month: string) => request<MonthlyReport>(`/reports/${month}`),
  generate: (month: string) => request<MonthlyReport>(`/reports/generate?month_year=${encodeURIComponent(month)}`, { method: 'POST' }),
}
export const sectors = {
  create: (payload: { name: string; monthly_budget: number; color_tag: string }) => post<Sector>('/sectors/', payload),
  update: (id: number, payload: { name?: string; monthly_budget?: number }) => put<Sector>(`/sectors/${id}`, payload),
  remove: (id: number) => remove(`/sectors/${id}`),
}
export const expenses = {
  create: (payload: { sector_id: number; amount: number; date: string; note: string }) => post<Expense>('/expenses/', payload),
  list: (sectorId: number) => request<Expense[]>(`/expenses/?sector_id=${sectorId}`),
}