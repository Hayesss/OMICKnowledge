var typeColors = {
  assay: '#3b82f6',
  stage: '#22c55e',
  step: '#f97316',
  tool: '#ec4899',
  concept: '#a855f7',
  issue: '#ef4444',
  resource: '#14b8a6'
};

class FlowView {
  constructor(svgSelector, containerSelector) {
    this.arrowId = `arrow-${Math.random().toString(36).substr(2, 9)}`;
    this.svg = d3.select(svgSelector);
    this.container = document.querySelector(containerSelector);
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 2])
      .on('zoom', (event) => {
        if (this.g) this.g.attr('transform', event.transform);
      });
    this.svg.call(this.zoom);
  }

  render(graphData, rootAssayId = null) {
    this.svg.selectAll('*').remove();
    this.g = this.svg.append('g');
    
    // Build hierarchy from edges
    const nodes = graphData.nodes.map(n => ({...n}));
    const edges = graphData.edges.map(e => ({...e}));
    
    // Filter to show assay -> stage -> step -> tool chain
    const validRelations = ['has_stage', 'has_step', 'uses_tool', 'prerequisite_for'];
    const flowEdges = edges.filter(e => validRelations.includes(e.relation));
    
    // If rootAssayId specified, filter to that assay's subtree
    let visibleNodes = nodes;
    let visibleEdges = flowEdges;
    
    if (rootAssayId) {
      const visibleIds = new Set([rootAssayId]);
      const queue = [rootAssayId];
      while (queue.length) {
        const id = queue.shift();
        flowEdges.forEach(e => {
          if (e.source === id && !visibleIds.has(e.target)) {
            visibleIds.add(e.target);
            queue.push(e.target);
          }
        });
      }
      visibleEdges = flowEdges.filter(e => 
        visibleIds.has(e.source) && visibleIds.has(e.target)
      );
      visibleNodes = nodes.filter(n => visibleIds.has(n.id));
    }
    
    // Build dagre graph
    const g = new dagre.graphlib.Graph().setGraph({
      rankdir: 'TB',
      nodesep: 40,
      ranksep: 60,
      marginx: 20,
      marginy: 20
    }).setDefaultEdgeLabel(() => ({}));
    
    visibleNodes.forEach(n => {
      g.setNode(n.id, { label: n.name, width: 120, height: 40, data: n });
    });
    
    visibleEdges.forEach(e => {
      g.setEdge(e.source, e.target);
    });
    
    dagre.layout(g);
    
    const graphWidth = g.graph().width || 0;
    const graphHeight = g.graph().height || 0;
    if (graphWidth === 0 || graphHeight === 0) {
      return;
    }
    
    // Draw edges
    const edgeSelection = this.g.append('g')
      .selectAll('path')
      .data(g.edges())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', e => {
        const edge = g.edge(e);
        const points = edge.points;
        let d = `M${points[0].x},${points[0].y}`;
        for (let i = 1; i < points.length; i++) {
          d += ` L${points[i].x},${points[i].y}`;
        }
        return d;
      })
      .attr('fill', 'none')
      .attr('marker-end', `url(#${this.arrowId})`);
    
    // Arrow marker
    this.g.append('defs').append('marker')
      .attr('id', this.arrowId)
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 9)
      .attr('refY', 5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z')
      .attr('fill', '#9ca3af');
    
    // Draw nodes
    const nodeSelection = this.g.append('g')
      .selectAll('g')
      .data(g.nodes())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', n => {
        const node = g.node(n);
        return `translate(${node.x - node.width / 2},${node.y - node.height / 2})`;
      })
      .on('click', (event, n) => {
        event.stopPropagation();
        const nodeData = g.node(n).data;
        if (window.app && window.app.showDetail) {
          window.app.showDetail(nodeData);
        }
      });
    
    nodeSelection.append('rect')
      .attr('width', n => g.node(n).width)
      .attr('height', n => g.node(n).height)
      .attr('rx', 6)
      .attr('ry', 6)
      .attr('fill', n => typeColors[g.node(n).data.type] || '#6b7280')
      .attr('opacity', 0.15)
      .attr('stroke', n => typeColors[g.node(n).data.type] || '#6b7280')
      .attr('stroke-width', 2);
    
    nodeSelection.append('text')
      .attr('x', n => g.node(n).width / 2)
      .attr('y', n => g.node(n).height / 2 + 4)
      .attr('text-anchor', 'middle')
      .text(n => g.node(n).label)
      .attr('fill', '#374151')
      .attr('font-size', '12px');
    
    // Center the graph
    const scale = Math.min(
      this.width / (graphWidth + 80),
      this.height / (graphHeight + 80),
      1
    );
    const translateX = (this.width - graphWidth * scale) / 2;
    const translateY = (this.height - graphHeight * scale) / 2;
    
    this.svg.transition().duration(300).call(
      this.zoom.transform,
      d3.zoomIdentity.translate(translateX, translateY).scale(scale)
    );
  }

  resize() {
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
  }
}
