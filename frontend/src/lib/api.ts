/**
 * Typed API client for the SimpleResolve backend.
 * All data-fetching in the frontend goes through these functions
 * so there is a single place to change the base URL or add auth headers.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface ClientSummary {
  id: string
  name: string
  kyc_level: string
  products_held: string[]
  account_opened_at: string
  stated_income: number
  occupation: string
  overall_risk_score: number
  archetype: string
  active_restriction_level: number
}

export interface ProactiveAction {
  timestamp: string
  action: 'notification_sent' | 'step_up_auth' | 'follow_up_call_scheduled' | 'info_request_sent' | 'auto_de_escalated' | 'guardrail_intercept' | 'coordinated_alert'
  label: string
  trigger: string
  channel: string
  status: string
}

export interface ClientDetail extends ClientSummary {
  date_of_birth: string
  archetype_trajectory: string
  risk_trend: string
  risk_scores: Record<string, number>
  risk_history: { date: string; score: number }[]
  indicators_detected: { indicator: string; detected_at: string; confidence: number }[]
  known_counterparties: { name: string; type: string; last_seen: string; frequency: number }[]
  total_inflow_30d: number
  total_outflow_30d: number
  deposit_frequency_per_week: number
  proactive_actions: ProactiveAction[]
  latest_investigation_id: string | null
  latest_investigation_status: string | null
  latest_investigation_classification: string | null
}

export interface Transaction {
  id: string
  client_id: string
  type: string
  product: string
  amount: number
  timestamp: string
  source: string | null
  destination: string | null
  counterparty_name: string | null
  txn_metadata: Record<string, unknown> | null
}

export interface Restriction {
  id: string
  client_id: string
  level: number
  restricted_capabilities: string[]
  allowed_capabilities: string[]
  reason: string
  client_message: string
  gemini_reasoning: string | null
  trigger_type: string | null
  is_active: boolean
  triggered_at: string
}

export interface STRDraft {
  id: string
  investigation_id: string
  subject_profile: string
  activity_description: string
  indicators_present: { indicator: string; confidence: number; reasoning: string; fintrac_ref?: string }[]
  behavioral_context: string
  network_analysis: string
  recommendation: string
  key_uncertainties: string[]
  narrative_full: string
  tagged_transactions: TaggedTransaction[]
  money_flow: MoneyFlow | null
  ai_confidence: number | null
  ai_reasoning_chain: string | null
  status: 'draft' | 'approved' | 'dismissed'
  analyst_notes: string | null
  decided_at: string | null
  decided_by: string | null
  created_at: string
}

export interface TaggedTransaction extends Transaction {
  fintrac_indicators: { indicator: string; confidence: number; reasoning: string }[]
}

export interface MoneyFlow {
  nodes: { id: string; label: string; type: string }[]
  edges: { from: string; to: string; amount: number; type: string }[]
}

export interface NetworkGraph {
  nodes: { id: string; label: string; type: string }[]
  edges: { from: string; to: string; type: string }[]
}

export interface StepLogEntry {
  step: string
  label: string
  layer: number
  status: 'complete' | 'running' | 'pending'
  timestamp: string
  details: string
  action_type: string | null
}

export interface InvestigationSummary {
  id: string
  client_id: string
  client_name: string
  status: string
  classification: string | null
  confidence: number | null
  is_coordinated: boolean
  correlated_client_ids: string[]
  response_level: number
  step_log: StepLogEntry[]
  created_at: string
  updated_at: string
}

export interface InvestigationDetail extends InvestigationSummary {
  trigger_event: Record<string, unknown> | null
  network_graph: NetworkGraph | null
  reasoning: string | null
  str_draft: STRDraft | null
}

export interface SimulateResponse {
  investigation_id: string
  client_id: string
  client_name: string
  message: string
}

export interface DashboardSummary {
  total_clients: number
  clients_by_restriction_level: Record<string, number>
  open_investigations: number
  str_drafts_pending: number
  strs_filed_this_month: number
  recent_activity: {
    id: string
    entity_type: string
    entity_id: string
    action: string
    actor: string
    timestamp: string
  }[]
}

// ── API calls ──────────────────────────────────────────────────────────────

export const api = {
  // Dashboard
  getDashboard: () => get<DashboardSummary>('/dashboard/summary'),
  getActivity: (limit = 50) => get<DashboardSummary['recent_activity']>(`/dashboard/activity?limit=${limit}`),

  // Clients
  getClients: () => get<ClientSummary[]>('/clients'),
  getClient: (id: string) => get<ClientDetail>(`/clients/${id}`),
  getClientTransactions: (id: string) => get<Transaction[]>(`/clients/${id}/transactions`),
  getClientProfile: (id: string) => get<ClientDetail>(`/clients/${id}/profile`),

  // Restrictions
  getRestriction: (clientId: string) => get<Restriction | null>(`/restrictions/${clientId}`),

  // Investigations
  getInvestigations: (status?: string) =>
    get<InvestigationSummary[]>(`/investigations${status ? `?status=${status}` : ''}`),
  getInvestigation: (id: string) => get<InvestigationDetail>(`/investigations/${id}`),
  triggerInvestigation: (clientId: string, triggerType = 'manual') =>
    post<InvestigationSummary>(`/investigations/trigger/${clientId}`, {
      trigger_type: triggerType,
    }),
  decideSTR: (investigationId: string, decision: 'approve' | 'dismiss', notes?: string) =>
    post<InvestigationSummary>(`/investigations/${investigationId}/decide`, {
      decision,
      analyst: 'human_analyst',
      notes,
    }),
  simulate: (clientId: string) =>
    post<SimulateResponse>(`/investigations/simulate/${clientId}`, {}),
}
