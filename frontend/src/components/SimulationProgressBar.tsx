'use client'
import { useSimulation } from '@/context/SimulationContext'
import Link from 'next/link'

const LAYER_COLOR: Record<number, string> = {
  1: 'text-indigo-400',
  2: 'text-amber-400',
  3: 'text-orange-400',
}

const LAYER_BADGE: Record<number, string> = {
  1: 'bg-indigo-900/60 text-indigo-300 border border-indigo-700/40',
  2: 'bg-amber-900/60 text-amber-300 border border-amber-700/40',
  3: 'bg-orange-900/60 text-orange-300 border border-orange-700/40',
}

const LAYER_LABEL: Record<number, string> = {
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

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-indigo-400 shrink-0" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg className="h-4 w-4 text-emerald-400 shrink-0" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
    </svg>
  )
}

export default function SimulationProgressBar() {
  const { status, clientName, steps, expanded, investigationId, toggleExpanded, dismissSimulation } = useSimulation()

  if (status === 'idle') return null

  const currentStep = steps[steps.length - 1]
  const isDone = status === 'complete'

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 shadow-2xl">
      {/* Expanded drawer */}
      {expanded && (
        <div
          className="bg-[#0d0d14] border-t border-slate-700/60 max-h-72 overflow-y-auto"
          style={{ scrollbarWidth: 'thin' }}
        >
          <div className="px-4 pt-3 pb-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
              Pipeline Steps — {clientName}
            </p>
            <div className="space-y-1.5 pb-2">
              {steps.map((step, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <div className="mt-0.5 shrink-0">
                    <CheckIcon />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${LAYER_BADGE[step.layer] || 'bg-slate-800 text-slate-400'}`}>
                        {LAYER_LABEL[step.layer] || `Layer ${step.layer}`}
                      </span>
                      {step.action_type && (
                        <span className="text-xs">{ACTION_ICON[step.action_type] || ''}</span>
                      )}
                      <span className="text-xs font-medium text-slate-200">{step.label}</span>
                    </div>
                    {step.details && (
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{step.details}</p>
                    )}
                  </div>
                  <span className="text-xs text-slate-600 whitespace-nowrap shrink-0 mt-0.5">
                    {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
              ))}
              {steps.length === 0 && (
                <p className="text-xs text-slate-500 py-2">Initialising pipeline…</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Collapsed bar */}
      <div className="bg-[#0d0d14] border-t border-slate-700/60 px-4 py-2.5 flex items-center gap-3">
        <div className="flex items-center gap-2 shrink-0">
          {isDone ? <CheckIcon /> : <Spinner />}
          <span className="text-xs font-semibold text-slate-300">{clientName}</span>
        </div>

        <div className="flex-1 min-w-0">
          {isDone ? (
            <span className="text-xs text-emerald-400 font-medium">
              Analysis complete
              {investigationId && (
                <> — <Link href={`/investigations/${investigationId}`} className="underline hover:text-emerald-300">View Report →</Link></>
              )}
            </span>
          ) : (
            <span className={`text-xs truncate ${currentStep ? LAYER_COLOR[currentStep.layer] : 'text-slate-400'}`}>
              {currentStep?.label || 'Starting pipeline…'}
            </span>
          )}
        </div>

        {/* Step count */}
        {steps.length > 0 && (
          <span className="text-xs text-slate-500 shrink-0 font-mono">{steps.length} steps</span>
        )}

        {/* Expand/collapse toggle */}
        <button
          onClick={toggleExpanded}
          className="text-slate-400 hover:text-slate-200 transition-colors shrink-0 ml-1"
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          <svg className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
        </button>

        {/* Dismiss */}
        {isDone && (
          <button
            onClick={dismissSimulation}
            className="text-slate-500 hover:text-slate-300 transition-colors shrink-0"
            aria-label="Dismiss"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}
