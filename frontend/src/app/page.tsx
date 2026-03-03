'use client'
import Link from 'next/link'
import { useRef, useState } from 'react'
import { motion, useInView, AnimatePresence } from 'framer-motion'
import { Plus_Jakarta_Sans, IBM_Plex_Mono } from 'next/font/google'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

const jakarta = Plus_Jakarta_Sans({ subsets: ['latin'], weight: ['400', '500', '600', '700', '800'] })
const mono = IBM_Plex_Mono({ weight: ['400', '500'], subsets: ['latin'] })

// ── Scroll reveal ─────────────────────────────────────────────────────────────

function Reveal({ children, delay = 0, className = '' }: {
  children: React.ReactNode; delay?: number; className?: string
}) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 18 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}>
      {children}
    </motion.div>
  )
}

function SectionTag({ children }: { children: React.ReactNode }) {
  return (
    <span className={`text-[10px] font-bold text-indigo-500 uppercase tracking-[0.18em] ${mono.className}`}>
      {children}
    </span>
  )
}

// ── Scenario data ─────────────────────────────────────────────────────────────

const SCENARIOS = [
  {
    id: 'structuring',
    label: 'Structuring Pattern',
    client: { name: 'Bob Kamara', profile: 'Self-employed consultant', income: '$56,000', age: '6 months', kyc: 'Standard' },
    description: 'Three e-transfers just below the $10,000 FINTRAC mandatory reporting threshold, spaced 2 days apart, from new counterparties.',
    layer1: {
      score: 0.87,
      archetype: 'structured_depositor',
      trend: 'Escalating: 0.34 to 0.87 over 14 days',
      indicators: [
        { name: 'Structuring', confidence: 0.90, detail: '$9,200 / $9,500 / $9,400 in 6 days from new counterparties' },
        { name: 'New Counterparty Burst', confidence: 0.72, detail: '3 previously unseen senders in 7-day window' },
        { name: 'Income Inconsistency', confidence: 0.61, detail: '$28,100 monthly inflow vs $4,667 expected' },
      ],
    },
    layer2: {
      level: 3,
      label: 'L3 — Restricted + Investigation',
      reasoning: 'Three deposits structured just below the $10,000 mandatory FINTRAC reporting threshold, spaced 2 days apart, originating exclusively from new unverified counterparties. The deposit sequence ($9,200, $9,500, $9,400) demonstrates deliberate threshold avoidance. Total inflow of $28,100 over 30 days represents 6x the expected monthly income. Restricting all e-transfer inflows from new counterparties and crypto operations while preserving essential payment access.',
      restricted: ['e_transfer_in_new', 'crypto_buy', 'crypto_send_external'],
      allowed: ['chequing_deposit', 'bill_payment', 'e_transfer_known', 'investment_hold'],
    },
    layer3: {
      classification: 'full_investigation', confidence: 89,
      fintrac: ['Indicator 9: Structured transactions below threshold', 'Indicator 14: Deposits inconsistent with stated income'],
      excerpt: 'Subject maintained a pattern of deposits structured below the mandatory $10,000 reporting threshold across a 6-day period. Three transactions totalling $28,100 arrived from previously uncontacted counterparties. The regularity of amounts, combined with new-counterparty origin and stated income inconsistency, is consistent with deliberate structuring under PCMLTFA s.9.',
    },
  },
  {
    id: 'crypto',
    label: 'Crypto Layering',
    client: { name: 'Carl Mendez', profile: 'Software developer', income: '$62,000', age: '18 months', kyc: 'Standard' },
    description: 'Large fiat deposit immediately converted to cryptocurrency and transmitted externally within 3 hours, across multiple product types.',
    layer1: {
      score: 0.91,
      archetype: 'crypto_launderer',
      trend: 'Spike: 0.21 to 0.91 in a single day',
      indicators: [
        { name: 'Rapid Crypto Conversion', confidence: 0.92, detail: '$18,000 deposit to $16,200 crypto send in 3 hours' },
        { name: 'Layering', confidence: 0.85, detail: 'Fiat to BTC to ETH across 3 product types in 4 hours' },
        { name: 'Income Inconsistency', confidence: 0.71, detail: 'Single deposit exceeds monthly expected income 3.5x' },
      ],
    },
    layer2: {
      level: 3,
      label: 'L3 — Restricted + Investigation',
      reasoning: 'Rapid conversion of a large fiat deposit into cryptocurrency followed by immediate external transmission. The velocity (deposit to external send in under 3 hours), combined with multi-hop conversion (fiat to BTC to ETH), is inconsistent with any legitimate investment pattern. The layering across multiple product types is a deliberate obscuring mechanism. Chequing access preserved; all crypto operations restricted immediately.',
      restricted: ['crypto_send_external', 'crypto_buy', 'crypto_sell', 'crypto_convert'],
      allowed: ['chequing_deposit', 'e_transfer_known', 'bill_payment', 'investment_hold'],
    },
    layer3: {
      classification: 'full_investigation', confidence: 92,
      fintrac: ['Indicator 28: Rapid crypto conversion', 'Indicator 31: Multi-product layering', 'Indicator 6: Transaction velocity inconsistency'],
      excerpt: 'Subject initiated a sequence of transactions consistent with the layering phase of money laundering. A $18,000 deposit was converted to Bitcoin within 45 minutes, cross-converted to Ethereum, and $16,200 subsequently transmitted to an external wallet. The multi-hop conversion path and 3-hour end-to-end velocity indicate deliberate obscuring of fund origin under PCMLTFA s.7.',
    },
  },
  {
    id: 'mule',
    label: 'Mule Account',
    client: { name: 'James Okafor', profile: 'Part-time retail worker', income: '$28,000', age: '3 months', kyc: 'Basic' },
    description: 'Eight new inbound senders over 7 days, funds aggregated and transmitted as a single outbound crypto transaction within 4 hours of the final deposit.',
    layer1: {
      score: 0.92,
      archetype: 'mule_like',
      trend: 'Escalating: 0.12 to 0.92 over 7 days',
      indicators: [
        { name: 'New Counterparty Burst', confidence: 0.85, detail: '8 new inbound senders, $400–$1,400 each, in 7-day window' },
        { name: 'Rapid Crypto Conversion', confidence: 0.92, detail: 'Aggregated $9,800 sent to single external wallet within 4h' },
        { name: 'Income Inconsistency', confidence: 0.78, detail: '$9,800 received over 7 days vs $538/week expected' },
      ],
    },
    layer2: {
      level: 3,
      label: 'L3 — Restricted + Investigation',
      reasoning: 'Eight unique inbound senders (all new counterparties with no prior history) transferring fragmented amounts that aggregate to $9,800, followed by a single outbound crypto send within 4 hours of the final deposit. This is a textbook mule pattern: receive fragmented funds from a sender network, rapidly consolidate, transmit externally before settlement holds can be applied. The 3-month account age with Basic KYC amplifies the risk signal. Restricting all outbound crypto and new-counterparty transfers immediately.',
      restricted: ['crypto_send_external', 'crypto_buy', 'e_transfer_out_new', 'wire_transfer'],
      allowed: ['chequing_deposit', 'bill_payment', 'e_transfer_known'],
    },
    layer3: {
      classification: 'full_investigation', confidence: 95,
      fintrac: ['Indicator 16: Third-party payments', 'Indicator 28: Rapid crypto consolidation', 'Indicator 4: Account as pass-through node', 'Indicator 22: Structuring across multiple senders'],
      excerpt: 'Subject\'s account received 8 distinct e-transfers from previously uncontacted parties over a 7-day window, totalling $9,800. Within 4 hours of the final deposit, the aggregated balance was transmitted to external cryptocurrency wallet 0x7a3f... This pattern (fragmented receipt from a sender network followed by rapid crypto consolidation) is consistent with the subject operating as a collection node in a coordinated mule network.',
    },
  },
]

