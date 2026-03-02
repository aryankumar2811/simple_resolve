import Link from 'next/link'
import { DM_Serif_Display, IBM_Plex_Mono } from 'next/font/google'

const display = DM_Serif_Display({ weight: '400', subsets: ['latin'] })
const mono = IBM_Plex_Mono({ weight: ['400', '500', '700'], subsets: ['latin'] })

const layers = [
  {
    number: '01',
    title: 'Behavioral Intelligence',
    subtitle: 'Continuous profiling',
    description:
      "Maintains a living risk profile for every client. Pre-computes behavioral baselines, archetypes, and per-product risk scores — so investigation doesn't start from scratch.",
    tech: 'Python · SQLAlchemy · PostgreSQL',
    accent: '#6366f1',
  },
  {
    number: '02',
    title: 'Graduated Response Engine',
    subtitle: 'Proportional restrictions',
    description:
      "Gemini reasons about which specific capabilities to restrict based on the semantic relationship between the trigger and the client's product holdings. Not on/off. Proportional.",
    tech: 'Gemini 1.5 Pro · FastAPI',
    accent: '#38bdf8',
  },
  {
    number: '03',
    title: 'Investigation Orchestrator',
    subtitle: 'Multi-agent pipeline',
    description:
      'An 8-node LangGraph pipeline: baseline pull → FINTRAC tagging → money flow mapping → cross-client correlation → sanctions check → classification → STR drafting.',
    tech: 'LangGraph · Gemini · D3.js',
    accent: '#34d399',
  },
  {
    number: '04',
    title: 'Human Boundary',
    subtitle: 'Irreducible judgment',
    description:
      "Under Canada's PCMLTFA, filing an STR is a criminal act signed personally. The analyst makes one decision: file or don't. AI prepares the evidence; humans carry the liability.",
    tech: 'Next.js · Human review',
    accent: '#fb923c',
  },
]

const pipelineNodes = [
  { label: 'Transaction\nEvent', sub: 'trigger' },
  { label: 'Deviation\nAnalysis', sub: 'L1 · baseline' },
  { label: 'Contextual\nReasoning', sub: 'L2 · Gemini' },
  { label: 'Graduated\nResponse', sub: 'L2 · scope' },
  { label: 'Investigation\nOrchestration', sub: 'L3 · DAG' },
  { label: 'Human\nReview', sub: 'L4 · decision' },
]

