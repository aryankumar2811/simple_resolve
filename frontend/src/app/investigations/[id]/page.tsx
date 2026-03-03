'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api, InvestigationDetail, TaggedTransaction, StepLogEntry } from '@/lib/api'
import MoneyFlowGraph from '@/components/MoneyFlowGraph'
import CrossClientNetwork from '@/components/CrossClientNetwork'
import SupervisorModal from '@/components/SupervisorModal'

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

const LAYER_BADGE: Record<number, string> = {
  1: 'bg-indigo-100 text-indigo-700',
  2: 'bg-amber-100 text-amber-700',
  3: 'bg-orange-100 text-orange-700',
}
const LAYER_LABELS: Record<number, string> = {
  1: 'L1 Behavioral',
  2: 'L2 Response',
  3: 'L3 Orchestrator',
}

const ACTION_ICON: Record<string, string> = {
  notification_sent: '🔔',
  step_up_auth: '🔒',
  follow_up_call_scheduled: '📞',
  info_request_sent: '📋',
  auto_de_escalated: '✅',
  guardrail_intercept: '⚡',
  coordinated_alert: '🔗',
}

const ALL_INDICATORS = [
  { id: 'structuring', label: 'Structuring or Smurfing' },
  { id: 'layering', label: 'Layering: multi-product conversion' },
  { id: 'rapid_crypto_conversion', label: 'Rapid cryptocurrency conversion / exit' },
  { id: 'income_inconsistency', label: 'Income inconsistency: deposits exceed stated income' },
  { id: 'new_counterparty_burst', label: 'New counterparty burst: sudden influx of senders' },
  { id: 'round_tripping', label: 'Round-tripping: funds returning through different channels' },
  { id: 'third_party_payments', label: 'Third-party payment pattern' },
  { id: 'sanctions_proximity', label: 'Sanctions or PEP proximity' },
  { id: 'high_volume_low_value', label: 'High-volume, low-value transaction pattern' },
]

type Tab = 'evidence' | 'fintrac' | 'steps' | 'audit'

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
      <td className="px-3 py-2 text-xs text-slate-500">{txn.counterparty_name || '-'}</td>
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
          {indicators.length === 0 && <span className="text-slate-300">-</span>}
        </div>
      </td>
    </tr>
  )
}

// ── Helpers for FINTRAC form ──────────────────────────────────────────────────

function FINTRACSection({ num, title, children }: { num: string; title: string; children: React.ReactNode }) {
  return (
    <div className="px-6 py-5">
      <div className="flex items-center gap-2.5 mb-4">
        <span className="text-[10px] font-bold text-white bg-slate-500 w-5 h-5 rounded flex items-center justify-center shrink-0 tabular-nums">
          {num}
        </span>
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">{label}</p>
      <div className="bg-white border border-slate-200 rounded-md px-3 py-2 text-sm text-slate-700">
        {value}
      </div>
    </div>
  )
}

// ── FINTRAC Document ──────────────────────────────────────────────────────────

