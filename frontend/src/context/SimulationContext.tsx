'use client'
import { createContext, useContext, useState, useCallback, useRef, ReactNode } from 'react'
import { api, StepLogEntry } from '@/lib/api'

interface SimulationState {
  investigationId: string | null
  clientId: string | null
  clientName: string
  steps: StepLogEntry[]
  status: 'idle' | 'running' | 'complete' | 'error'
  expanded: boolean
}

interface SimulationContextValue extends SimulationState {
  startSimulation: (clientId: string, clientName: string) => Promise<void>
  dismissSimulation: () => void
  toggleExpanded: () => void
}

const SimulationContext = createContext<SimulationContextValue | null>(null)

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SimulationState>({
    investigationId: null,
    clientId: null,
    clientName: '',
    steps: [],
    status: 'idle',
    expanded: false,
  })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startSimulation = useCallback(async (clientId: string, clientName: string) => {
    stopPolling()
    setState(prev => ({
      ...prev,
      investigationId: null,
      clientId,
      clientName,
      steps: [],
      status: 'running',
      expanded: false,
    }))

    try {
      const res = await api.simulate(clientId)
      const invId = res.investigation_id

      setState(prev => ({ ...prev, investigationId: invId }))

      // Poll for step progress
      pollRef.current = setInterval(async () => {
        try {
          const inv = await api.getInvestigation(invId)
          const steps = inv.step_log || []

          const isDone = [
            'str_drafted', 'de_escalated', 'fast_tracked', 'filed', 'dismissed'
          ].includes(inv.status) || steps.some(s => s.step === 'complete' || s.step === 'str_complete')

          setState(prev => ({
            ...prev,
            steps,
            status: isDone ? 'complete' : 'running',
          }))

          if (isDone) {
            stopPolling()
          }
        } catch {
          // polling errors are non-fatal
        }
      }, 900)
    } catch (err) {
      setState(prev => ({ ...prev, status: 'error' }))
    }
  }, [stopPolling])

  const dismissSimulation = useCallback(() => {
    stopPolling()
    setState({
      investigationId: null,
      clientId: null,
      clientName: '',
      steps: [],
      status: 'idle',
      expanded: false,
    })
  }, [stopPolling])

  const toggleExpanded = useCallback(() => {
    setState(prev => ({ ...prev, expanded: !prev.expanded }))
  }, [])

  return (
    <SimulationContext.Provider value={{ ...state, startSimulation, dismissSimulation, toggleExpanded }}>
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const ctx = useContext(SimulationContext)
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider')
  return ctx
}
