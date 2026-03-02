'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api, ClientSummary, DashboardSummary } from '@/lib/api'
import { useSimulation } from '@/context/SimulationContext'

const LEVEL_BADGE: Record<number, string> = {
  0: 'bg-emerald-900/40 text-emerald-400 border border-emerald-800/40',
  1: 'bg-blue-900/40 text-blue-400 border border-blue-800/40',
  2: 'bg-amber-900/40 text-amber-400 border border-amber-800/40',
  3: 'bg-orange-900/40 text-orange-400 border border-orange-800/40',
  4: 'bg-red-900/40 text-red-400 border border-red-800/40',
}

const LEVEL_LABEL: Record<number, string> = {
  0: 'Clear', 1: 'Monitor', 2: 'Guardrail', 3: 'Restricted', 4: 'Frozen',
}

const ARCHETYPE_LABEL: Record<string, string> = {
  payroll_depositor: 'Payroll',
  active_trader: 'Trader',
  new_investor: 'New Investor',
  seasonal_spiker: 'Seasonal',
  mule_like: 'High Risk',
}

function MetricCard({
  label,
  value,
  sub,
  accent = false,
  warn = false,
}: {
  label: string
  value: string | number
  sub?: string
  accent?: boolean
  warn?: boolean
}) {
  return (
    <div
      className="rounded-xl p-5"
      style={{
        background: '#111119',
        border: `1px solid ${warn ? 'rgba(251,146,60,0.25)' : accent ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.06)'}`,
      }}
    >
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">{label}</p>
      <p
        className="text-3xl font-bold"
        style={{ color: warn ? '#fb923c' : accent ? '#818cf8' : '#f1f5f9' }}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </div>
  )
}

