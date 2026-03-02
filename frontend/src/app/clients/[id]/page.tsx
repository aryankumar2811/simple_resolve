import { api, ClientDetail, Transaction } from '@/lib/api'
import { notFound } from 'next/navigation'
import Link from 'next/link'
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

export default async function ClientProfilePage({ params }: { params: { id: string } }) {
  let client: ClientDetail
  let txns: Transaction[]
  try {
    ;[client, txns] = await Promise.all([
      api.getClient(params.id),
      api.getClientTransactions(params.id),
    ])
  } catch {
    notFound()
  }

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: profile card */}
        <div className="space-y-4">
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
        </div>

        {/* Right column: charts + transactions */}
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
    </div>
  )
}