function FINTRACDocument({ inv }: { inv: InvestigationDetail }) {
  const draft = inv.str_draft
  const [deciding, setDeciding] = useState(false)
  const [decided, setDecided] = useState(false)
  const [supervisorOpen, setSupervisorOpen] = useState(false)
  const [submitConfirm, setSubmitConfirm] = useState(false)
  const [activityText, setActivityText] = useState(draft?.activity_description ?? '')
  const [savedDraft, setSavedDraft] = useState(false)

  const handleDecision = async (decision: 'approve' | 'dismiss') => {
    setDeciding(true)
    setSubmitConfirm(false)
    try {
      await api.decideSTR(inv.id, decision, '')
      setDecided(true)
      window.location.reload()
    } catch {
      setDeciding(false)
    }
  }

  const handleSaveDraft = () => {
    setSavedDraft(true)
    setTimeout(() => setSavedDraft(false), 2000)
  }

  if (!draft) {
    return (
      <div className="py-16 text-center text-slate-400 text-sm">
        {inv.status === 'de_escalated'
          ? 'Investigation de-escalated. No STR required.'
          : 'FINTRAC document not yet generated.'}
      </div>
    )
  }

  const detectedIds = new Set(draft.indicators_present?.map(i => i.indicator) ?? [])
  const statusTag = draft.status === 'approved' ? 'FILED' : draft.status === 'dismissed' ? 'DISMISSED' : 'DRAFT'

  return (
    <>
      <SupervisorModal isOpen={supervisorOpen} onClose={() => setSupervisorOpen(false)} caseId={inv.id} />

      {/* Submit confirmation dialog */}
      {submitConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setSubmitConfirm(false)} />
          <div className="relative bg-white rounded-xl border border-slate-200 shadow-2xl p-6 max-w-md w-full">
            <h3 className="font-semibold text-slate-900 mb-2">Submit to FINTRAC?</h3>
            <p className="text-sm text-slate-600 mb-5 leading-relaxed">
              Under the PCMLTFA, filing this STR is a criminal act signed personally. By proceeding, you
              confirm the information is accurate to the best of your knowledge.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setSubmitConfirm(false)}
                className="text-sm px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDecision('approve')}
                disabled={deciding}
                className="text-sm px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-40 transition-colors"
              >
                Confirm & File STR
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl overflow-hidden border border-slate-200 shadow-sm">
        {/* Document header */}
        <div className="bg-white px-6 py-4 flex items-center justify-between flex-wrap gap-3 border-b border-slate-200">
          <div>
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">
              Proceeds of Crime (Money Laundering) and Terrorist Financing Act, S.7
            </p>
            <h2 className="text-base font-bold text-slate-900 mt-1">
              Suspicious Transaction Report: {statusTag}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Case #{inv.id.slice(0, 8).toUpperCase()} &nbsp;·&nbsp; Subject: {inv.client_name}
              &nbsp;·&nbsp; AI-generated · Pending human review
            </p>
          </div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
            statusTag === 'FILED'
              ? 'bg-purple-50 text-purple-700 border-purple-200'
              : statusTag === 'DISMISSED'
              ? 'bg-slate-100 text-slate-500 border-slate-200'
              : 'bg-amber-50 text-amber-700 border-amber-200'
          }`}>
            {statusTag}
          </span>
        </div>

        {/* Form body */}
        <div className="divide-y divide-slate-100 bg-slate-50">

          {/* 1 - Reporting Entity */}
          <FINTRACSection num="1" title="Reporting Entity">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <ReadonlyField label="Institution" value="SimpleResolve Financial Inc." />
              <ReadonlyField label="Compliance Officer" value="Jennifer Walsh, CAMS" />
              <ReadonlyField label="Branch / Jurisdiction" value="Toronto, ON, Canada" />
            </div>
          </FINTRACSection>

          {/* 2 - Subject Profile */}
          {draft.subject_profile && (
            <FINTRACSection num="2" title="Subject Profile">
              <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                {draft.subject_profile}
              </p>
            </FINTRACSection>
          )}

          {/* 3 - Transaction Details */}
          {draft.tagged_transactions?.length > 0 && (
            <FINTRACSection num="3" title="Transaction Details">
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      {['Date', 'Type', 'Product', 'Amount', 'Counterparty', 'Indicators'].map(h => (
                        <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-slate-500">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {draft.tagged_transactions.map((t: TaggedTransaction) => (
                      <TransactionRow key={t.id} txn={t} />
                    ))}
                  </tbody>
                </table>
              </div>
            </FINTRACSection>
          )}

          {/* 4 - Suspicious Activity Description */}
          <FINTRACSection num="4" title="Suspicious Activity Description">
            <p className="text-xs text-slate-400 mb-2">
              AI-generated narrative. Edit before filing if needed.
            </p>
            <textarea
              value={activityText}
              onChange={e => setActivityText(e.target.value)}
              rows={6}
              disabled={draft.status !== 'draft'}
              className="w-full text-sm text-slate-700 border border-slate-200 rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none bg-white disabled:bg-slate-50 disabled:text-slate-500"
            />
          </FINTRACSection>

          {/* 4b - AI Investigation Narrative */}
          {draft.narrative_full ? (
            <FINTRACSection num="4b" title="AI Investigation Narrative">
              <p className="text-xs text-slate-400 mb-2">
                Full narrative generated by the investigation orchestrator.
              </p>
              <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {draft.narrative_full}
                </p>
              </div>
            </FINTRACSection>
          ) : (
            <FINTRACSection num="4b" title="AI Investigation Narrative">
              <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-6 text-center">
                <p className="text-xs text-slate-400">
                  Narrative will be generated when the simulation pipeline runs. Use the Dashboard to trigger a simulation.
                </p>
              </div>
            </FINTRACSection>
          )}

          {/* 5 - FINTRAC Indicators Checklist */}
          <FINTRACSection num="5" title="FINTRAC Indicators Checklist">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {ALL_INDICATORS.map(ind => {
                const detected = detectedIds.has(ind.id)
                const detail = draft.indicators_present?.find(i => i.indicator === ind.id)
                return (
                  <label
                    key={ind.id}
                    className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-default ${
                      detected ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200 opacity-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      readOnly
                      checked={detected}
                      className="mt-0.5 rounded accent-red-600 shrink-0"
                    />
                    <div className="min-w-0">
                      <p className={`text-xs font-semibold ${detected ? 'text-red-700' : 'text-slate-500'}`}>
                        {ind.label}
                      </p>
                      {detected && detail?.reasoning && (
                        <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                          {detail.reasoning}
                        </p>
                      )}
                      {detected && detail?.confidence && (
                        <p className="text-[10px] text-red-500 font-medium mt-0.5">
                          {(detail.confidence * 100).toFixed(0)}% confidence
                        </p>
                      )}
                    </div>
                  </label>
                )
              })}
            </div>
          </FINTRACSection>

          {/* 6 - Supporting Documents */}
          <FINTRACSection num="6" title="Supporting Documents">
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center bg-white">
              <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-sm text-slate-500">Drop files here or click to attach</p>
              <p className="text-xs text-slate-400 mt-1">KYC documents, transaction receipts, correspondence</p>
              <div className="mt-3 flex gap-2 justify-center flex-wrap">
                {['KYC_Identification.pdf', 'Transaction_History.csv'].map(f => (
                  <span key={f} className="text-xs bg-slate-100 border border-slate-200 text-slate-600 px-2.5 py-1 rounded-full flex items-center gap-1">
                    <svg className="w-3 h-3 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                    </svg>
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </FINTRACSection>

          {/* 7 - AI Analysis */}
          <FINTRACSection num="7" title="AI Analysis">
            <div className="space-y-4">
              {draft.ai_confidence != null && (
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide w-24 shrink-0">
                    Confidence
                  </span>
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-indigo-500 transition-all"
                      style={{ width: `${draft.ai_confidence}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-indigo-700 w-12 text-right tabular-nums">
                    {draft.ai_confidence?.toFixed(0)}%
                  </span>
                </div>
              )}
              {draft.behavioral_context && (
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                    Behavioral Context
                  </p>
                  <p className="text-sm text-slate-600 leading-relaxed">{draft.behavioral_context}</p>
                </div>
              )}
              {draft.network_analysis && (
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                    Network Analysis
                  </p>
                  <p className="text-sm text-slate-600 leading-relaxed">{draft.network_analysis}</p>
                </div>
              )}
              {draft.recommendation && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-3">
                  <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">
                    AI Recommendation
                  </p>
                  <p className="text-sm text-indigo-800 font-medium">{draft.recommendation}</p>
                </div>
              )}
            </div>
          </FINTRACSection>

          {/* 8 - Key Uncertainties */}
          {draft.key_uncertainties?.length > 0 && (
            <FINTRACSection num="8" title="Key Uncertainties">
              <ul className="space-y-2">
                {draft.key_uncertainties.map((u, i) => (
                  <li key={i} className="flex gap-2.5 text-sm text-slate-600">
                    <span className="text-amber-500 shrink-0 font-bold">{i + 1}.</span>
                    <span className="leading-relaxed">{u}</span>
                  </li>
                ))}
              </ul>
            </FINTRACSection>
          )}
        </div>

        {/* Sticky action footer - draft */}
        {draft.status === 'draft' && (
          <div className="bg-white border-t border-slate-200 px-6 py-4 flex items-center justify-between gap-4 flex-wrap sticky bottom-0">
            <p className="text-xs text-slate-400">
              Layer 4: Human Decision &nbsp;·&nbsp; Under PCMLTFA, the filing analyst signs personally
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={handleSaveDraft}
                className="text-xs px-3 py-1.5 border border-slate-200 rounded-md text-slate-600 hover:bg-slate-50 transition-colors"
              >
                {savedDraft ? 'Saved ✓' : 'Save Draft'}
              </button>
              <button
                onClick={() => setSupervisorOpen(true)}
                className="text-xs px-3 py-1.5 border border-amber-300 rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors font-medium"
              >
                Raise to Supervisor
              </button>
              <button
                onClick={() => handleDecision('dismiss')}
                disabled={deciding || decided}
                className="text-xs px-3 py-1.5 border border-slate-200 rounded-md text-slate-500 hover:bg-slate-50 transition-colors disabled:opacity-40"
              >
                Dismiss
              </button>
              <button
                onClick={() => setSubmitConfirm(true)}
                disabled={deciding || decided}
                className="text-xs px-4 py-1.5 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 transition-colors disabled:opacity-40"
              >
                Submit to FINTRAC
              </button>
            </div>
          </div>
        )}

        {/* Filed / dismissed footer */}
        {(draft.status === 'approved' || draft.status === 'dismissed') && (
          <div className="bg-white border-t border-slate-200 px-6 py-3 text-center">
            <span className={`text-xs font-medium ${
              draft.status === 'approved' ? 'text-purple-600' : 'text-slate-400'
            }`}>
              {draft.status === 'approved'
                ? `Filed by ${draft.decided_by ?? 'analyst'} on ${draft.decided_at ? new Date(draft.decided_at).toLocaleDateString() : '-'}`
                : `Dismissed by ${draft.decided_by ?? 'analyst'}`}
              {draft.analyst_notes && ` · ${draft.analyst_notes}`}
            </span>
          </div>
        )}
      </div>
    </>
  )
}