// ── Architecture chart data ───────────────────────────────────────────────────

const HOURLY_DATA = [
  { time: '00:00', events: 12400, flagged: 18, autoResolved: 15, investigations: 3 },
  { time: '02:00', events: 9800, flagged: 12, autoResolved: 10, investigations: 2 },
  { time: '04:00', events: 8100, flagged: 9, autoResolved: 8, investigations: 1 },
  { time: '06:00', events: 14200, flagged: 21, autoResolved: 17, investigations: 4 },
  { time: '08:00', events: 38600, flagged: 58, autoResolved: 46, investigations: 12 },
  { time: '10:00', events: 51200, flagged: 76, autoResolved: 58, investigations: 18 },
  { time: '12:00', events: 54800, flagged: 82, autoResolved: 61, investigations: 21 },
  { time: '14:00', events: 49300, flagged: 74, autoResolved: 55, investigations: 19 },
  { time: '16:00', events: 47100, flagged: 71, autoResolved: 54, investigations: 17 },
  { time: '18:00', events: 38900, flagged: 58, autoResolved: 44, investigations: 14 },
  { time: '20:00', events: 29300, flagged: 44, autoResolved: 35, investigations: 9 },
  { time: '22:00', events: 19800, flagged: 30, autoResolved: 24, investigations: 6 },
]

// Deterministic account grid: 81 cells, risk levels 0–4
const GRID_RISKS = [
  0,0,0,0,0,0,1,0,0,
  0,0,1,0,0,0,0,0,0,
  0,3,0,0,0,1,0,0,0,
  0,0,0,0,2,0,0,0,1,
  0,0,0,4,0,0,0,0,0,
  1,0,0,0,0,0,2,0,0,
  0,0,0,0,1,0,0,0,0,
  0,3,0,0,0,0,0,2,0,
  0,0,0,1,0,0,0,0,3,
]

const RISK_DOT: Record<number, string> = {
  0: 'bg-emerald-400',
  1: 'bg-blue-400',
  2: 'bg-amber-400',
  3: 'bg-orange-500',
  4: 'bg-red-500',
}
const RISK_RING: Record<number, string> = {
  3: 'ring-2 ring-orange-400 ring-offset-1',
  4: 'ring-2 ring-red-400 ring-offset-1',
}

// ── Architecture diagram data ─────────────────────────────────────────────────

type ArchVariant = 'slate' | 'indigo' | 'amber' | 'violet'

const NODE_ROWS: Array<{
  id: string; label: string; variant: ArchVariant
  border: string; bg: string; labelColor: string; activeBorder: string; activeBg: string
  nodes: string[]
}> = [
  {
    id: 'ingestion', label: 'Data Ingestion', variant: 'slate',
    border: 'border-slate-200', bg: 'bg-slate-50', labelColor: 'text-slate-400',
    activeBorder: 'border-slate-400', activeBg: 'bg-slate-100',
    nodes: ['Transaction Events', 'Kafka Event Stream', 'Financial Activity Model'],
  },
  {
    id: 'behavioral', label: 'Behavioral Layer', variant: 'indigo',
    border: 'border-indigo-100', bg: 'bg-indigo-50/50', labelColor: 'text-indigo-400',
    activeBorder: 'border-indigo-400', activeBg: 'bg-indigo-50',
    nodes: ['ML Platform (Triton)', 'Behavioral Profile DB', 'LLM Gateway'],
  },
  {
    id: 'response', label: 'Response Layer', variant: 'amber',
    border: 'border-amber-100', bg: 'bg-amber-50/50', labelColor: 'text-amber-500',
    activeBorder: 'border-amber-400', activeBg: 'bg-amber-50',
    nodes: ['Graduated Response Engine', 'Restriction Enforcement', 'Client Notification'],
  },
  {
    id: 'investigation', label: 'Investigation Layer', variant: 'violet',
    border: 'border-violet-100', bg: 'bg-violet-50/50', labelColor: 'text-violet-500',
    activeBorder: 'border-violet-400', activeBg: 'bg-violet-50',
    nodes: ['Investigation Orchestrator', 'Book of Record', 'Human Review Queue'],
  },
]

