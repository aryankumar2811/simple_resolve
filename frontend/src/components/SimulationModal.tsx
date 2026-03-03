'use client'
import { useEffect, useRef } from 'react'
import Link from 'next/link'
import { useSimulation, SimClientState } from '@/context/SimulationContext'

function LayerBadge({ layer }: { layer: number }) {
  const config = {
    1: { label: 'L1', cls: 'bg-indigo-100 text-indigo-700 border-indigo-200' },
    2: { label: 'L2', cls: 'bg-amber-100 text-amber-700 border-amber-200' },
    3: { label: 'L3', cls: 'bg-orange-100 text-orange-700 border-orange-200' },
  }[layer] || { label: `L${layer}`, cls: 'bg-slate-100 text-slate-600 border-slate-200' }
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold border ${config.cls}`}>
      {config.label}
    </span>
  )
}

function ActionIcon({ type }: { type: string | null }) {
  if (!type) return null
  const icons: Record<string, string> = {
    notification_sent: '🔔',
    step_up_auth: '🔐',
    follow_up_call_scheduled: '📞',
    info_request_sent: '📧',
    auto_de_escalated: '↓',
    guardrail_intercept: '🛡',
  }
  return <span className="text-sm mr-1">{icons[type] || ''}</span>
}

function OutcomeBadge({ client }: { client: SimClientState }) {
  if (client.status === 'pending') {
    return <span className="text-xs text-slate-400 font-medium">Pending</span>
  }
  if (client.status === 'error') {
    return <span className="text-xs text-red-500 font-medium">Error</span>
  }
  if (client.status === 'running') {
    return (
      <span className="text-xs text-indigo-600 font-medium flex items-center gap-1">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
        Running
      </span>
    )
  }
  // complete
  const level = client.outcome.level
  const classification = client.outcome.classification
  if (level === null) return <span className="text-xs text-green-600 font-medium">Done</span>

  const labels: Record<number, { label: string; cls: string }> = {
    0: { label: 'Resolved', cls: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
    1: { label: 'L1: Monitoring', cls: 'text-blue-700 bg-blue-50 border-blue-200' },
    2: { label: 'L2: Guardrail', cls: 'text-amber-700 bg-amber-50 border-amber-200' },
    3: { label: 'L3: Investigation', cls: 'text-orange-700 bg-orange-50 border-orange-200' },
    4: { label: 'L4: Frozen', cls: 'text-red-700 bg-red-50 border-red-200' },
  }
  const cfg = labels[level] || { label: `L${level}`, cls: 'text-slate-700 bg-slate-50 border-slate-200' }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}

function ClientStatusIcon({ status }: { status: SimClientState['status'] }) {
  if (status === 'pending') return <span className="text-slate-300 text-lg">○</span>
  if (status === 'error') return <span className="text-red-500 text-lg">✕</span>
  if (status === 'complete') return <span className="text-emerald-500 text-lg">✓</span>
  // running
  return (
    <svg className="animate-spin h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

export function InlineSimulationPanel() {
  const { clients, activeClientIndex, allComplete, isRunning, expandModal, displayMode } = useSimulation()
  const inlineStepRef = useRef<HTMLDivElement>(null)
  const activeClient = clients[activeClientIndex]

  useEffect(() => {
    if (inlineStepRef.current) {
      inlineStepRef.current.scrollTop = inlineStepRef.current.scrollHeight
    }
  }, [activeClient?.steps?.length])

  // Only show when simulation is active and in inline mode
  if (clients.length === 0 || displayMode === 'expanded') return null

  const completedCount = clients.filter(c => c.status === 'complete' || c.status === 'error').length
  const pct = clients.length > 0 ? (completedCount / clients.length) * 100 : 0
  const recentSteps = activeClient?.steps?.slice(-4) || []

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
      {/* Compact header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2.5">
          {isRunning && (
            <svg className="animate-spin h-3.5 w-3.5 text-indigo-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {allComplete && <span className="text-emerald-500 text-sm">✓</span>}
          <span className="text-xs font-semibold text-slate-700">
            {allComplete ? 'Simulation Complete' : 'AML Pipeline Running'}
          </span>
          <span className="text-xs text-slate-400 font-mono">
            {completedCount}/{clients.length} clients
          </span>
          {activeClient && isRunning && (
            <span className="text-xs text-indigo-600 font-medium">
              · {activeClient.clientName}
            </span>
          )}
        </div>
        <button
          onClick={expandModal}
          className="text-xs text-indigo-600 hover:text-indigo-800 font-medium px-2 py-1 rounded hover:bg-indigo-50 transition-colors"
        >
          Expand
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-slate-100">
        <div
          className="h-full bg-indigo-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Recent steps (last 4) */}
      <div ref={inlineStepRef} className="px-4 py-2 space-y-1.5 max-h-40 overflow-y-auto">
        {recentSteps.length === 0 && isRunning && (
          <div className="flex items-center gap-2 text-slate-400 text-xs py-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            Initializing pipeline...
          </div>
        )}
        {recentSteps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <LayerBadge layer={step.layer} />
            <span className="font-medium text-slate-700 truncate flex-1">{step.label}</span>
            <span className="text-[10px] text-slate-400 font-mono shrink-0">
              {new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>
        ))}
        {isRunning && recentSteps.length > 0 && (
          <div className="flex items-center gap-1.5 text-[11px] text-indigo-500">
            <span className="inline-block w-1 h-1 rounded-full bg-indigo-400 animate-pulse" />
            Processing...
          </div>
        )}
      </div>

      {/* Completed client chips */}
      {completedCount > 0 && (
        <div className="px-4 py-2 border-t border-slate-100 flex flex-wrap gap-1.5">
          {clients.filter(c => c.status === 'complete').slice(0, 8).map(c => (
            <span key={c.clientId} className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-slate-50 border border-slate-200 text-slate-600">
              <span className="text-emerald-500">✓</span>
              {c.clientName}
              {c.outcome.level !== null && (
                <span className={`font-semibold ${c.outcome.level === 0 ? 'text-emerald-600' : c.outcome.level <= 2 ? 'text-amber-600' : 'text-orange-600'}`}>
                  {c.outcome.level === 0 ? 'OK' : `L${c.outcome.level}`}
                </span>
              )}
            </span>
          ))}
          {completedCount > 8 && (
            <span className="text-[10px] text-slate-400">+{completedCount - 8} more</span>
          )}
        </div>
      )}
    </div>
  )
}

export default function SimulationModal() {
  const { isModalOpen, displayMode, clients, activeClientIndex, allComplete, isRunning, closeModal, collapseToInline } = useSimulation()
  const stepListRef = useRef<HTMLDivElement>(null)
  const activeClient = clients[activeClientIndex]

  // Auto-scroll step list to bottom
  useEffect(() => {
    if (stepListRef.current) {
      stepListRef.current.scrollTop = stepListRef.current.scrollHeight
    }
  }, [activeClient?.steps?.length])

  if (!isModalOpen || displayMode !== 'expanded') return null

  const completedCount = clients.filter(c => c.status === 'complete' || c.status === 'error').length
  const firstInvestigationId = clients.find(c => c.investigationId)?.investigationId

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        onClick={allComplete ? closeModal : undefined}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-[90vw] max-w-5xl h-[80vh] flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200 bg-slate-50 shrink-0">
          <div className="flex items-center gap-3">
            {isRunning && (
              <svg className="animate-spin h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {allComplete && <span className="text-emerald-500">✓</span>}
            <h2 className="font-semibold text-slate-900 text-sm">
              {allComplete ? 'Simulation Complete' : 'Running AML Simulation Pipeline'}
            </h2>
            <span className="text-xs text-slate-500 font-mono">
              {completedCount} / {clients.length} clients processed
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={collapseToInline}
              className="text-xs text-slate-500 hover:text-slate-700 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
            >
              Collapse
            </button>
            {allComplete && (
              <button
                onClick={closeModal}
                className="text-slate-400 hover:text-slate-700 text-lg leading-none"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-slate-100 shrink-0">
          <div
            className="h-full bg-indigo-500 transition-all duration-500"
            style={{ width: `${clients.length > 0 ? (completedCount / clients.length) * 100 : 0}%` }}
          />
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left panel - client queue */}
          <div className="w-64 border-r border-slate-200 flex flex-col bg-slate-50 shrink-0">
            <div className="px-4 py-2.5 border-b border-slate-200">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Client Queue</p>
            </div>
            <div className="flex-1 overflow-y-auto">
              {clients.map((client, idx) => (
                <div
                  key={client.clientId}
                  className={`flex items-start gap-2.5 px-4 py-3 border-b border-slate-100 ${
                    idx === activeClientIndex ? 'bg-indigo-50' : ''
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    <ClientStatusIcon status={client.status} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-medium truncate ${
                      idx === activeClientIndex ? 'text-indigo-700' : 'text-slate-700'
                    }`}>{client.clientName}</p>
                    <div className="mt-1">
                      <OutcomeBadge client={client} />
                    </div>
                    {client.investigationId && client.status === 'complete' && (
                      <Link
                        href={`/investigations/${client.investigationId}`}
                        className="text-[10px] text-indigo-500 hover:underline mt-0.5 block"
                        onClick={closeModal}
                      >
                        View report →
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right panel - step log */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {activeClient ? (
              <>
                <div className="px-5 py-2.5 border-b border-slate-100 bg-white shrink-0 flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900">{activeClient.clientName}</span>
                  <span className="text-slate-400 text-xs">· Layer 1 → Layer 2 → Layer 3</span>
                </div>
                <div ref={stepListRef} className="flex-1 overflow-y-auto px-5 py-3 space-y-2">
                  {activeClient.steps.length === 0 && activeClient.status === 'running' && (
                    <div className="flex items-center gap-2 text-slate-400 text-sm py-4">
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Initializing pipeline...
                    </div>
                  )}
                  {activeClient.steps.map((step, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 text-sm py-1.5 border-b border-slate-50 last:border-0"
                    >
                      <LayerBadge layer={step.layer} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <ActionIcon type={step.action_type} />
                          <span className="font-medium text-slate-800 text-xs">{step.label}</span>
                        </div>
                        {step.details && (
                          <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{step.details}</p>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono shrink-0 mt-0.5">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                  {activeClient.status === 'running' && activeClient.steps.length > 0 && (
                    <div className="flex items-center gap-2 text-xs text-indigo-500 py-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                      Processing...
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
                Select a client to view steps
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        {allComplete && (
          <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 shrink-0 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              All {clients.length} clients processed. Dashboard will refresh automatically.
            </p>
            <div className="flex gap-2">
              {firstInvestigationId && (
                <Link
                  href={`/investigations/${firstInvestigationId}`}
                  onClick={closeModal}
                  className="text-xs bg-indigo-600 text-white px-4 py-1.5 rounded font-medium hover:bg-indigo-700 transition-colors"
                >
                  View First Investigation →
                </Link>
              )}
              <button
                onClick={closeModal}
                className="text-xs bg-white border border-slate-200 text-slate-700 px-4 py-1.5 rounded font-medium hover:bg-slate-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