// ── Helpers for structured step details ──────────────────────────────────────

const DATA_LABELS: Record<string, string> = {
  txn_count: 'Transactions',
  products: 'Products',
  counterparty_count: 'Counterparties',
  risk_score: 'Risk Score',
  avg_deposit: 'Avg Deposit',
  avg_withdrawal: 'Avg Withdrawal',
  deposit_freq_per_week: 'Deposit Freq/Week',
  total_inflow_30d: 'Inflow (30d)',
  total_outflow_30d: 'Outflow (30d)',
  flagged_txn_count: 'Flagged Transactions',
  highest_confidence: 'Highest Confidence',
  indicator_breakdown: 'Indicators',
  node_count: 'Graph Nodes',
  edge_count: 'Graph Edges',
  total_flow: 'Total Flow',
  external_destinations: 'External Destinations',
  linked_clients: 'Linked Clients',
  wallet_clusters: 'Wallet Clusters',
  link_types: 'Link Types',
  classification: 'Classification',
  confidence: 'Confidence',
  key_factors: 'Key Factors',
  reasoning: 'Reasoning',
  narrative_length: 'Narrative Length',
  sections: 'Sections',
  recommendation: 'Recommendation',
  level: 'Response Level',
  restricted: 'Restricted Capabilities',
  allowed: 'Allowed Capabilities',
  trigger_type: 'Trigger Type',
  archetype: 'Archetype',
  trajectory: 'Trajectory',
  indicators: 'Indicators',
}