const ARROW_COLORS: Record<ArchVariant, { line: string; dot: string; stroke: string }> = {
  slate:  { line: 'bg-slate-200',  dot: 'bg-slate-400',  stroke: '#94a3b8' },
  indigo: { line: 'bg-indigo-200', dot: 'bg-indigo-400', stroke: '#818cf8' },
  amber:  { line: 'bg-amber-200',  dot: 'bg-amber-400',  stroke: '#fbbf24' },
  violet: { line: 'bg-violet-200', dot: 'bg-violet-400', stroke: '#a78bfa' },
}

const NODE_DETAILS: Record<string, { layer: string; desc: string; stat: string }> = {
  'Transaction Events': {
    layer: 'Data Ingestion',
    desc: 'Every client action across chequing, crypto, e-transfers, TFSA, and Visa flows as a discrete event. Each event carries product type, amount, counterparty identifier, timestamp, and geographic metadata. This is the raw input to the behavioral scoring pipeline.',
    stat: '3M+ accounts monitored',
  },
  'Kafka Event Stream': {
    layer: 'Data Ingestion',
    desc: 'Real-time event streaming infrastructure. All services publish data to the general ledger through real-time streams. The behavioral scoring pipeline subscribes to this feed and processes events with sub-second delivery guarantees. No polling, no batch delays.',
    stat: 'Sub-second delivery',
  },
  'Financial Activity Model': {
    layer: 'Data Ingestion',
    desc: 'A unified representation of all financial activities across every product line. FAM normalizes chequing, crypto, investing, and transfers into a single event schema, enabling the behavioral layer to reason across product boundaries without custom integration per product.',
    stat: 'Cross-product unified schema',
  },
  'ML Platform (Triton)': {
    layer: 'Behavioral Layer',
    desc: 'NVIDIA Triton inference server running behavioral scoring models at production scale. Handles archetype classification, deviation scoring, and risk trajectory computation. The same infrastructure serves all real-time ML inference across the platform.',
    stat: '145M+ predictions/year, 99.999% uptime',
  },
  'Behavioral Profile DB': {
    layer: 'Behavioral Layer',
    desc: 'PostgreSQL with JSONB columns storing 12-dimensional risk vectors, archetype trajectories, temporal indicator history, and per-product risk decomposition for every client. The behavioral scoring delta executes as a PostgreSQL trigger at transaction ingest time, not in Python, achieving sub-5ms profile updates.',
    stat: 'Sub-5ms updates via DB trigger',
  },
  'LLM Gateway': {
    layer: 'Behavioral Layer',
    desc: 'PII-redaction layer before any LLM call. Strips names, account numbers, and other identifiers from inputs; rehydrates outputs. Provides multi-model support and audit logging. Client data never reaches an external LLM without PII stripping. Critical for FINTRAC compliance and data residency.',
    stat: 'PII-stripped before every call',
  },
  'Graduated Response Engine': {
    layer: 'Response Layer',
    desc: 'The LLM receives the behavioral profile, product holdings, detected indicators, and PCMLTFA regulatory context via the LLM Gateway. It returns a typed JSON object specifying which capabilities to restrict, which to preserve, the client-facing message, and the legal reasoning. This output is the permanent compliance audit record.',
    stat: 'Structured JSON output in ~2s',
  },
  'Restriction Enforcement': {
    layer: 'Response Layer',
    desc: 'Applies the minimum restriction set derived from the LLM decision. Restrictions are product-scoped: a crypto layering trigger disables crypto operations, not chequing. Every restriction change is persisted with the full decision context, creating a tamper-evident record ready for OSFI examination.',
    stat: 'Product-scoped, not account-wide',
  },
  'Client Notification': {
    layer: 'Response Layer',
    desc: 'LLM-drafted notification reviewed against a compliance-approved template library. Specific and informative ("crypto withdrawals temporarily paused while we verify recent activity") rather than generic ("account frozen for security reasons"). Delivered via in-app notification and email.',
    stat: 'Compliance-template reviewed',
  },
  'Investigation Orchestrator': {
    layer: 'Investigation Layer',
    desc: 'LangGraph 8-node directed acyclic graph dispatched to distributed workers for Level 3+ cases. Eight specialized agents run concurrently: baseline enrichment, FINTRAC indicator tagging, money flow reconstruction, cross-client correlation, sanctions screening, case classification, and STR narrative generation. The graph is deterministic and re-entrant.',
    stat: 'Under 4 min end-to-end',
  },
  'Book of Record': {
    layer: 'Investigation Layer',
    desc: 'Every AI decision persisted with its full input context, reasoning chain, and output. Tamper-evident audit storage ready for OSFI examination. Investigation outcomes, restriction changes, and STR filing decisions are all recorded here with complete evidence chains.',
    stat: 'Full evidence chain per decision',
  },
  'Human Review Queue': {
    layer: 'Investigation Layer',
    desc: 'The analyst receives a complete investigation package: behavioral deviation analysis, money flow visualization, cross-client correlation data, FINTRAC indicator tags, and a draft STR narrative. One decision: file or dismiss. Under PCMLTFA, this decision carries personal criminal liability. The system is designed so this is the only judgment the analyst needs to make.',
    stat: '100% judgment, 0% data assembly',
  },
}

// ── Restriction level distribution ───────────────────────────────────────────

const RESTRICTION_LEVELS = [
  { label: 'L0 Baseline', pct: 96.8, color: 'bg-emerald-400', note: 'Passive monitoring' },
  { label: 'L1 Monitor',  pct: 2.4,  color: 'bg-blue-400',    note: 'Enhanced telemetry, client sees nothing' },
  { label: 'L2 Guardrail',pct: 0.5,  color: 'bg-amber-400',   note: 'Step-up auth for specific actions' },
  { label: 'L3 Restrict', pct: 0.2,  color: 'bg-orange-500',  note: 'Specific capabilities blocked' },
  { label: 'L4 Frozen',   pct: 0.1,  color: 'bg-red-500',     note: 'Target: under 0.05%' },
]

// ── Layer data ────────────────────────────────────────────────────────────────

