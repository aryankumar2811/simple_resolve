'use client'
import { useEffect, useRef } from 'react'
import type { NetworkGraph } from '@/lib/api'

const NODE_STYLES: Record<string, { color: string; label: string }> = {
  primary_client: { color: '#6366f1', label: 'Primary' },
  correlated_client: { color: '#f97316', label: 'Linked Client' },
  wallet_cluster: { color: '#ef4444', label: 'Wallet Cluster' },
}

interface Props {
  data: NetworkGraph
}

export default function CrossClientNetwork({ data }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data?.nodes?.length) return

    import('d3').then((d3) => {
      const svg = d3.select(svgRef.current)
      svg.selectAll('*').remove()

      const width = svgRef.current!.clientWidth || 500
      const height = 260

      const nodes = data.nodes.map((n) => ({ ...n })) as any[]
      const links = data.edges.map((e) => ({ source: e.from, target: e.to, type: e.type }))

      const simulation = d3
        .forceSimulation(nodes)
        .force('link', d3.forceLink(links).id((d: any) => d.id).distance(140))
        .force('charge', d3.forceManyBody().strength(-400))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(30))

      const link = svg
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('stroke', '#e2e8f0')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', (d: any) => (d.type === 'temporal_deposit_cluster' ? '5 3' : ''))

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
        .attr('r', (d: any) => (d.type === 'wallet_cluster' ? 18 : 24))
        .attr('fill', (d: any) => NODE_STYLES[d.type]?.color || '#94a3b8')
        .attr('fill-opacity', 0.85)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)

      node
        .append('text')
        .text((d: any) => (d.label as string).slice(0, 8))
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', 8)
        .attr('fill', '#fff')
        .attr('font-weight', '700')

      simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y)
        node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
      })
    })
  }, [data])

  if (!data?.nodes?.length) return null

  return (
    <div>
      <svg ref={svgRef} className="w-full" height={260} />
      <div className="flex gap-4 mt-2 text-xs text-slate-500">
        {Object.entries(NODE_STYLES).map(([type, { color, label }]) => (
          <span key={type} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full inline-block" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