function parseStepDetails(details: string): { summary: string; data: Record<string, unknown> } | null {
  try {
    const parsed = JSON.parse(details)
    if (parsed && typeof parsed === 'object' && 'summary' in parsed) {
      return parsed as { summary: string; data: Record<string, unknown> }
    }
  } catch {
    // Not JSON - return null for plain string rendering
  }
  return null
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '-'
  if (typeof val === 'number') {
    if (val >= 1000) return `$${val.toLocaleString()}`
    if (val < 1 && val > 0) return `${(val * 100).toFixed(0)}%`
    return val.toLocaleString()
  }
  if (Array.isArray(val)) return val.join(', ') || '-'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

// ── Agent Steps tab ───────────────────────────────────────────────────────────

function AgentStepsTab({ stepLog }: { stepLog: StepLogEntry[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  if (!stepLog || stepLog.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-slate-400">
        No agent steps recorded. Run the simulate pipeline from the Dashboard.
      </div>
    )
  }

  const toggle = (idx: number) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-400">
        {stepLog.length} pipeline steps · Layer 1 (Behavioral) → Layer 2 (Response) → Layer 3 (Orchestrator)
      </p>
      <div className="relative">
        <div className="absolute left-3 top-0 bottom-0 w-px bg-slate-200" />
        <div className="space-y-3 pl-8">
          {stepLog.map((step, i) => {
            const parsed = step.details ? parseStepDetails(step.details) : null
            const isExpanded = expanded.has(i)
            const hasData = parsed && parsed.data && Object.keys(parsed.data).length > 0

            return (
              <div key={i} className="relative">
                <div className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-white" />
                <div
                  className={`bg-white rounded-lg border p-3 shadow-sm transition-colors ${
                    hasData ? 'cursor-pointer hover:border-indigo-200' : ''
                  } ${isExpanded ? 'border-indigo-200' : 'border-slate-100'}`}
                  onClick={() => hasData && toggle(i)}
                >
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${LAYER_BADGE[step.layer] || 'bg-slate-100 text-slate-600'}`}>
                      {LAYER_LABELS[step.layer] || `Layer ${step.layer}`}
                    </span>
                    {step.action_type && (
                      <span className="text-xs">{ACTION_ICON[step.action_type] || ''}</span>
                    )}
                    <span className="text-xs font-medium text-slate-700">{step.label}</span>
                    <span className="ml-auto flex items-center gap-1.5">
                      <span className="text-xs text-slate-400 font-mono">
                        {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                      {hasData && (
                        <svg
                          className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none" viewBox="0 0 24 24" stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </span>
                  </div>
                  {/* Summary line */}
                  {parsed ? (
                    <p className="text-xs text-slate-500 leading-relaxed">{parsed.summary}</p>
                  ) : step.details ? (
                    <p className="text-xs text-slate-500 leading-relaxed">{step.details}</p>
                  ) : null}

                  {/* Expanded data grid */}
                  {isExpanded && parsed?.data && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
                        {Object.entries(parsed.data).map(([key, val]) => (
                          <div key={key} className="flex justify-between text-xs gap-2">
                            <span className="text-slate-400 font-medium shrink-0">
                              {DATA_LABELS[key] || key.replace(/_/g, ' ')}
                            </span>
                            <span className="text-slate-700 font-mono text-right truncate">
                              {formatValue(val)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function InvestigationDetailPage() {
  const params = useParams()
  const [inv, setInv] = useState<InvestigationDetail | null>(null)
  const [auditLog, setAuditLog] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('fintrac')

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

  useEffect(() => {
    if (!params.id) return
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/investigations/${params.id}/audit`)
      .then(r => r.ok ? r.json() : [])
      .then(setAuditLog)
      .catch(() => {})
  }, [params.id])

  if (loading) return <div className="py-20 text-center text-slate-400">Loading…</div>
  if (error || !inv) return <div className="py-20 text-center text-slate-400">{error}</div>

  const taggedTxns: TaggedTransaction[] = inv.str_draft?.tagged_transactions || []

  const tabs: { id: Tab; label: string }[] = [
    { id: 'fintrac', label: 'FINTRAC Document' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'steps', label: `Agent Steps ${inv.step_log?.length ? `(${inv.step_log.length})` : ''}` },
    { id: 'audit', label: 'Audit' },
  ]

  return (
    <div className="space-y-5">
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
                <span className="text-slate-400 font-normal ml-1">
                  ({inv.confidence?.toFixed(0)}% confidence)
                </span>
              )}
            </div>
          )}
          {inv.is_coordinated && (
            <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
              Coordinated: {inv.correlated_client_ids.length + 1} linked clients
            </span>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === id
                ? 'border-indigo-600 text-indigo-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* FINTRAC Document tab */}
      {tab === 'fintrac' && <FINTRACDocument inv={inv} />}

      {/* Evidence tab */}
      {tab === 'evidence' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {inv.str_draft?.money_flow?.nodes?.length ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <h2 className="text-sm font-semibold text-slate-700 mb-3">Money Flow</h2>
                <MoneyFlowGraph data={inv.str_draft.money_flow} />
              </div>
            ) : null}
            {inv.is_coordinated && inv.network_graph?.nodes?.length ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                <h2 className="text-sm font-semibold text-slate-700 mb-1">Cross-Client Network</h2>
                <p className="text-xs text-slate-400 mb-3">
                  Clients share wallet cluster or temporal deposit pattern
                </p>
                <CrossClientNetwork data={inv.network_graph} />
              </div>
            ) : null}
          </div>

          {taggedTxns.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-200">
                <h2 className="text-sm font-semibold text-slate-700">Transaction Timeline: FINTRAC Tagged</h2>
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

          {inv.reasoning && (
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-5">
              <h2 className="text-sm font-semibold text-slate-700 mb-2">AI Classification Reasoning</h2>
              <p className="text-sm text-slate-600 leading-relaxed">{inv.reasoning}</p>
            </div>
          )}
        </div>
      )}

      {/* Agent Steps tab */}
      {tab === 'steps' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Agent Research Pipeline</h2>
          <AgentStepsTab stepLog={inv.step_log || []} />
        </div>
      )}

      {/* Audit tab */}
      {tab === 'audit' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-700">Audit Trail</h2>
          </div>
          <div className="divide-y divide-slate-50 max-h-96 overflow-y-auto">
            {auditLog.length === 0 && (
              <p className="px-5 py-4 text-sm text-slate-400">No audit entries.</p>
            )}
            {auditLog.map((entry: any) => (
              <div key={entry.id} className="flex items-start gap-3 px-5 py-2.5 text-sm">
                <span className="text-xs text-slate-400 font-mono whitespace-nowrap pt-0.5">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
                <span className="text-slate-700 flex-1">{entry.action.replace(/_/g, ' ')}</span>
                <span className="text-xs text-slate-400 shrink-0">{entry.actor}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
