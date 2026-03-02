'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api, ClientDetail, Transaction, InvestigationSummary } from '@/lib/api'
import RiskTimeline from '@/components/RiskTimeline'

const LEVEL_BADGE: Record<number, string> = {
  0: 'bg-green-100 text-green-700 border-green-200',
  1: 'bg-blue-100 text-blue-700 border-blue-200',
  2: 'bg-amber-100 text-amber-700 border-amber-200',
  3: 'bg-orange-100 text-orange-700 border-orange-200',
  4: 'bg-red-100 text-red-700 border-red-200',
}
const LEVEL_LABEL: Record<number, string> = {
  0: 'Baseline', 1: 'Monitor', 2: 'Guardrail', 3: 'Restricted', 4: 'Frozen',
}

const ACTION_ICONS: Record<string, { icon: string; color: string; bg: string }> = {
  notification_sent:       { icon: 'N', color: 'text-blue-600',   bg: 'bg-blue-100'   },
  step_up_auth:            { icon: 'A', color: 'text-amber-700',  bg: 'bg-amber-100'  },
  follow_up_call_scheduled:{ icon: 'C', color: 'text-indigo-700', bg: 'bg-indigo-100' },
  info_request_sent:       { icon: 'I', color: 'text-purple-700', bg: 'bg-purple-100' },
  auto_de_escalated:       { icon: 'D', color: 'text-green-700',  bg: 'bg-green-100'  },
  guardrail_intercept:     { icon: 'G', color: 'text-orange-700', bg: 'bg-orange-100' },
  coordinated_alert:       { icon: 'X', color: 'text-red-700',    bg: 'bg-red-100'    },
}
const ACTION_LABELS: Record<string, string> = {
  notification_sent:        'Client Notified',
  step_up_auth:             'Step-up Auth',
  follow_up_call_scheduled: 'Follow-up Call',
  info_request_sent:        'Info Request',
  auto_de_escalated:        'Auto De-escalated',
  guardrail_intercept:      'Guardrail Intercept',
  coordinated_alert:        'Coordinated Alert',
}

const STATUS_COLORS: Record<string, string> = {
  scheduled:        'bg-blue-50 text-blue-700',
  delivered:        'bg-green-50 text-green-700',
  active:           'bg-orange-50 text-orange-700',
  awaiting_response:'bg-purple-50 text-purple-700',
  completed:        'bg-slate-50 text-slate-600',
}

