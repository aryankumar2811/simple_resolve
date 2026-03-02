import Link from 'next/link'
import { api, ClientSummary } from '@/lib/api'

const LEVEL_BADGE: Record<number, string> = {
  0: 'bg-green-100 text-green-700',
  1: 'bg-blue-100 text-blue-700',
  2: 'bg-amber-100 text-amber-700',
  3: 'bg-orange-100 text-orange-700',
  4: 'bg-red-100 text-red-700',
}

const LEVEL_LABEL: Record<number, string> = {
  0: 'Baseline',
  1: 'Monitor',
  2: 'Guardrail',
  3: 'Restricted',
  4: 'Frozen',
}

function RiskBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.75 ? 'bg-orange-500' : score >= 0.6 ? 'bg-amber-500' : score >= 0.4 ? 'bg-blue-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 bg-slate-200 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500">{score.toFixed(2)}</span>
    </div>
  )
}

export default async function ClientsPage() {
  let clients: ClientSummary[] = []
  try {
    clients = await api.getClients()
  } catch {
    return <p className="text-slate-400 text-center py-20">Backend not reachable.</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Clients</h1>
        <p className="text-sm text-slate-500 mt-1">{clients.length} clients · click any row to see full profile</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {['Name', 'KYC', 'Products', 'Archetype', 'Risk Score', 'Restriction'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3">
                  <Link href={`/clients/${c.id}`} className="font-medium text-indigo-600 hover:underline">
                    {c.name}
                  </Link>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{c.id.slice(0, 8)}…</p>
                </td>
                <td className="px-4 py-3 text-slate-600 capitalize">{c.kyc_level}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {c.products_held.map((p) => (
                      <span key={p} className="bg-slate-100 text-slate-600 text-xs px-1.5 py-0.5 rounded">
                        {p}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">{c.archetype.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3">
                  <RiskBar score={c.overall_risk_score} />
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${LEVEL_BADGE[c.active_restriction_level]}`}>
                    L{c.active_restriction_level} {LEVEL_LABEL[c.active_restriction_level]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