export default function LandingPage() {
  return (
    <div
      className="min-h-screen"
      style={{ background: '#0a0a0f', color: '#e2e8f0' }}
    >
      <style>{`
        @keyframes particle-flow {
          0%   { left: -4px; opacity: 0; }
          8%   { opacity: 1; }
          92%  { opacity: 1; }
          100% { left: calc(100% + 4px); opacity: 0; }
        }
        @keyframes pulse-ring {
          0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
          70%  { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
          100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0; }
        }
        .particle {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 5px; height: 5px;
          border-radius: 50%;
          background: #818cf8;
          animation: particle-flow 2.4s linear infinite;
        }
        .particle:nth-child(2) { animation-delay: 0.8s; }
        .particle:nth-child(3) { animation-delay: 1.6s; }
        .node-pulse { animation: pulse-ring 2s ease-out infinite; }
        .cursor-blink { animation: blink 1s step-end infinite; }
        .layer-card:hover { border-color: rgba(99,102,241,0.35) !important; }
      `}</style>

      {/* ── Header ── */}
      <header style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div
          className="mx-auto flex items-center justify-between"
          style={{ maxWidth: 1280, padding: '1.25rem 2rem' }}
        >
          <span
            className={mono.className}
            style={{ fontSize: '0.8rem', letterSpacing: '0.18em', color: '#e2e8f0', fontWeight: 500 }}
          >
            SIMPLE<span style={{ color: '#818cf8' }}>RESOLVE</span>
          </span>
          <nav className="hidden sm:flex items-center gap-8">
            {[
              { href: '/dashboard', label: 'Dashboard' },
              { href: '/investigations', label: 'Investigations' },
              { href: '/clients', label: 'Clients' },
            ].map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={mono.className}
                style={{ color: '#64748b', fontSize: '0.72rem', textDecoration: 'none', letterSpacing: '0.08em', transition: 'color 0.15s' }}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="mx-auto" style={{ maxWidth: 1280, padding: '7rem 2rem 5rem' }}>
        <div
          className={mono.className}
          style={{ color: '#6366f1', fontSize: '0.65rem', letterSpacing: '0.35em', marginBottom: '2.5rem', fontWeight: 500 }}
        >
          AI-NATIVE AML INVESTIGATION — CANADA (FINTRAC)
        </div>

        <h1
          className={display.className}
          style={{
            fontSize: 'clamp(2.8rem, 8vw, 6.5rem)',
            lineHeight: 1.05,
            color: '#f8fafc',
            marginBottom: '1.75rem',
            maxWidth: 820,
          }}
        >
          AML Investigation.
          <br />
          <span style={{ color: '#818cf8' }}>Reimagined.</span>
        </h1>

        <p
          style={{
            fontSize: '1.05rem',
            color: '#94a3b8',
            lineHeight: 1.75,
            maxWidth: 580,
            marginBottom: '3rem',
          }}
        >
          SimpleResolve replaces binary account freezes with proportional, AI-driven
          interventions — and turns raw transaction data into FINTRAC-ready
          investigation narratives.
        </p>

        <div className="flex gap-3 flex-wrap items-center">
          <Link
            href="/dashboard"
            style={{
              background: '#4f46e5',
              color: '#fff',
              padding: '0.8rem 1.75rem',
              borderRadius: 4,
              textDecoration: 'none',
              fontSize: '0.85rem',
              fontWeight: 600,
              letterSpacing: '0.02em',
            }}
          >
            Enter Dashboard →
          </Link>
          <Link
            href="/investigations"
            style={{
              border: '1px solid rgba(99,102,241,0.35)',
              color: '#a5b4fc',
              padding: '0.8rem 1.75rem',
              borderRadius: 4,
              textDecoration: 'none',
              fontSize: '0.85rem',
              letterSpacing: '0.02em',
            }}
          >
            View Investigations →
          </Link>
        </div>

        {/* Subtle rule */}
        <div style={{ marginTop: '5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }} />
      </section>

      {/* ── Four Layers ── */}
      <section className="mx-auto" style={{ maxWidth: 1280, padding: '0 2rem 6rem' }}>
        <div
          className={mono.className}
          style={{ color: '#475569', fontSize: '0.65rem', letterSpacing: '0.3em', marginBottom: '3rem' }}
        >
          ARCHITECTURE — FOUR GRADUATED LAYERS
        </div>

        <div
          className="grid gap-px"
          style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr)', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: 8 }}
        >
          {layers.map((layer) => (
            <div
              key={layer.number}
              className="layer-card"
              style={{
                background: '#0a0a0f',
                padding: '2.25rem',
                borderLeft: `2px solid ${layer.accent}`,
                border: `1px solid rgba(255,255,255,0.05)`,
                transition: 'border-color 0.2s',
              }}
            >
              <div className="flex items-start justify-between mb-4">
                <span
                  className={mono.className}
                  style={{ color: layer.accent, fontSize: '1.75rem', fontWeight: 700, lineHeight: 1, opacity: 0.7 }}
                >
                  {layer.number}
                </span>
                <span
                  className={mono.className}
                  style={{ fontSize: '0.6rem', color: '#475569', letterSpacing: '0.12em', textTransform: 'uppercase', marginTop: 4 }}
                >
                  {layer.subtitle}
                </span>
              </div>
              <h3
                style={{ fontSize: '1rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '0.75rem' }}
              >
                {layer.title}
              </h3>
              <p style={{ fontSize: '0.83rem', color: '#64748b', lineHeight: 1.65 }}>
                {layer.description}
              </p>
              <div
                className={mono.className}
                style={{ marginTop: '1.5rem', fontSize: '0.65rem', color: '#334155', letterSpacing: '0.05em' }}
              >
                {layer.tech}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Pipeline Visualization ── */}
      <section
        style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          padding: '5rem 2rem',
          background: 'rgba(15,17,28,0.8)',
        }}
      >
        <div className="mx-auto" style={{ maxWidth: 1280 }}>
          <div
            className={mono.className}
            style={{ color: '#475569', fontSize: '0.65rem', letterSpacing: '0.3em', marginBottom: '3rem', textAlign: 'center' }}
          >
            PIPELINE — END-TO-END FLOW
          </div>

          {/* Mobile: vertical stack; Desktop: horizontal */}
          <div
            className="hidden lg:flex items-center justify-between"
            style={{ gap: 0 }}
          >
            {pipelineNodes.map((node, i) => (
              <div key={i} className="flex items-center flex-1">
                {/* Node */}
                <div
                  className="node-pulse"
                  style={{
                    background: 'rgba(99,102,241,0.08)',
                    border: '1px solid rgba(99,102,241,0.3)',
                    borderRadius: 6,
                    padding: '0.9rem 0.75rem',
                    minWidth: 110,
                    textAlign: 'center',
                    flexShrink: 0,
                  }}
                >
                  <div style={{ fontSize: '0.78rem', color: '#e2e8f0', fontWeight: 500, whiteSpace: 'pre-line', lineHeight: 1.3 }}>
                    {node.label}
                  </div>
                  <div
                    className={mono.className}
                    style={{ fontSize: '0.58rem', color: '#4f46e5', marginTop: '0.4rem', letterSpacing: '0.05em' }}
                  >
                    {node.sub}
                  </div>
                </div>

                {/* Connector (between nodes, not after last) */}
                {i < pipelineNodes.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: 2,
                      background: 'rgba(99,102,241,0.2)',
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    <div className="particle" />
                    <div className="particle" />
                    <div className="particle" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Mobile vertical */}
          <div className="lg:hidden flex flex-col items-center gap-2">
            {pipelineNodes.map((node, i) => (
              <div key={i} className="flex flex-col items-center">
                <div
                  style={{
                    background: 'rgba(99,102,241,0.08)',
                    border: '1px solid rgba(99,102,241,0.3)',
                    borderRadius: 6,
                    padding: '0.75rem 1.25rem',
                    textAlign: 'center',
                    minWidth: 180,
                  }}
                >
                  <div style={{ fontSize: '0.82rem', color: '#e2e8f0', fontWeight: 500, lineHeight: 1.3 }}>
                    {node.label.replace('\n', ' ')}
                  </div>
                  <div className={mono.className} style={{ fontSize: '0.6rem', color: '#4f46e5', marginTop: 3 }}>
                    {node.sub}
                  </div>
                </div>
                {i < pipelineNodes.length - 1 && (
                  <div style={{ width: 2, height: 24, background: 'rgba(99,102,241,0.25)' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI-Native section ── */}
      <section className="mx-auto" style={{ maxWidth: 1280, padding: '6rem 2rem' }}>
        <div
          className={mono.className}
          style={{ color: '#475569', fontSize: '0.65rem', letterSpacing: '0.3em', marginBottom: '3rem' }}
        >
          WHAT AI-NATIVE MEANS
        </div>

        <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
          {/* Left: remove Gemini thought experiment */}
          <div>
            <h2
              className={display.className}
              style={{ fontSize: '1.8rem', color: '#f1f5f9', marginBottom: '1.5rem', lineHeight: 1.2 }}
            >
              Test it: remove Gemini from SimpleResolve.
            </h2>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {[
                'Maintaining real-time behavioral profiles for millions of clients? Gone.',
                'Reasoning about which capabilities to restrict based on semantic relationship? Gone — rules engines can only do on/off.',
                'Cross-client coordination detection in real time? Gone — humans work one case at a time.',
                'Synthesising behavioral baseline + FINTRAC indicators + network data into a legal narrative? Gone.',
              ].map((item, i) => (
                <li key={i} className="flex gap-3" style={{ color: '#94a3b8', fontSize: '0.88rem', lineHeight: 1.6 }}>
                  <span style={{ color: '#4f46e5', flexShrink: 0, marginTop: '0.15rem' }}>—</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p
              style={{
                marginTop: '2rem',
                fontSize: '0.83rem',
                color: '#475569',
                fontStyle: 'italic',
                lineHeight: 1.6,
              }}
            >
              The workflow shape is fundamentally different. That is what AI-native means.
            </p>
          </div>

          {/* Right: stats terminal */}
          <div
            className={mono.className}
            style={{
              background: '#0d1117',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: 8,
              padding: '2rem',
              fontSize: '0.8rem',
            }}
          >
            <div style={{ color: '#6366f1', marginBottom: '1.5rem', fontSize: '0.65rem', letterSpacing: '0.2em' }}>
              PLATFORM METRICS — SIMULATED SCALE
            </div>
            {[
              { key: 'accounts_monitored', value: '3,200,000', label: 'Accounts monitored' },
              { key: 'risk_events_auto_resolved', value: '94.7%', label: 'Risk events auto-resolved at Level 0–1' },
              { key: 'avg_investigation_time', value: '4 min', label: 'Average investigation time' },
              { key: 'avg_restriction_scope', value: '1.8 products', label: 'Average restriction scope' },
              { key: 'binary_freeze_scope', value: '7.4 products', label: 'Legacy binary freeze scope' },
              { key: 'str_accuracy', value: '91.2%', label: 'STR draft classification accuracy' },
            ].map(({ key, value, label }) => (
              <div
                key={key}
                className="flex justify-between items-baseline"
                style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}
              >
                <span style={{ color: '#475569', fontSize: '0.72rem' }}>{label}</span>
                <span style={{ color: '#e2e8f0', fontWeight: 500, fontSize: '0.9rem' }}>{value}</span>
              </div>
            ))}
            <div style={{ color: '#334155', fontSize: '0.6rem', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>PROTOTYPE DEMO</span>
              <span className="cursor-blink">_</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer
        style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
          padding: '2.5rem 2rem',
        }}
      >
        <div
          className="mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          style={{ maxWidth: 1280 }}
        >
          <span
            className={mono.className}
            style={{ color: '#334155', fontSize: '0.7rem', letterSpacing: '0.08em' }}
          >
            SIMPLERESOLVE — Prototype. Not for production use.
          </span>
          <div className="flex gap-6">
            {[
              { href: '/dashboard', label: 'Dashboard' },
              { href: '/investigations', label: 'Investigations' },
              { href: '/clients', label: 'Clients' },
            ].map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={mono.className}
                style={{ color: '#475569', fontSize: '0.7rem', textDecoration: 'none', letterSpacing: '0.06em' }}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}