const LAYERS = [
  {
    num: '01', tag: 'Layer 1', accent: 'border-t-indigo-500',
    title: 'Continuous Risk Surface',
    summary: 'A living behavioral model updated on every transaction.',
    bullets: [
      'Maintains a 12-dimensional behavioral profile per client, updated on every transaction',
      'Classifies clients into behavioral archetypes (payroll depositor, active trader, crypto-heavy) with archetype-specific baselines',
      'Builds a counterparty network graph enriched with each new transaction',
      'Scores risk per-product: crypto withdrawals scored independently from bill payments',
      'Detects deviations relative to each client\'s own history, not static thresholds',
    ],
    tech: 'Kafka event streams · ML Platform · PostgreSQL JSONB · 12 behavioral dimensions · sub-5ms updates',
  },
  {
    num: '02', tag: 'Layer 2', accent: 'border-t-amber-400',
    title: 'Graduated Response Engine',
    summary: 'Five restriction levels. The minimum necessary intervention.',
    bullets: [
      'L0 Baseline (97% of accounts): passive monitoring only',
      'L1 Monitor: enhanced telemetry, client sees nothing',
      'L2 Guardrail: step-up auth for specific high-risk actions',
      'L3 Restrict: specific capabilities blocked based on trigger type',
      'L4 Freeze: reserved for confirmed account takeover or sanctions match',
      'Levels re-evaluate continuously; L3 can de-escalate to L1 in minutes',
    ],
    tech: 'LLM reasoning engine · Structured JSON output · Real-time re-evaluation · PCMLTFA-grounded',
  },
  {
    num: '03', tag: 'Layer 3', accent: 'border-t-violet-500',
    title: 'Investigation Orchestrator',
    summary: '8-node parallel pipeline. Not a cold start.',
    bullets: [
      'Starts from deep behavioral context (Layer 1), not a cold start',
      '8 specialized AI agents run concurrently: baseline enrichment, FINTRAC tagging, money flow, cross-client correlation, sanctions screening, classification, STR drafting',
      'Cross-client correlation queries the entire client base for coordinated patterns',
      'Produces one evidence package covering the full correlated network',
      'End-to-end in under 4 minutes',
    ],
    tech: 'LangGraph DAG · LangChain · Parallel execution · Cross-client correlation · under 4 min',
  },
  {
    num: '04', tag: 'Layer 4', accent: 'border-t-slate-400',
    title: 'Human Boundary',
    summary: 'One judgment call. The system handles everything else.',
    bullets: [
      'Filing an STR under PCMLTFA is a legal act signed personally by the compliance officer',
      'FINTRAC\'s "reasonable grounds to suspect" standard is deliberately subjective',
      'CSA Staff Notice 11-348 requires human-in-the-loop for AI in Canadian capital markets',
      'Analyst receives a complete investigation package and makes one decision: file or dismiss',
      'Time shifts from 80% evidence assembly to 100% judgment',
    ],
    tech: 'PCMLTFA s.7 · FINTRAC STR · CSA Staff Notice 11-348 · Full audit trail · Human sign-off',
  },
]

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  const pct = Math.round(score * 100)
  const color = score >= 0.85 ? 'bg-red-500' : score >= 0.75 ? 'bg-orange-500' : score >= 0.60 ? 'bg-amber-400' : 'bg-blue-400'
  return (
    <div ref={ref} className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={inView ? { width: `${pct}%` } : {}}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
      <span className={`text-sm font-bold tabular-nums ${score >= 0.75 ? 'text-orange-600' : 'text-slate-700'} ${mono.className}`}>
        {score.toFixed(2)}
      </span>
    </div>
  )
}

// ── Scenario viewer ───────────────────────────────────────────────────────────

