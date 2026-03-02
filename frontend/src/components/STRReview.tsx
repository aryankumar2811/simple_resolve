'use client'
import { useState } from 'react'
import type { STRDraft } from '@/lib/api'

interface Props {
  draft: STRDraft
  investigationId: string
  onDecision: (decision: 'approve' | 'dismiss', notes: string) => Promise<void>
}

const INDICATOR_COLORS: Record<string, string> = {
  structuring: 'bg-red-100 text-red-700',
  layering: 'bg-orange-100 text-orange-700',
  rapid_crypto_conversion: 'bg-amber-100 text-amber-700',
  income_inconsistency: 'bg-yellow-100 text-yellow-700',
  new_counterparty_burst: 'bg-purple-100 text-purple-700',
  velocity_anomaly: 'bg-pink-100 text-pink-700',
  default: 'bg-slate-100 text-slate-700',
}

function IndicatorChip({ indicator, confidence }: { indicator: string; confidence: number }) {
  const cls = INDICATOR_COLORS[indicator] || INDICATOR_COLORS.default
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {indicator.replace(/_/g, ' ')}
      <span className="opacity-70">{(confidence * 100).toFixed(0)}%</span>
    </span>
  )
}

export default function STRReview({ draft, investigationId, onDecision }: Props) {
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [showReasoning, setShowReasoning] = useState(false)

  const handle = async (decision: 'approve' | 'dismiss') => {
    setLoading(true)
    await onDecision(decision, notes)
    setLoading(false)
  }

  if (draft.status !== 'draft') {
    return (
      <div className={`rounded-lg border p-4 text-sm font-medium ${
        draft.status === 'approved' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-slate-50 border-slate-200 text-slate-500'
      }`}>
        STR {draft.status === 'approved' ? '✓ Approved and filed with FINTRAC' : '✗ Dismissed'}
        {draft.analyst_notes && <p className="mt-1 font-normal">{draft.analyst_notes}</p>}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Indicators summary */}
      {draft.indicators_present.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            FINTRAC Indicators Detected
          </p>
          <div className="flex flex-wrap gap-2">
            {draft.indicators_present.map((ind, i) => (
              <IndicatorChip key={i} indicator={ind.indicator} confidence={ind.confidence} />
            ))}
          </div>
        </div>
      )}

      {/* Narrative */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Draft STR Narrative
        </p>
        <div className="bg-slate-950 rounded-lg p-4 max-h-80 overflow-y-auto">
          <pre className="text-xs text-slate-200 whitespace-pre-wrap font-mono leading-relaxed">
            {draft.narrative_full || 'Narrative not yet generated.'}
          </pre>
        </div>
      </div>

      {/* Key uncertainties */}
      {draft.key_uncertainties.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-amber-700 mb-1">Key Uncertainties</p>
          <ul className="list-disc list-inside text-xs text-amber-600 space-y-0.5">
            {draft.key_uncertainties.map((u, i) => <li key={i}>{u}</li>)}
          </ul>
        </div>
      )}

      {/* AI reasoning (collapsible) */}
      {draft.ai_reasoning_chain && (
        <div>
          <button
            className="text-xs text-slate-400 hover:text-slate-600 underline"
            onClick={() => setShowReasoning(!showReasoning)}
          >
            {showReasoning ? 'Hide' : 'Show'} AI reasoning chain
          </button>
          {showReasoning && (
            <div className="mt-2 bg-slate-50 border border-slate-200 rounded p-3 text-xs text-slate-600 whitespace-pre-wrap">
              {draft.ai_reasoning_chain}
            </div>
          )}
        </div>
      )}

      {/* Analyst decision */}
      <div className="border-t border-slate-200 pt-4">
        <p className="text-sm font-semibold text-slate-700 mb-2">Analyst Decision</p>
        <textarea
          className="w-full border border-slate-300 rounded-lg p-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          rows={3}
          placeholder="Add notes (optional)…"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className="flex gap-3 mt-3">
          <button
            disabled={loading}
            onClick={() => handle('approve')}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
          >
            ✓ Approve & File STR
          </button>
          <button
            disabled={loading}
            onClick={() => handle('dismiss')}
            className="flex-1 bg-slate-200 hover:bg-slate-300 disabled:opacity-50 text-slate-700 text-sm font-semibold py-2 rounded-lg transition-colors"
          >
            ✗ Dismiss
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Under s. 7 of the PCMLTFA, filing is a legal act that requires
          human sign-off. SimpleResolve never files automatically.
        </p>
      </div>
    </div>
  )
}