export default function ClientProfilePage() {
  const params = useParams()
  const id = params.id as string

  const [client, setClient] = useState<ClientDetail | null>(null)
  const [txns, setTxns] = useState<Transaction[]>([])
  const [investigation, setInvestigation] = useState<InvestigationSummary | null>(null)
  const [tab, setTab] = useState<'profile' | 'investigation'>('profile')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getClient(id), api.getClientTransactions(id)])
      .then(([c, t]) => {
        setClient(c)
        setTxns(t)
        if (c.latest_investigation_id) {
          api.getInvestigation(c.latest_investigation_id).then((inv) =>
            setInvestigation(inv as unknown as InvestigationSummary)
          ).catch(() => {})
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="py-20 text-center text-slate-400">Loading…</div>
  if (!client) return <div className="py-20 text-center text-slate-400">Client not found</div>

  const hasInvestigation = !!client.latest_investigation_id
  const showInvestigationTab = client.active_restriction_level >= 2 || hasInvestigation

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{client.name}</h1>
          <p className="text-sm text-slate-500 font-mono mt-0.5">{client.id}</p>
        </div>
        <span className={`border text-sm font-semibold px-3 py-1 rounded-full ${LEVEL_BADGE[client.active_restriction_level]}`}>
          Level {client.active_restriction_level} — {LEVEL_LABEL[client.active_restriction_level]}
        </span>
      </div>

      {/* Tab bar (only if investigation data available) */}
      {showInvestigationTab && (
        <div className="flex gap-1 border-b border-slate-200">
          {(['profile', 'investigation'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors capitalize ${
                tab === t
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t === 'investigation' ? 'Investigation' : 'Profile'}
              {t === 'investigation' && hasInvestigation && (
                <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${
                  client.latest_investigation_status === 'str_drafted'
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-indigo-100 text-indigo-600'
                }`}>
                  {client.latest_investigation_status?.replace(/_/g, ' ')}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ── PROFILE TAB ── */}
      {tab === 'profile' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column */}
          <div className="space-y-4">
            {/* Client info */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
              <h2 className="text-sm font-semibold text-slate-700">Client Profile</h2>
              {[
                ['Occupation', client.occupation],
                ['Stated Income', `$${client.stated_income.toLocaleString()}/yr`],
                ['KYC Level', client.kyc_level],
                ['Date of Birth', client.date_of_birth],
                ['Account Opened', new Date(client.account_opened_at).toLocaleDateString()],
                ['Products', client.products_held.join(', ')],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-slate-500">{k}</span>
                  <span className="text-slate-800 font-medium capitalize">{v}</span>
                </div>
              ))}
            </div>

            {/* Risk fingerprint */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-3">Behavioral Fingerprint</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Archetype</span>
                  <span className="font-medium text-indigo-700">{client.archetype.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Trajectory</span>
                  <span className={`font-medium ${client.archetype_trajectory === 'shifting_negative' ? 'text-red-600' : 'text-green-600'}`}>
                    {client.archetype_trajectory.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">30-day Inflow</span>
                  <span className="font-medium">${client.total_inflow_30d.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">30-day Outflow</span>
                  <span className="font-medium">${client.total_outflow_30d.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Deposit Freq</span>
                  <span className="font-medium">{client.deposit_frequency_per_week.toFixed(1)}/wk</span>
                </div>
              </div>
            </div>

            {/* FINTRAC indicators */}
            {client.indicators_detected.length > 0 && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-4">
                <h2 className="text-sm font-semibold text-red-700 mb-2">FINTRAC Indicators Active</h2>
                <div className="space-y-1.5">
                  {client.indicators_detected.map((ind, i) => (
                    <div key={i} className="flex justify-between text-xs">
                      <span className="text-red-600">{ind.indicator.replace(/_/g, ' ')}</span>
                      <span className="font-semibold text-red-700">{(ind.confidence * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Proactive actions */}
            {client.proactive_actions.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <h2 className="text-sm font-semibold text-slate-700 mb-3">System Actions</h2>
                <div className="space-y-3">
                  {client.proactive_actions.map((action, i) => {
                    const icon = ACTION_ICONS[action.action] || { icon: '•', color: 'text-slate-600', bg: 'bg-slate-100' }
                    return (
                      <div key={i} className="flex gap-2.5 items-start">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${icon.bg} ${icon.color}`}>
                          {icon.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-semibold text-slate-700">
                              {ACTION_LABELS[action.action] || action.action}
                            </span>
                            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${STATUS_COLORS[action.status] || 'bg-slate-50 text-slate-600'}`}>
                              {action.status.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{action.label}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{action.trigger} · {action.channel}</p>
                          <p className="text-xs text-slate-400 font-mono mt-0.5">
                            {new Date(action.timestamp).toLocaleDateString()} {new Date(action.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right column */}
          <div className="lg:col-span-2 space-y-4">
            {client.risk_history.length > 0 && <RiskTimeline data={client.risk_history} />}

            {/* Known counterparties */}
            {client.known_counterparties.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <h2 className="text-sm font-semibold text-slate-700 mb-3">Known Counterparties</h2>
                <div className="space-y-1.5">
                  {client.known_counterparties.slice(0, 6).map((cp, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-slate-700">{cp.name}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-400">{cp.type}</span>
                        <span className="text-xs font-mono text-slate-500">{cp.frequency}×</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent transactions */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-200">
                <h2 className="text-sm font-semibold text-slate-700">Recent Transactions</h2>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 sticky top-0">
                    <tr>
                      {['Date', 'Type', 'Product', 'Amount', 'Counterparty'].map((h) => (
                        <th key={h} className="text-left px-4 py-2 text-slate-500 font-semibold">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {txns.map((t) => (
                      <tr key={t.id} className="border-b border-slate-50">
                        <td className="px-4 py-1.5 font-mono text-slate-500">
                          {new Date(t.timestamp).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-1.5 text-slate-600">{t.type.replace(/_/g, ' ')}</td>
                        <td className="px-4 py-1.5 text-slate-500">{t.product}</td>
                        <td className="px-4 py-1.5 font-semibold text-slate-800">
                          ${t.amount.toLocaleString()}
                        </td>
                        <td className="px-4 py-1.5 text-slate-500">{t.counterparty_name || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── INVESTIGATION TAB ── */}
      {tab === 'investigation' && (
        <div className="space-y-4">
          {!hasInvestigation ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-slate-500 text-sm">No investigation has been run yet.</p>
              <p className="text-slate-400 text-xs mt-1">Use the Simulate button on the Dashboard to run the full pipeline.</p>
            </div>
          ) : (
            <>
              {/* Investigation summary */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <div className="flex items-start justify-between flex-wrap gap-3">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-700">Latest Investigation</h2>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{client.latest_investigation_id}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {client.latest_investigation_classification && (
                      <span className="text-xs font-semibold px-2 py-1 rounded-full bg-orange-100 text-orange-700">
                        {client.latest_investigation_classification.replace(/_/g, ' ')}
                      </span>
                    )}
                    <Link
                      href={`/investigations/${client.latest_investigation_id}`}
                      className="text-xs font-semibold px-3 py-1.5 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
                    >
                      View Full Investigation →
                    </Link>
                  </div>
                </div>
              </div>

              {/* Agent steps mini-timeline */}
              {investigation && (investigation as any).step_log?.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                  <h2 className="text-sm font-semibold text-slate-700 mb-4">Agent Research Steps</h2>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {((investigation as any).step_log as any[]).map((step: any, i: number) => {
                      const layerColors: Record<number, string> = {
                        1: 'bg-indigo-100 text-indigo-700',
                        2: 'bg-amber-100 text-amber-700',
                        3: 'bg-orange-100 text-orange-700',
                      }
                      const layerLabels: Record<number, string> = {
                        1: 'L1 Behavioral',
                        2: 'L2 Response',
                        3: 'L3 Orchestrator',
                      }
                      return (
                        <div key={i} className="flex gap-3 items-start">
                          <div className="flex flex-col items-center">
                            <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                              <svg className="w-3 h-3 text-emerald-600" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            {i < ((investigation as any).step_log as any[]).length - 1 && (
                              <div className="w-px h-4 bg-slate-200 mt-1" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0 pb-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${layerColors[step.layer] || 'bg-slate-100 text-slate-600'}`}>
                                {layerLabels[step.layer] || `Layer ${step.layer}`}
                              </span>
                              <span className="text-xs font-medium text-slate-700">{step.label}</span>
                            </div>
                            {step.details && (
                              <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{step.details}</p>
                            )}
                          </div>
                          <span className="text-xs text-slate-400 font-mono shrink-0">
                            {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