function ScenarioViewer() {
  const [active, setActive] = useState(0)
  const s = SCENARIOS[active]

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {SCENARIOS.map((sc, i) => (
          <button
            key={sc.id}
            onClick={() => setActive(i)}
            className={`text-sm font-medium px-4 py-2 rounded-lg border transition-colors ${
              i === active
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-slate-500 border-slate-200 hover:border-slate-400 hover:text-slate-800'
            }`}
          >
            {sc.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
          className="space-y-4"
        >
          {/* Client card */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 flex flex-wrap gap-6 items-start">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-0.5">Client</p>
              <p className="text-base font-bold text-slate-900">{s.client.name}</p>
              <p className="text-sm text-slate-500">{s.client.profile}</p>
            </div>
            {[
              { label: 'Stated Income', val: s.client.income },
              { label: 'Account Age', val: s.client.age },
              { label: 'KYC Level', val: s.client.kyc },
            ].map(({ label, val }) => (
              <div key={label}>
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-0.5">{label}</p>
                <p className="text-sm font-semibold text-slate-700">{val}</p>
              </div>
            ))}
            <div className="flex-1 min-w-[200px]">
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-0.5">Trigger</p>
              <p className="text-sm text-slate-600 leading-relaxed">{s.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Layer 1 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs font-bold text-white bg-indigo-500 px-2 py-0.5 rounded">Layer 1</span>
                <span className="text-xs font-semibold text-slate-600">Behavioral Intelligence</span>
              </div>

              <div className="mb-4">
                <p className="text-xs text-slate-400 font-medium mb-1.5">Overall Risk Score</p>
                <ScoreBar score={s.layer1.score} />
              </div>

              <div className="mb-4 space-y-2.5">
                <p className="text-xs text-slate-400 font-medium">Detected Indicators</p>
                {s.layer1.indicators.map((ind, i) => (
                  <div key={i}>
                    <div className="flex items-baseline justify-between mb-0.5">
                      <span className="text-xs font-semibold text-slate-700">{ind.name}</span>
                      <span className={`text-xs font-bold ${mono.className} ${ind.confidence >= 0.85 ? 'text-red-500' : 'text-orange-500'}`}>
                        {(ind.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-1">
                      <motion.div
                        className={`h-full rounded-full ${ind.confidence >= 0.85 ? 'bg-red-400' : ind.confidence >= 0.70 ? 'bg-orange-400' : 'bg-amber-400'}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${ind.confidence * 100}%` }}
                        transition={{ duration: 0.6, delay: i * 0.1 + 0.3 }}
                      />
                    </div>
                    <p className={`text-[10px] text-slate-400 ${mono.className}`}>{ind.detail}</p>
                  </div>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-400 font-medium mb-0.5">Archetype</p>
                <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                  {s.layer1.archetype}
                </span>
                <p className={`text-[10px] text-slate-400 mt-1 ${mono.className}`}>{s.layer1.trend}</p>
              </div>
            </div>

            {/* Layer 2 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs font-bold text-white bg-amber-500 px-2 py-0.5 rounded">Layer 2</span>
                <span className="text-xs font-semibold text-slate-600">Graduated Response</span>
              </div>

              <div className="mb-4">
                <span className="text-xs font-bold px-2 py-1 rounded-md bg-orange-100 text-orange-700 border border-orange-200">
                  {s.layer2.label}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-xs text-slate-400 font-medium mb-2">LLM Reasoning</p>
                <p className={`text-[11px] text-slate-600 leading-relaxed border-l-2 border-indigo-300 pl-3 italic ${mono.className}`}>
                  &ldquo;{s.layer2.reasoning}&rdquo;
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                <div>
                  <p className="text-xs text-red-600 font-semibold mb-1.5">Restricted</p>
                  <ul className="space-y-1">
                    {s.layer2.restricted.map((cap, i) => (
                      <li key={i} className={`text-[10px] text-slate-500 ${mono.className}`}>x {cap}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs text-emerald-600 font-semibold mb-1.5">Allowed</p>
                  <ul className="space-y-1">
                    {s.layer2.allowed.map((cap, i) => (
                      <li key={i} className={`text-[10px] text-slate-500 ${mono.className}`}>v {cap}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Layer 3 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs font-bold text-white bg-orange-500 px-2 py-0.5 rounded">Layer 3</span>
                <span className="text-xs font-semibold text-slate-600">Investigation</span>
              </div>

              <div className="flex items-center gap-3 mb-4">
                <div>
                  <p className="text-xs text-slate-400 font-medium mb-0.5">Classification</p>
                  <p className="text-sm font-bold text-slate-900 capitalize">
                    {s.layer3.classification.replace(/_/g, ' ')}
                  </p>
                </div>
                <div className="ml-auto text-right">
                  <p className="text-xs text-slate-400 font-medium mb-0.5">Confidence</p>
                  <p className={`text-xl font-extrabold text-indigo-600 ${mono.className}`}>
                    {s.layer3.confidence}%
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <p className="text-xs text-slate-400 font-medium mb-1.5">FINTRAC Indicators</p>
                <ul className="space-y-1">
                  {s.layer3.fintrac.map((f, i) => (
                    <li key={i} className={`text-[10px] text-slate-500 leading-relaxed ${mono.className}`}>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-400 font-medium mb-2">STR Draft Excerpt</p>
                <p className={`text-[10px] text-slate-500 leading-relaxed bg-slate-50 rounded p-2.5 border border-slate-100 ${mono.className}`}>
                  &ldquo;{s.layer3.excerpt}&rdquo;
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

// ── Account dot grid ──────────────────────────────────────────────────────────

function AccountGrid() {
  return (
    <div>
      <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(9, 1fr)' }}>
        {GRID_RISKS.map((risk, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2, delay: i * 0.008 }}
            className={`relative w-4 h-4 rounded-full ${RISK_DOT[risk]} ${RISK_RING[risk] ?? ''}`}
          >
            {(risk === 3 || risk === 4) && (
              <motion.div
                className={`absolute inset-0 rounded-full ${risk === 4 ? 'bg-red-400' : 'bg-orange-400'}`}
                animate={{ opacity: [0.4, 0, 0.4], scale: [1, 1.8, 1] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut', delay: i * 0.1 }}
              />
            )}
          </motion.div>
        ))}
      </div>
      <div className="flex gap-4 mt-4 flex-wrap">
        {[
          { color: 'bg-emerald-400', label: 'L0 Clear' },
          { color: 'bg-blue-400', label: 'L1 Monitor' },
          { color: 'bg-amber-400', label: 'L2 Guardrail' },
          { color: 'bg-orange-500', label: 'L3 Restricted' },
          { color: 'bg-red-500', label: 'L4 Frozen' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full ${color}`} />
            <span className={`text-[10px] text-slate-400 ${mono.className}`}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Flow arrow (animated travelling dot) ──────────────────────────────────────

function FlowArrow({ variant }: { variant: ArchVariant }) {
  const c = ARROW_COLORS[variant]
  return (
    <div className="flex items-center gap-0.5 shrink-0 w-10 mx-1">
      <div className={`relative flex-1 h-px ${c.line} overflow-hidden`}>
        <motion.div
          className={`absolute top-0 h-full w-6 ${c.dot} opacity-60`}
          style={{ filter: 'blur(1px)' }}
          animate={{ x: ['-24px', '44px'] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
        />
      </div>
      <svg className="w-2.5 h-2.5 shrink-0" viewBox="0 0 10 10" fill="none">
        <path d="M2 2l5 3-5 3" stroke={c.stroke} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

// ── Architecture diagram ──────────────────────────────────────────────────────

function ArchitectureDiagram() {
  const [activeNode, setActiveNode] = useState<string | null>(null)
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  const layerColors: Record<string, { label: string; left: string; nodeBorder: string; nodeHover: string; activeBg: string; activeBorder: string; arrow: string }> = {
    ingestion:    { label: 'text-slate-400',  left: 'border-l-slate-300',  nodeBorder: 'border-slate-150', nodeHover: 'hover:border-slate-300', activeBg: 'bg-slate-50', activeBorder: 'border-slate-400', arrow: 'text-slate-300' },
    behavioral:   { label: 'text-indigo-500', left: 'border-l-indigo-400', nodeBorder: 'border-indigo-100', nodeHover: 'hover:border-indigo-300', activeBg: 'bg-indigo-50', activeBorder: 'border-indigo-400', arrow: 'text-indigo-300' },
    response:     { label: 'text-amber-500',  left: 'border-l-amber-400',  nodeBorder: 'border-amber-100', nodeHover: 'hover:border-amber-300', activeBg: 'bg-amber-50', activeBorder: 'border-amber-400', arrow: 'text-amber-300' },
    investigation:{ label: 'text-violet-500', left: 'border-l-violet-400', nodeBorder: 'border-violet-100', nodeHover: 'hover:border-violet-300', activeBg: 'bg-violet-50', activeBorder: 'border-violet-400', arrow: 'text-violet-300' },
  }

  return (
    <div ref={ref} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      {NODE_ROWS.map((row, rowIdx) => {
        const c = layerColors[row.id]
        return (
          <div key={row.id}>
            {/* Connector line between layers */}
            {rowIdx > 0 && (
              <div className="flex justify-center">
                <div className="flex flex-col items-center py-0">
                  <div className={`w-px h-3 ${c.arrow.replace('text-', 'bg-')}`} />
                  <svg className={`w-3 h-2 ${c.arrow}`} viewBox="0 0 12 8" fill="currentColor">
                    <path d="M6 8L1 2h10L6 8z" />
                  </svg>
                </div>
              </div>
            )}

            {/* Layer */}
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={inView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.35, delay: rowIdx * 0.1 }}
              className={`flex items-stretch border-l-[3px] ${c.left} mx-3 ${rowIdx === 0 ? 'mt-3' : ''} ${rowIdx === NODE_ROWS.length - 1 ? 'mb-3' : ''}`}
            >
              {/* Layer label */}
              <div className="w-24 sm:w-28 shrink-0 flex items-center pl-3">
                <span className={`text-[9px] font-bold uppercase tracking-widest ${c.label} ${mono.className}`}>
                  {row.label}
                </span>
              </div>

              {/* Nodes in row */}
              <div className="flex-1 flex items-center gap-1 py-2 pr-3">
                {row.nodes.map((nodeId, nodeIdx) => (
                  <div key={nodeId} className="flex items-center flex-1 min-w-0">
                    {nodeIdx > 0 && (
                      <svg className={`w-4 h-3 shrink-0 mx-0.5 ${c.arrow}`} viewBox="0 0 16 12" fill="none">
                        <path d="M0 6h12M9 3l3 3-3 3" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                    <motion.button
                      initial={{ opacity: 0 }}
                      animate={inView ? { opacity: 1 } : {}}
                      transition={{ duration: 0.25, delay: rowIdx * 0.08 + nodeIdx * 0.05 }}
                      onClick={() => setActiveNode(activeNode === nodeId ? null : nodeId)}
                      className={`flex-1 min-w-0 text-left px-2.5 py-2 rounded-md border transition-all cursor-pointer ${
                        activeNode === nodeId
                          ? `${c.activeBorder} ${c.activeBg} shadow-sm`
                          : `${c.nodeBorder} bg-white ${c.nodeHover} hover:shadow-sm`
                      }`}
                    >
                      <p className={`text-[10px] font-semibold text-slate-700 leading-tight truncate ${mono.className}`}>
                        {nodeId}
                      </p>
                      <p className="text-[9px] text-slate-400 mt-0.5 leading-tight truncate">
                        {NODE_DETAILS[nodeId]?.stat}
                      </p>
                    </motion.button>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )
      })}

      {/* Detail panel */}
      <AnimatePresence>
        {activeNode !== null && NODE_DETAILS[activeNode] && (
          <motion.div
            key={activeNode}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t border-slate-200 px-5 py-4 bg-slate-50">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <p className={`text-[10px] font-bold text-indigo-400 uppercase tracking-wide ${mono.className}`}>
                      {NODE_DETAILS[activeNode].layer}
                    </p>
                    <span className={`text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100 ${mono.className}`}>
                      {NODE_DETAILS[activeNode].stat}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900 mb-1">{activeNode}</p>
                  <p className="text-xs text-slate-500 leading-relaxed">{NODE_DETAILS[activeNode].desc}</p>
                </div>
                <button
                  onClick={() => setActiveNode(null)}
                  className="shrink-0 w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-slate-400 hover:bg-slate-300 hover:text-slate-600 transition-colors"
                >
                  <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path d="M2 2l8 8M10 2l-8 8" />
                  </svg>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Restriction level bars ────────────────────────────────────────────────────

function RestrictionLevelBars() {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })

  return (
    <div ref={ref} className="space-y-3.5">
      {RESTRICTION_LEVELS.map((level, i) => (
        <div key={level.label}>
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-baseline gap-2">
              <span className={`text-xs font-bold text-slate-700 ${mono.className}`}>{level.label}</span>
              <span className="text-[10px] text-slate-400">{level.note}</span>
            </div>
            <span className={`text-xs font-bold tabular-nums text-slate-500 ${mono.className}`}>
              {level.pct}%
            </span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${level.color}`}
              initial={{ width: 0 }}
              animate={inView ? { width: `${level.pct}%` } : {}}
              transition={{ duration: 0.7, delay: i * 0.1 + 0.1, ease: 'easeOut' }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function StartPage() {
  const heroRef = useRef(null)
  const heroInView = useInView(heroRef, { once: true })

  return (
    <div className={`${jakarta.className} -mx-4 sm:-mx-6 lg:-mx-8 -mt-8 overflow-x-hidden bg-white`}>

      {/* ── NAV ─────────────────────────────────────────────────────────── */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="sticky top-0 z-40 bg-white/90 backdrop-blur-sm border-b border-slate-200"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-8 h-14 flex items-center">
          <span className="text-slate-900 font-bold text-xl tracking-tight">SimpleResolve</span>
        </div>
      </motion.header>

      {/* ── SECTION 1: OPENING ──────────────────────────────────────────── */}
      <section ref={heroRef} className="max-w-6xl mx-auto px-4 sm:px-8 pt-20 pb-16">
        <motion.div initial={{ opacity: 0 }} animate={heroInView ? { opacity: 1 } : {}} transition={{ duration: 0.4 }}>
          <SectionTag>AML Compliance · PCMLTFA · FINTRAC · Canadian Fintech</SectionTag>
        </motion.div>
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={heroInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.08 }}
          className="text-4xl sm:text-5xl font-extrabold text-slate-900 mt-4 mb-5 leading-[1.08] tracking-tight max-w-3xl"
        >
          Stop freezing your customers.{' '}
          <br className="hidden sm:block" />
          Start resolving risk.
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={heroInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.16 }}
          className="max-w-3xl text-slate-500 text-base leading-relaxed mb-10"
        >
          <p>
            Legacy AML locks every flagged account and waits for manual review. SimpleResolve uses behavioral AI
            to catch real threats, unfreeze legitimate customers in minutes, and stay{' '}
            <span className="text-slate-700 font-medium">FINTRAC-compliant</span> — automatically.
          </p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={heroInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.45, delay: 0.26 }}
        >
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-indigo-600 text-white font-semibold text-sm px-5 py-2.5 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Open Dashboard
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </motion.div>
      </section>

      {/* ── SECTION 2: LEGACY AML ────────────────────────────────────────── */}
      <section className="border-y border-slate-200 bg-slate-50 py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-8">
          <Reveal>
            <SectionTag>How This Redefines Legacy AML</SectionTag>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 mb-3 tracking-tight">
              Legacy AML is a blunt instrument.
            </h2>
            <p className="text-slate-500 max-w-2xl mb-12 leading-relaxed">
              The industry standard is a rules engine that triggers on thresholds and freezes everything. SimpleResolve
              replaces each step in that workflow with an AI-native equivalent.
            </p>
          </Reveal>

          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 pr-6 text-xs font-semibold text-slate-400 uppercase tracking-wide w-40">Workflow Step</th>
                  <th className="text-left py-3 pr-6 text-xs font-semibold text-red-500 uppercase tracking-wide">Legacy Approach</th>
                  <th className="text-left py-3 text-xs font-semibold text-indigo-500 uppercase tracking-wide">SimpleResolve</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[
                  {
                    step: 'Risk Detection',
                    legacy: 'Static threshold rules. Same rules for all clients, all products, all contexts.',
                    modern: 'Continuous behavioral profiling. Each client has a dynamic baseline. Deviations score against their own history.',
                  },
                  {
                    step: 'Account Action',
                    legacy: 'Binary: full freeze or nothing. All 7+ products suspended regardless of which triggered the alert.',
                    modern: 'Graduated response: LLM reasons which specific capabilities to restrict. Average: 1.8 products affected.',
                  },
                  {
                    step: 'Investigation',
                    legacy: 'Manual analyst work: pulling transaction history, cross-referencing spreadsheets, writing narrative from scratch.',
                    modern: '8-node LangGraph pipeline runs autonomously: FINTRAC tagging, money flow, network correlation, STR drafting.',
                  },
                  {
                    step: 'Cross-Client Correlation',
                    legacy: 'Only possible with weeks of manual work across siloed case files.',
                    modern: 'Real-time wallet cluster and counterparty correlation across all monitored accounts simultaneously.',
                  },
                  {
                    step: 'STR Preparation',
                    legacy: 'Analyst writes the narrative manually, maps indicators by hand, submits via FINTRAC portal.',
                    modern: 'AI drafts a PCMLTFA-compliant narrative with FINTRAC indicator codes pre-mapped. Analyst reviews, signs, files.',
                  },
                  {
                    step: 'Human Role',
                    legacy: 'Analyst handles every step: detection, investigation, writing, decision, submission.',
                    modern: 'Analyst makes one decision: file or dismiss. Everything else is handled by the pipeline.',
                  },
                ].map(({ step, legacy, modern }) => (
                  <tr key={step} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-3.5 pr-6 text-xs font-semibold text-slate-500 align-top">{step}</td>
                    <td className="py-3.5 pr-6 text-slate-500 leading-relaxed align-top">{legacy}</td>
                    <td className="py-3.5 text-slate-700 leading-relaxed align-top font-medium">{modern}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── SECTION 3: FOUR LAYERS ───────────────────────────────────────── */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-8">
          <Reveal>
            <SectionTag>Architecture</SectionTag>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 mb-2 tracking-tight">Four layers. One pipeline.</h2>
            <p className="text-slate-500 mb-12 max-w-2xl leading-relaxed">
              Each layer has a distinct responsibility. Removing any layer degrades a specific capability.
            </p>
          </Reveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {LAYERS.map((layer, i) => (
              <Reveal key={layer.num} delay={i * 0.06}>
                <div className={`bg-white border border-slate-200 border-t-2 ${layer.accent} rounded-xl p-6 h-full flex flex-col`}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold text-white bg-slate-600 px-2 py-0.5 rounded ${mono.className}`}>
                        {layer.tag}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">{layer.summary}</span>
                    </div>
                    <span className="text-3xl font-black text-slate-100">{layer.num}</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-3">{layer.title}</h3>
                  <ul className="space-y-1.5 flex-1">
                    {layer.bullets.map((bullet, j) => (
                      <li key={j} className="flex items-start gap-2 text-sm text-slate-500 leading-snug">
                        <span className="w-1 h-1 rounded-full bg-slate-300 shrink-0 mt-2" />
                        {bullet}
                      </li>
                    ))}
                  </ul>
                  <div className={`mt-4 pt-3.5 border-t border-slate-100 text-[10px] text-slate-400 ${mono.className}`}>
                    {layer.tech}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECTION 4: WORKFLOW WITH EXAMPLES ───────────────────────────── */}
      <section className="border-y border-slate-200 bg-slate-50 py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-8">
          <Reveal>
            <SectionTag>Workflow with Examples</SectionTag>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 mb-2 tracking-tight">
              See the pipeline output.
            </h2>
            <p className="text-slate-500 mb-10 max-w-2xl leading-relaxed">
              Select a scenario to see what each layer produces: raw behavioral scoring, LLM restriction
              reasoning, and the final STR draft excerpt.
            </p>
          </Reveal>
          <ScenarioViewer />
        </div>
      </section>

      {/* ── SECTION 5: SYSTEM ARCHITECTURE ──────────────────────────────── */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-8">
          <Reveal>
            <SectionTag>System Architecture</SectionTag>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 mb-2 tracking-tight">
              Every component is load-bearing.
            </h2>
            <p className="text-slate-500 mb-10 max-w-2xl leading-relaxed">
              Remove any layer and a specific capability disappears. This is not a rules engine with an AI
              wrapper. The AI is the decision substrate. Click any node to see its role in the pipeline.
            </p>
          </Reveal>
          <Reveal delay={0.05}>
            <ArchitectureDiagram />
          </Reveal>
        </div>
      </section>

      {/* ── SECTION 6: ARCHITECTURE AT SCALE ────────────────────────────── */}
      <section className="border-y border-slate-200 bg-slate-50 py-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-8">
          <Reveal>
            <SectionTag>At Scale</SectionTag>
            <h2 className="text-3xl font-extrabold text-slate-900 mt-3 mb-2 tracking-tight">
              How this works at production scale.
            </h2>
            <p className="text-slate-500 mb-12 max-w-2xl leading-relaxed">
              Behavioral profiles pre-computed at ingest. Investigations run on distributed workers.
              The human analyst is never in the critical path.
            </p>
          </Reveal>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
            {/* Transaction event volume chart */}
            <Reveal delay={0.05}>
              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <p className="text-sm font-semibold text-slate-800 mb-1">Transaction Event Volume</p>
                <p className={`text-[10px] text-slate-400 mb-1 ${mono.className}`}>Simulated 24h at production scale: events processed / flagged / auto-resolved</p>
                <p className={`text-[10px] text-emerald-600 font-semibold mb-4 ${mono.className}`}>
                  ~97% of flagged events auto-resolve at L0–L1 without human involvement
                </p>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={HOURLY_DATA} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <defs>
                      <linearGradient id="gradEvents" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.12} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gradFlagged" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gradResolved" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#34d399" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: 'none' }}
                      labelStyle={{ fontWeight: 600, color: '#1e293b' }}
                    />
                    <Area type="monotone" dataKey="events" name="Transactions" stroke="#6366f1" strokeWidth={1.5} fill="url(#gradEvents)" dot={false} />
                    <Area type="monotone" dataKey="flagged" name="Flagged" stroke="#f97316" strokeWidth={1.5} fill="url(#gradFlagged)" dot={false} />
                    <Area type="monotone" dataKey="autoResolved" name="Auto-resolved" stroke="#34d399" strokeWidth={1.5} fill="url(#gradResolved)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Reveal>

            {/* Restriction level distribution */}
            <Reveal delay={0.1}>
              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <p className="text-sm font-semibold text-slate-800 mb-1">Account Restriction Level Distribution</p>
                <p className={`text-[10px] text-slate-400 mb-1 ${mono.className}`}>
                  Production target — down from ~100% at L4 in a binary freeze model
                </p>
                <p className={`text-[10px] text-indigo-500 font-semibold mb-5 ${mono.className}`}>
                  Target: under 0.05% of accounts at L4 (full freeze)
                </p>
                <RestrictionLevelBars />
              </div>
            </Reveal>
          </div>

          {/* Account monitoring grid + processing steps */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Reveal delay={0.08}>
              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <p className="text-sm font-semibold text-slate-800 mb-1">Live Account Risk Register</p>
                <p className={`text-[10px] text-slate-400 mb-5 ${mono.className}`}>
                  Simulated view: each cell is one monitored account. High-risk accounts pulse in real time.
                </p>
                <AccountGrid />
              </div>
            </Reveal>

            <Reveal delay={0.12}>
              <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-6">
                <div>
                  <p className="text-sm font-semibold text-slate-800 mb-4">Processing Pipeline</p>
                  <div className="space-y-3.5">
                    {[
                      { label: 'Transaction ingest', detail: 'Event triggers behavioral delta via database trigger. Profile updated in real time.', timing: '<5ms', layer: 'L1' },
                      { label: 'Risk threshold evaluation', detail: 'If deviation crosses threshold, Layer 2 LLM call is enqueued immediately.', timing: '<50ms', layer: 'L2' },
                      { label: 'Scope reasoning', detail: 'LLM returns restriction JSON. Restriction applied, client notified with specific message.', timing: '~2s', layer: 'L2' },
                      { label: 'Investigation dispatch', detail: 'If level 3 or above, LangGraph 8-node pipeline is dispatched to distributed workers.', timing: '~4 min', layer: 'L3' },
                      { label: 'Human review', detail: 'STR draft delivered to analyst queue with full evidence package. Analyst decides: file or dismiss.', timing: 'analyst decision', layer: 'L4' },
                    ].map((step, i) => (
                      <div key={i} className="flex gap-3 items-start">
                        <span className={`text-[10px] font-bold text-white px-1.5 py-0.5 rounded shrink-0 mt-0.5 ${
                          step.layer === 'L1' ? 'bg-indigo-500' : step.layer === 'L2' ? 'bg-amber-500' : step.layer === 'L3' ? 'bg-orange-500' : 'bg-slate-500'
                        } ${mono.className}`}>
                          {step.layer}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline justify-between gap-2">
                            <p className="text-xs font-semibold text-slate-800">{step.label}</p>
                            <span className={`text-[10px] text-slate-400 shrink-0 ${mono.className}`}>{step.timing}</span>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">{step.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100">
                  <p className={`text-[10px] text-slate-400 leading-relaxed ${mono.className}`}>
                    Each layer runs independently. A slow Layer 3 investigation does not block Layer 2
                    from processing new events. The human analyst is never in the critical path.
                  </p>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer className="px-4 sm:px-8 py-10 border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <span className="text-slate-900 font-bold text-lg">SimpleResolve</span>
            <p className={`text-xs text-slate-400 mt-0.5 ${mono.className}`}>
              Prototype system. Not for production use. All client data is synthetic.
            </p>
          </div>
          <div className="flex gap-6">
            {[['Dashboard', '/dashboard'], ['Clients', '/clients'], ['Investigations', '/investigations']].map(([label, href]) => (
              <Link key={href} href={href} className="text-xs text-slate-400 hover:text-slate-700 transition-colors">
                {label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
