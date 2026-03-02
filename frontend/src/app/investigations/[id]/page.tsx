'use client'
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, InvestigationDetail, TaggedTransaction } from '@/lib/api'
import MoneyFlowGraph from '@/components/MoneyFlowGraph'
import CrossClientNetwork from '@/components/CrossClientNetwork'
import STRReview from '@/components/STRReview'

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-100 text-blue-700',
  running: 'bg-indigo-100 text-indigo-700',
  de_escalated: 'bg-green-100 text-green-700',
  fast_tracked: 'bg-amber-100 text-amber-700',
  str_drafted: 'bg-orange-100 text-orange-700',
  filed: 'bg-purple-100 text-purple-700',
  dismissed: 'bg-slate-100 text-slate-500',
}

const INDICATOR_CHIP: Record<string, string> = {
  structuring: 'bg-red-100 text-red-700',
  layering: 'bg-orange-100 text-orange-700',
  rapid_crypto_conversion: 'bg-amber-100 text-amber-700',
  income_inconsistency: 'bg-yellow-100 text-yellow-800',
  new_counterparty_burst: 'bg-purple-100 text-purple-700',
  default: 'bg-slate-100 text-slate-700',
}

function TransactionRow({ txn }: { txn: TaggedTransaction }) {
  const indicators = txn.fintrac_indicators || []
  return (
    <tr className="border-b border-slate-100">
      <td className="px-3 py-2 text-xs font-mono text-slate-500 whitespace-nowrap">
        {new Date(txn.timestamp).toLocaleDateString()}
      </td>
      <td className="px-3 py-2 text-xs text-slate-600">{txn.type.replace(/_/g, ' ')}</td>
      <td className="px-3 py-2 text-xs text-slate-500">{txn.product}</td>
      <td className="px-3 py-2 text-xs font-semibold text-slate-800">
        ${txn.amount.toLocaleString()}
      </td>
      <td className="px-3 py-2 text-xs text-slate-500">{txn.counterparty_name || '—'}</td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap gap-1">
          {indicators.map((ind, i) => (
            <span
              key={i}
              className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${INDICATOR_CHIP[ind.indicator] || INDICATOR_CHIP.default}`}
              title={ind.reasoning}
            >
              {ind.indicator.replace(/_/g, ' ')} {(ind.confidence * 100).toFixed(0)}%
            </span>
          ))}
          {indicators.length === 0 && <span className="text-slate-300">—</span>}
        </div>
      </td>
    </tr>
  )
}

export default function InvestigationDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [inv, setInv] = useState<InvestigationDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const data = await api.getInvestigation(params.id as string)
      setInv(data)
    } catch {
      setError('Investigation not found')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [params.id])

  const handleDecision = async (decision: 'approve' | 'dismiss', notes: string) => {
    await api.decideSTR(params.id as string, decision, notes)
    await load()
  }

  if (loading) return <div className="py-20 text-center text-slate-400">Loading…</div>
  if (error || !inv) return <div className="py-20 text-center text-slate-400">{error}</div>

  const taggedTxns: TaggedTransaction[] = inv.str_draft?.tagged_transactions || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">
              <Link href={`/clients/${inv.client_id}`} className="hover:underline text-indigo-700">
                {inv.client_name}
              </Link>
            </h1>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_COLORS[inv.status] || ''}`}>
              {inv.status.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">{inv.id}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {inv.classification && (
            <div className="text-sm font-semibold text-slate-700">
              {inv.classification.replace(/_/g, ' ')}
              {inv.confidence !== null && (
                <span className="text-slate-400 font-normal ml-1">({inv.confidence?.toFixed(0)}% confidence)</span>
              )}
            </div>
          )}
          {inv.is_coordinated && (
            <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
              Coordinated — {inv.correlated_client_ids.length + 1} linked clients
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Money Flow Graph */}
        {inv.str_draft?.money_flow?.nodes?.length ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-3">Money Flow</h2>
            <MoneyFlowGraph data={inv.str_draft.money_flow} />
          </div>
        ) : null}

        {/* Cross-client network */}
        {inv.is_coordinated && inv.network_graph?.nodes?.length ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-slate-700 mb-1">Cross-Client Network</h2>
            <p className="text-xs text-slate-400 mb-3">
              Clients D, E, F sent funds to wallets in the same cluster
            </p>
            <CrossClientNetwork data={inv.network_graph} />
          </div>
        ) : null}
      </div>

      {/* Transaction timeline */}
      {taggedTxns.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-700">Transaction Timeline — FINTRAC Tagged</h2>
          </div>
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="w-full">
              <thead className="bg-slate-50 sticky top-0">
                <tr>
                  {['Date', 'Type', 'Product', 'Amount', 'Counterparty', 'Indicators'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {taggedTxns.map((t) => <TransactionRow key={t.id} txn={t} />)}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AI Reasoning */}
      {inv.reasoning && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-2">AI Classification Reasoning</h2>
          <p className="text-sm text-slate-600 leading-relaxed">{inv.reasoning}</p>
        </div>
      )}

      {/* STR Review (Layer 4 human decision) */}
      {inv.str_draft && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">
            Layer 4 — Human Decision
          </h2>
          <STRReview
            draft={inv.str_draft}
            investigationId={inv.id}
            onDecision={handleDecision}
          />
        </div>
      )}
    </div>
  )
}
