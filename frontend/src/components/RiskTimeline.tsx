'use client'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'

interface Props {
  data: { date: string; score: number }[]
}

export default function RiskTimeline({ data }: Props) {
  const formatted = data.map((d) => ({
    date: d.date.slice(5),   // "MM-DD"
    score: d.score,
  }))

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">Risk Score — 30-Day History</h3>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={4} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
          <Tooltip
            formatter={(v: number) => [v.toFixed(2), 'Risk Score']}
            labelFormatter={(l) => `Date: ${l}`}
          />
          {/* Level thresholds */}
          <ReferenceLine y={0.4} stroke="#3b82f6" strokeDasharray="4 2" label={{ value: 'L1', fontSize: 9, fill: '#3b82f6' }} />
          <ReferenceLine y={0.6} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'L2', fontSize: 9, fill: '#f59e0b' }} />
          <ReferenceLine y={0.75} stroke="#f97316" strokeDasharray="4 2" label={{ value: 'L3', fontSize: 9, fill: '#f97316' }} />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#6366f1"
            strokeWidth={2}
            fill="url(#riskGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex gap-4 mt-2 text-xs text-slate-500">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-500 inline-block" /> L1 Monitor 0.40</span>
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-500 inline-block" /> L2 Guardrail 0.60</span>
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-orange-500 inline-block" /> L3 Restrict 0.75</span>
      </div>
    </div>
  )
}
