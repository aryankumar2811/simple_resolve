import Link from 'next/link'
import { api, InvestigationSummary } from '@/lib/api'

const STATUS_BADGE: Record<string, string> = {
  open: 'bg-blue-100 text-blue-700',
  running: 'bg-indigo-100 text-indigo-700',
  de_escalated: 'bg-green-100 text-green-700',
  fast_tracked: 'bg-amber-100 text-amber-700',
  str_drafted: 'bg-orange-100 text-orange-700',
  filed: 'bg-purple-100 text-purple-700',
  dismissed: 'bg-slate-100 text-slate-500',
}

const CLASSIFICATION_BADGE: Record<string, string> = {
  de_escalate: 'bg-green-100 text-green-700',
  fast_track: 'bg-amber-100 text-amber-700',
  full_investigation: 'bg-red-100 text-red-700',
}

export default async function InvestigationsPage() {
  let investigations: InvestigationSummary[] = []
  try {
    investigations = await api.getInvestigations()
  } catch {
    return <p className="text-slate-400 text-center py-20">Backend not reachable.</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Investigations</h1>
        <p className="text-sm text-slate-500 mt-1">
          {investigations.length} total · trigger new ones via a client profile page
        </p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {['Client', 'Status', 'Classification', 'Confidence', 'Coordinated', 'Created'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {investigations.map((inv) => (
              <tr key={inv.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3">
                  <Link href={`/investigations/${inv.id}`} className="font-medium text-indigo-600 hover:underline">
                    {inv.client_name}
                  </Link>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{inv.id.slice(0, 8)}…</p>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_BADGE[inv.status] || 'bg-slate-100 text-slate-600'}`}>
                    {inv.status.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {inv.classification ? (
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${CLASSIFICATION_BADGE[inv.classification] || ''}`}>
                      {inv.classification.replace(/_/g, ' ')}
                    </span>
                  ) : <span className="text-slate-400">—</span>}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {inv.confidence !== null ? `${inv.confidence?.toFixed(0)}%` : '—'}
                </td>
                <td className="px-4 py-3">
                  {inv.is_coordinated ? (
                    <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                      Yes ({inv.correlated_client_ids.length + 1} clients)
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">No</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-slate-500">
                  {new Date(inv.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
            {investigations.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-slate-400 text-sm">
                  No investigations yet. Trigger one from a client profile page.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