function SimulateButton({ client }: { client: ClientSummary }) {
  const { startSimulation, status, clientId } = useSimulation()
  const isThisClient = clientId === client.id
  const isRunning = isThisClient && status === 'running'

  return (
    <button
      onClick={() => startSimulation(client.id, client.name)}
      disabled={status === 'running'}
      className="text-xs font-semibold px-3 py-1.5 rounded transition-all"
      style={{
        background: isRunning
          ? 'rgba(99,102,241,0.2)'
          : 'rgba(99,102,241,0.12)',
        color: status === 'running' && !isThisClient ? '#475569' : '#818cf8',
        border: '1px solid rgba(99,102,241,0.25)',
        cursor: status === 'running' ? 'not-allowed' : 'pointer',
        minWidth: 80,
      }}
    >
      {isRunning ? (
        <span className="flex items-center gap-1.5">
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Running
        </span>
      ) : 'Simulate'}
    </button>
  )
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null)
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([api.getDashboard(), api.getClients()])
      .then(([d, c]) => {
        setDashboard(d)
        setClients(c)
      })
      .catch(() => setError(true))
  }, [])

  if (error) {
    return (
      <div className="text-center py-20" style={{ color: '#64748b' }}>
        <p className="text-lg font-semibold text-slate-300">Backend not reachable</p>
        <p className="text-sm mt-1">Start the FastAPI server and seed the database first.</p>
        <pre
          className="text-xs mt-4 inline-block px-4 py-3 rounded"
          style={{ background: '#111119', border: '1px solid rgba(255,255,255,0.06)', color: '#94a3b8' }}
        >
          {`cd backend && uvicorn app.main:app --reload\npython -m app.seed.seed_data`}
        </pre>
      </div>
    )
  }

  const restrictedCount = dashboard
    ? Object.entries(dashboard.clients_by_restriction_level)
        .filter(([k]) => k !== '0')
        .reduce((s, [, v]) => s + v, 0)
    : 0

  return (
    <div className="space-y-8" style={{ color: '#e2e8f0' }}>
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#f8fafc' }}>
            Compliance Dashboard
          </h1>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>
            Real-time AML monitoring across 3.2M+ accounts
          </p>
        </div>
        <Link
          href="/"
          className="text-xs px-3 py-1.5 rounded"
          style={{
            border: '1px solid rgba(99,102,241,0.2)',
            color: '#6366f1',
            textDecoration: 'none',
          }}
        >
          ← System Overview
        </Link>
      </div>

      {/* Scale metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard label="Monitored Accounts" value="3.2M" sub="active accounts" accent />
        <MetricCard label="Risk Events Today" value="1,847" sub="auto-processed" />
        <MetricCard
          label="Open Investigations"
          value={dashboard ? dashboard.open_investigations : '—'}
          sub="in pipeline"
          warn={!!(dashboard && dashboard.open_investigations > 0)}
        />
        <MetricCard
          label="STR Drafts Pending"
          value={dashboard ? dashboard.str_drafts_pending : '—'}
          sub="human review"
          warn={!!(dashboard && dashboard.str_drafts_pending > 0)}
        />
        <MetricCard
          label="STRs Filed"
          value={dashboard ? dashboard.strs_filed_this_month : '—'}
          sub="this month"
        />
        <MetricCard label="Auto-Resolved" value="94.7%" sub="Level 0→1→0" />
      </div>

      {/* Restriction level breakdown */}
      {dashboard && (
        <div
          className="rounded-xl p-5"
          style={{ background: '#111119', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <h2 className="text-sm font-semibold mb-4" style={{ color: '#94a3b8' }}>
            Accounts by Restriction Level
          </h2>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(dashboard.clients_by_restriction_level).map(([level, count]) => (
              <div
                key={level}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold ${LEVEL_BADGE[+level] || ''}`}
              >
                L{level} — {LEVEL_LABEL[+level] ?? `Level ${level}`} &nbsp;·&nbsp; {count}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Client table */}
      <div
        className="rounded-xl overflow-hidden"
        style={{ border: '1px solid rgba(255,255,255,0.06)', background: '#111119' }}
      >
        <div
          className="px-5 py-3 flex items-center justify-between"
          style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
        >
          <h2 className="text-sm font-semibold" style={{ color: '#94a3b8' }}>
            Client Risk Register
          </h2>
          <span className="text-xs" style={{ color: '#475569' }}>
            {clients.length} clients · Click Simulate to run the full AI pipeline
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                {['Client', 'Restriction', 'Archetype', 'Risk Score', 'Indicators', 'Simulate'].map((h) => (
                  <th
                    key={h}
                    className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wide"
                    style={{ color: '#475569' }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {clients.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-sm" style={{ color: '#475569' }}>
                    Loading clients…
                  </td>
                </tr>
              )}
              {clients.map((client) => (
                <tr
                  key={client.id}
                  style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}
                  className="hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/clients/${client.id}`}
                      className="font-medium text-sm hover:underline"
                      style={{ color: '#818cf8', textDecoration: 'none' }}
                    >
                      {client.name}
                    </Link>
                    <p className="text-xs mt-0.5" style={{ color: '#475569' }}>{client.occupation}</p>
                  </td>

                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded-full ${LEVEL_BADGE[client.active_restriction_level]}`}
                    >
                      L{client.active_restriction_level} — {LEVEL_LABEL[client.active_restriction_level]}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-xs" style={{ color: '#64748b' }}>
                    {ARCHETYPE_LABEL[client.archetype] ?? client.archetype.replace(/_/g, ' ')}
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-1.5 rounded-full overflow-hidden"
                        style={{ width: 72, background: 'rgba(255,255,255,0.08)' }}
                      >
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(100, client.overall_risk_score * 100)}%`,
                            background: client.overall_risk_score > 0.75
                              ? '#ef4444'
                              : client.overall_risk_score > 0.5
                                ? '#f97316'
                                : client.overall_risk_score > 0.3
                                  ? '#eab308'
                                  : '#22c55e',
                          }}
                        />
                      </div>
                      <span className="text-xs font-mono" style={{ color: '#94a3b8' }}>
                        {(client.overall_risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>

                  {/* Placeholder for indicators detected count */}
                  <td className="px-4 py-3">
                    {client.active_restriction_level >= 2 ? (
                      <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171' }}>
                        Active
                      </span>
                    ) : (
                      <span className="text-xs" style={{ color: '#334155' }}>—</span>
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <SimulateButton client={client} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Activity feed */}
      {dashboard && (
        <div
          className="rounded-xl"
          style={{ border: '1px solid rgba(255,255,255,0.06)', background: '#111119' }}
        >
          <div
            className="px-5 py-3"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
          >
            <h2 className="text-sm font-semibold" style={{ color: '#94a3b8' }}>Recent Activity</h2>
          </div>
          <div className="divide-y max-h-72 overflow-y-auto" style={{ divideColor: 'rgba(255,255,255,0.03)' }}>
            {dashboard.recent_activity.map((entry) => (
              <div key={entry.id} className="flex items-start gap-3 px-5 py-2.5 text-sm">
                <span className="text-xs font-mono pt-0.5 whitespace-nowrap shrink-0" style={{ color: '#475569' }}>
                  {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span
                  className="text-xs px-1.5 py-0.5 rounded font-mono shrink-0"
                  style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8' }}
                >
                  {entry.entity_type}
                </span>
                <span className="flex-1 text-xs" style={{ color: '#94a3b8' }}>
                  {entry.action.replace(/_/g, ' ')}
                </span>
                <span className="text-xs shrink-0" style={{ color: '#334155' }}>
                  {entry.actor}
                </span>
              </div>
            ))}
            {dashboard.recent_activity.length === 0 && (
              <div className="px-5 py-8 text-center text-sm" style={{ color: '#475569' }}>
                No activity yet.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
