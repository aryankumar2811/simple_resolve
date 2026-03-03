'use client'
import { useState } from 'react'

const ANALYSTS = [
  { name: 'Sarah Mitchell', role: 'Senior AML Analyst', caseload: 2 },
  { name: 'David Chen', role: 'Compliance Lead', caseload: 0 },
  { name: 'Aisha Okafor', role: 'AML Analyst', caseload: 4 },
  { name: 'Marcus Webb', role: 'Senior AML Analyst', caseload: 1 },
]

interface Props {
  isOpen: boolean
  onClose: () => void
  caseId: string
}

export default function SupervisorModal({ isOpen, onClose, caseId }: Props) {
  const [selected, setSelected] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [priority, setPriority] = useState<'normal' | 'urgent' | 'critical'>('normal')
  const [submitted, setSubmitted] = useState(false)

  if (!isOpen) return null

  const refNum = `CASE-${new Date().getFullYear()}-${caseId.slice(0, 4).toUpperCase()}`

  const handleSubmit = () => {
    if (!selected) return
    setSubmitted(true)
    setTimeout(() => {
      onClose()
      setSubmitted(false)
      setSelected(null)
      setNotes('')
      setPriority('normal')
    }, 2200)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={submitted ? undefined : onClose} />
      <div className="relative bg-white rounded-xl border border-slate-200 shadow-2xl w-full max-w-lg">
        {submitted ? (
          <div className="p-8 text-center">
            <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-900">Case Assigned</h3>
            <p className="text-sm text-slate-600 mt-1">
              Assigned to <span className="font-medium">{selected}</span>
            </p>
            <p className="text-xs text-slate-400 mt-2 font-mono">Reference: {refNum}</p>
          </div>
        ) : (
          <div className="p-6 space-y-5">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-900">Raise to Supervisor</h2>
                <p className="text-xs text-slate-500 mt-0.5">Assign case {refNum} for senior review</p>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-lg leading-none mt-0.5">✕</button>
            </div>

            {/* Analyst selection */}
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-2">
                Assign To
              </label>
              <div className="space-y-2">
                {ANALYSTS.map(analyst => (
                  <button
                    key={analyst.name}
                    onClick={() => setSelected(analyst.name)}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg border text-left transition-colors ${
                      selected === analyst.name
                        ? 'border-indigo-400 bg-indigo-50'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-900">{analyst.name}</p>
                      <p className="text-xs text-slate-500">{analyst.role}</p>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      analyst.caseload === 0
                        ? 'bg-emerald-100 text-emerald-700'
                        : analyst.caseload <= 2
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {analyst.caseload} active {analyst.caseload === 1 ? 'case' : 'cases'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Priority */}
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-2">
                Priority
              </label>
              <div className="flex gap-2">
                {(['normal', 'urgent', 'critical'] as const).map(p => (
                  <button
                    key={p}
                    onClick={() => setPriority(p)}
                    className={`flex-1 py-2 rounded-lg border text-xs font-semibold capitalize transition-colors ${
                      priority === p
                        ? p === 'critical'
                          ? 'bg-red-50 border-red-300 text-red-700'
                          : p === 'urgent'
                          ? 'bg-amber-50 border-amber-300 text-amber-700'
                          : 'bg-indigo-50 border-indigo-300 text-indigo-700'
                        : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-2">
                Notes for Supervisor
              </label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Add context or specific instructions for the reviewing analyst..."
                rows={3}
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 text-slate-700 placeholder:text-slate-400"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-1">
              <button
                onClick={onClose}
                className="text-sm px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!selected}
                className="text-sm px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Assign Case
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
