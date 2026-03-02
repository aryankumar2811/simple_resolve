'use client'
import { useEffect, useRef } from 'react'
import type { MoneyFlow } from '@/lib/api'

// Node type → visual properties
const NODE_COLORS: Record<string, string> = {
  external_source: '#6366f1',
  product: '#0ea5e9',
  external_destination: '#f97316',
  external_wallet: '#ef4444',
}

const NODE_RADIUS = 22

interface Props {
  data: MoneyFlow
}

export default function MoneyFlowGraph({ data }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data?.nodes?.length) return

    // Dynamic import of D3 to avoid SSR issues
    import('d3').then((d3) => {
      const svg = d3.select(svgRef.current)
      svg.selectAll('*').remove()

      const width = svgRef.current!.clientWidth || 500
      const height = 340

      // Convert API nodes/edges to D3 format
      const nodes = data.nodes.map((n) => ({ ...n })) as (typeof data.nodes[0] & { x?: number; y?: number })[]
      const links = data.edges.map((e) => ({
        source: e.from,
        target: e.to,
        amount: e.amount,
        type: e.type,
      }))

      const simulation = d3
        .forceSimulation(nodes as d3.SimulationNodeDatum[])
        .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(NODE_RADIUS + 10))

      // Arrowhead marker
      svg
        .append('defs')
        .append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', NODE_RADIUS + 8)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#94a3b8')

      // Edges
      const link = svg
        .selectAll('.link')
        .data(links)
        .enter()
        .append('g')
        .attr('class', 'link')

      link
        .append('line')
        .attr('stroke', '#94a3b8')
        .attr('stroke-width', (d) => Math.max(1, Math.log10((d.amount || 1) / 1000) * 2 + 1))
        .attr('marker-end', 'url(#arrow)')

      link
        .append('text')
        .text((d) => `$${((d.amount as number) / 1000).toFixed(1)}k`)
        .attr('font-size', 9)
        .attr('fill', '#64748b')
        .attr('text-anchor', 'middle')

      // Nodes
      const node = svg
        .selectAll('.node')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(
          d3
            .drag<SVGGElement, any>()
            .on('start', (event, d) => {
              if (!event.active) simulation.alphaTarget(0.3).restart()
              d.fx = d.x; d.fy = d.y
            })
            .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
            .on('end', (event, d) => {
              if (!event.active) simulation.alphaTarget(0)
              d.fx = null; d.fy = null
            }),
        )

      node
        .append('circle')
        .attr('r', NODE_RADIUS)
        .attr('fill', (d: any) => NODE_COLORS[d.type] || '#94a3b8')
        .attr('fill-opacity', 0.85)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)

      node
        .append('text')
        .text((d: any) => {
          const label = d.label as string
          return label.length > 12 ? label.slice(0, 10) + '…' : label
        })
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', 9)
        .attr('fill', '#fff')
        .attr('font-weight', '600')

      simulation.on('tick', () => {
        link.select('line')
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y)

        link.select('text')
          .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
          .attr('y', (d: any) => (d.source.y + d.target.y) / 2 - 6)

        node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
      })
    })
  }, [data])

  if (!data?.nodes?.length) {
    return (
      <div className="h-[340px] flex items-center justify-center text-slate-400 text-sm">
        No money flow data available
      </div>
    )
  }

  return (
    <div>
      <svg ref={svgRef} className="w-full" height={340} />
      <div className="flex gap-4 mt-2 text-xs text-slate-500 flex-wrap">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full inline-block" style={{ background: color }} />
            {type.replace(/_/g, ' ')}
          </span>
        ))}
      </div>
    </div>
  )
}
