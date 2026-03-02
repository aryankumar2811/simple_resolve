import { api, DashboardSummary } from '@/lib/api'

const LEVEL_LABELS: Record<string, string> = {
  '0': 'Unrestricted',
  '1': 'Monitor',
  '2': 'Guardrail',
  '3': 'Restricted',
  '4': 'Frozen',
}

const LEVEL_COLORS: Record<string, string> = {
  '0': 'bg-green-100 text-green-700',
  '1': 'bg-blue-100 text-blue-700',
  '2': 'bg-amber-100 text-amber-700',
  '3': 'bg-orange-100 text-orange-700',
  '4': 'bg-red-100 text-red-700',
}

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

export default async function DashboardPage() {
  let data: DashboardSummary | null = null
  try {
    data = await api.getDashboard()
  } catch {
    return (
      <div className="text-center py-20 text-slate-400">
        <p className="text-lg font-semibold">Backend not reachable</p>
        <p className="text-sm mt-1">Start the FastAPI server and seed the database first.</p>
        <pre className="text-xs mt-4 inline-block bg-slate-100 px-4 py-2 rounded">
          {`cd backend && uvicorn app.main:app --reload\npython -m app.seed.seed_data`}
        </pre>
      </div>
    )
  }

  const restrictedCount = Object.entries(data.clients_by_restriction_level)
    .filter(([k]) => k !== '0')
    .reduce((s, [, v]) => s + v, 0)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time view of account restrictions, active investigations, and STR pipeline.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard label="Total Clients" value={data.total_clients} />
        <StatCard label="Clients Restricted" value={restrictedCount} sub="level 1–4" />
        <StatCard label="Open Investigations" value={data.open_investigations} />
        <StatCard label="STR Drafts Pending" value={data.str_drafts_pending} sub="human review" />
        <StatCard label="STRs Filed" value={data.strs_filed_this_month} sub="this month" />
      </div>

      {/* Restriction level breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-4">Clients by Restriction Level</h2>
        <div className="flex gap-3 flex-wrap">
          {Object.entries(data.clients_by_restriction_level).map(([level, count]) => (
            <div key={level} className={`px-4 py-2 rounded-lg text-sm font-semibold ${LEVEL_COLORS[level]}`}>
              {LEVEL_LABELS[level] ?? `L${level}`} — {count}
            </div>
          ))}
        </div>
      </div>

      {/* Activity feed */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-4">Recent Activity</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {data.recent_activity.map((entry) => (
            <div key={entry.id} className="flex items-start gap-3 text-sm py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-xs text-slate-400 font-mono pt-0.5 whitespace-nowrap">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
              <span className="bg-slate-100 text-slate-600 text-xs px-1.5 py-0.5 rounded font-mono">
                {entry.entity_type}
              </span>
              <span className="text-slate-700 flex-1">{entry.action.replace(/_/g, ' ')}</span>
              <span className="text-xs text-slate-400 whitespace-nowrap">{entry.actor}</span>
            </div>
          ))}
          {data.recent_activity.length === 0 && (
            <p className="text-slate-400 text-sm">No activity yet. Seed the database to see events.</p>
          )}
        </div>
      </div>
    </div>
  )
}
