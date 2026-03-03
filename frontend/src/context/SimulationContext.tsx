'use client'
import { createContext, useContext, useState, useCallback, useRef, ReactNode } from 'react'
import { api, StepLogEntry } from '@/lib/api'

export interface SimClientState {
  clientId: string
  clientName: string
  status: 'pending' | 'running' | 'complete' | 'error'
  investigationId: string | null
  steps: StepLogEntry[]
  outcome: {
    level: number | null
    classification: string | null
    archetype: string | null
  }
}

interface MultiSimulationState {
  isRunning: boolean
  isModalOpen: boolean
  displayMode: 'inline' | 'expanded'
  clients: SimClientState[]
  activeClientIndex: number
  allComplete: boolean
  onComplete: (() => void) | null  // callback to refresh dashboard after done
}

interface SimulationContextValue extends MultiSimulationState {
  startSimulation: (clients: { clientId: string; clientName: string }[], onComplete?: () => void) => Promise<void>
  expandModal: () => void
  collapseToInline: () => void
  closeModal: () => void
  reset: () => void
}

const SimulationContext = createContext<SimulationContextValue | null>(null)

const TERMINAL_STATUSES = ['str_drafted', 'de_escalated', 'fast_tracked', 'filed', 'dismissed']
const TERMINAL_STEPS = ['complete', 'str_complete']

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<MultiSimulationState>({
    isRunning: false,
    isModalOpen: false,
    displayMode: 'inline',
    clients: [],
    activeClientIndex: 0,
    allComplete: false,
    onComplete: null,
  })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const runningRef = useRef(false)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const runClient = useCallback(async (
    clientId: string,
    clientName: string,
    index: number,
    total: number,
    onClientDone: (index: number, investigationId: string | null) => void
  ) => {
    // Mark this client as running
    setState(prev => {
      const clients = [...prev.clients]
      clients[index] = { ...clients[index], status: 'running' }
      return { ...prev, activeClientIndex: index, clients }
    })

    let investigationId: string | null = null

    try {
      const res = await api.simulate(clientId)
      investigationId = res.investigation_id

      setState(prev => {
        const clients = [...prev.clients]
        clients[index] = { ...clients[index], investigationId }
        return { ...prev, clients }
      })

      // Poll for steps
      await new Promise<void>((resolve) => {
        pollRef.current = setInterval(async () => {
          if (!runningRef.current) {
            stopPolling()
            resolve()
            return
          }
          try {
            const inv = await api.getInvestigation(investigationId!)
            const steps = inv.step_log || []
            const isDone =
              TERMINAL_STATUSES.includes(inv.status) ||
              steps.some(s => TERMINAL_STEPS.includes(s.step))

            setState(prev => {
              const clients = [...prev.clients]
              clients[index] = {
                ...clients[index],
                steps,
                outcome: {
                  level: null,
                  classification: inv.classification || null,
                  archetype: null,
                },
                status: isDone ? 'complete' : 'running',
              }
              return { ...prev, clients }
            })

            if (isDone) {
              stopPolling()
              // Fetch the updated client to get level + archetype
              try {
                const updatedClient = await api.getClient(clientId)
                setState(prev => {
                  const clients = [...prev.clients]
                  clients[index] = {
                    ...clients[index],
                    outcome: {
                      level: updatedClient.active_restriction_level,
                      classification: inv.classification || null,
                      archetype: updatedClient.archetype || null,
                    },
                  }
                  return { ...prev, clients }
                })
              } catch {
                // non-fatal
              }
              resolve()
            }
          } catch {
            // polling error - non-fatal, keep retrying
          }
        }, 900)
      })
    } catch {
      setState(prev => {
        const clients = [...prev.clients]
        clients[index] = { ...clients[index], status: 'error' }
        return { ...prev, clients }
      })
    }

    onClientDone(index, investigationId)
  }, [stopPolling])

  const startSimulation = useCallback(async (
    clientList: { clientId: string; clientName: string }[],
    onComplete?: () => void
  ) => {
    stopPolling()
    runningRef.current = true

    const initialClients: SimClientState[] = clientList.map(c => ({
      clientId: c.clientId,
      clientName: c.clientName,
      status: 'pending',
      investigationId: null,
      steps: [],
      outcome: { level: null, classification: null, archetype: null },
    }))

    setState({
      isRunning: true,
      isModalOpen: false,
      displayMode: 'inline',
      clients: initialClients,
      activeClientIndex: 0,
      allComplete: false,
      onComplete: onComplete || null,
    })

    // Run clients sequentially
    for (let i = 0; i < clientList.length; i++) {
      if (!runningRef.current) break
      await runClient(
        clientList[i].clientId,
        clientList[i].clientName,
        i,
        clientList.length,
        () => {}
      )
    }

    runningRef.current = false
    setState(prev => ({ ...prev, isRunning: false, allComplete: true }))

    // Trigger dashboard refresh
    if (onComplete) onComplete()
  }, [stopPolling, runClient])

  const expandModal = useCallback(() => {
    setState(prev => ({ ...prev, isModalOpen: true, displayMode: 'expanded' }))
  }, [])

  const collapseToInline = useCallback(() => {
    setState(prev => ({ ...prev, isModalOpen: false, displayMode: 'inline' }))
  }, [])

  const closeModal = useCallback(() => {
    setState(prev => ({ ...prev, isModalOpen: false, displayMode: 'inline' }))
  }, [])

  const reset = useCallback(() => {
    stopPolling()
    runningRef.current = false
    setState({
      isRunning: false,
      isModalOpen: false,
      displayMode: 'inline',
      clients: [],
      activeClientIndex: 0,
      allComplete: false,
      onComplete: null,
    })
  }, [stopPolling])

  return (
    <SimulationContext.Provider value={{ ...state, startSimulation, expandModal, collapseToInline, closeModal, reset }}>
      {children}
    </SimulationContext.Provider>
  )
}

export function useSimulation() {
  const ctx = useContext(SimulationContext)
  if (!ctx) throw new Error('useSimulation must be used within SimulationProvider')
  return ctx
}
