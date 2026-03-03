'use client'
import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { api, ClientSummary, DashboardSummary } from '@/lib/api'
import { useSimulation } from '@/context/SimulationContext'
import SimulationModal, { InlineSimulationPanel } from '@/components/SimulationModal'

const LEVEL_BADGE: Record<number, string> = {
  0: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  1: 'bg-blue-100 text-blue-700 border border-blue-200',
  2: 'bg-amber-100 text-amber-700 border border-amber-200',
  3: 'bg-orange-100 text-orange-700 border border-orange-200',
  4: 'bg-red-100 text-red-700 border border-red-200',
}

const LEVEL_LABEL: Record<number, string> = {
  0: 'Resolved', 1: 'L1: Monitor', 2: 'L2: Guardrail',
  3: 'L3: Restricted', 4: 'L4: Frozen',
}

const ARCHETYPE_LABEL: Record<string, string> = {
  payroll_depositor: 'Payroll Depositor',
  active_trader: 'Active Trader',
  new_investor: 'New Investor',
  seasonal_spiker: 'Seasonal Spiker',
  mule_like: 'Mule-Like',
}

function MetricCard({
  label, value, sub, accent = false, warn = false,
}: {
  label: string; value: string | number; sub?: string; accent?: boolean; warn?: boolean;
}) {
  return (
    <div className={`rounded-lg p-5 bg-white border ${warn ? 'border-orange-200' : accent ? 'border-indigo-200' : 'border-slate-200'}`}>
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-3xl font-bold ${warn ? 'text-orange-600' : accent ? 'text-indigo-600' : 'text-slate-900'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

function RiskBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.75 ? 'bg-orange-500' : score >= 0.60 ? 'bg-amber-400' : score >= 0.40 ? 'bg-blue-400' : 'bg-emerald-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-slate-500 w-8 text-right">{score.toFixed(2)}</span>
    </div>
  )
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null)
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [loading, setLoading] = useState(true)
  const { startSimulation, isRunning, isModalOpen } = useSimulation()

  const fetchData = useCallback(async () => {
    try {
      const [dashData, clientData] = await Promise.all([
        api.getDashboard(),
        api.getClients(),
      ])
      setDashboard(dashData)
      setClients(clientData)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleSimulate = useCallback(async () => {
    const clientList = clients.map(c => ({ clientId: c.id, clientName: c.name }))
    await startSimulation(clientList, fetchData)
  }, [clients, startSimulation, fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400 text-sm">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <SimulationModal />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">AML Operations Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time behavioral risk monitoring across all monitored accounts.
        </p>
      </div>

      {/* Platform-scale metrics (static numbers represent production scale) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard label="Monitored Accounts" value="3.2M" sub="Platform scale" />
        <MetricCard label="Risk Events Today" value="1,847" sub="Across all clients" warn />
        <MetricCard label="Open Investigations" value={dashboard?.open_investigations ?? 0} sub="Require review" accent />
        <MetricCard label="STR Drafts Pending" value={dashboard?.str_drafts_pending ?? 0} sub="Awaiting analyst" warn />
        <MetricCard label="STRs Filed / Month" value={dashboard?.strs_filed_this_month ?? 0} sub="FINTRAC submissions" />
        <MetricCard label="Auto-Resolved" value="94.7%" sub="L0–L1 escalations" />
      </div>

      {/* Inline simulation panel (shows when simulation is running) */}
      <InlineSimulationPanel />

      {/* Client risk register */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Client Risk Register</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {clients.length} monitored clients · {clients.filter(c => c.active_restriction_level > 0).length} with active restrictions
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSimulate}
              disabled={isRunning}
              className="flex items-center gap-2 bg-indigo-600 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Running...
                </>
              ) : (
                <>
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Run Simulation
                </>
              )}
            </button>
            <span className="text-xs text-slate-400 max-w-[200px] leading-tight">
              In production, this pipeline runs automatically on every transaction event.
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Client</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">KYC</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Products</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Risk Level</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Archetype</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-40">Risk Score</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {clients.map(client => {
                const hasProfile = client.overall_risk_score > 0 || client.active_restriction_level > 0
                const hasRestriction = client.active_restriction_level > 0
                const level = client.active_restriction_level

                return (
                  <tr key={client.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-3.5">
                      <Link href={`/clients/${client.id}`} className="font-medium text-indigo-600 hover:text-indigo-800 hover:underline">
                        {client.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded capitalize">
                        {client.kyc_level}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-wrap gap-1">
                        {client.products_held.map(p => (
                          <span key={p} className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded capitalize">
                            {p}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      {hasProfile ? (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${LEVEL_BADGE[level] || LEVEL_BADGE[0]}`}>
                          {LEVEL_LABEL[level] || `L${level}`}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 font-medium">Not assessed</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-600">
                      {hasProfile && client.archetype
                        ? (ARCHETYPE_LABEL[client.archetype] || client.archetype.replace(/_/g, ' '))
                        : <span className="text-slate-400">-</span>
                      }
                    </td>
                    <td className="px-4 py-3.5 w-40">
                      {hasProfile
                        ? <RiskBar score={client.overall_risk_score} />
                        : <span className="text-slate-400 text-xs">-</span>
                      }
                    </td>
                    <td className="px-4 py-3.5">
                      {!hasProfile ? (
                        <span className="text-xs text-slate-400">Pending simulation</span>
                      ) : level === 0 ? (
                        <span className="text-xs text-emerald-600 font-medium">Resolved</span>
                      ) : level === 1 ? (
                        <span className="text-xs text-blue-600 font-medium">Monitoring</span>
                      ) : level === 2 ? (
                        <span className="text-xs text-amber-600 font-medium">Guardrail Active</span>
                      ) : level >= 3 ? (
                        <Link href={`/clients/${client.id}`} className="text-xs text-orange-600 font-medium hover:underline">
                          Under Investigation →
                        </Link>
                      ) : (
                        <span className="text-xs text-emerald-600 font-medium">Active</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Activity */}
      {dashboard?.recent_activity && dashboard.recent_activity.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-900">Recent Activity</h2>
          </div>
          <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
            {dashboard.recent_activity.map((entry: any) => (
              <div key={entry.id} className="flex items-start gap-3 px-5 py-2.5 text-sm">
                <span className="text-xs font-mono pt-0.5 whitespace-nowrap shrink-0 text-slate-400">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-slate-700 flex-1 text-xs">
                  <span className="font-medium text-slate-900">{entry.actor}</span>
                  {' · '}{entry.action.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-slate-400 capitalize shrink-0">{entry.entity_type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
