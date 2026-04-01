const typeColors = {
  assay: '#3b82f6',
  stage: '#22c55e',
  step: '#f97316',
  tool: '#ec4899',
  concept: '#a855f7',
  issue: '#ef4444',
  resource: '#14b8a6'
};

class NetworkView {
  constructor(svgSelector, containerSelector) {
    this.svg = d3.select(svgSelector);
    this.container = document.querySelector(containerSelector);
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.g = this.svg.append('g');
    
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        this.g.attr('transform', event.transform);
      });
    this.svg.call(this.zoom);
    
    this.simulation = null;
    this.nodes = [];
    this.edges = [];
    this.nodeElements = null;
    this.linkElements = null;
    this.labelElements = null;
  }

  render(graphData) {
    this.nodes = graphData.nodes.map(n => ({...n}));
    this.edges = graphData.edges.map(e => ({...e}));
    
    this.g.selectAll('*').remove();
    
    this.simulation = d3.forceSimulation(this.nodes)
      .force('link', d3.forceLink(this.edges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(30));
    
    this.linkElements = this.g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(this.edges)
      .enter()
      .append('line')
      .attr('class', 'link');
    
    const nodeGroup = this.g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(this.nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) this.simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) this.simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));
    
    nodeGroup.append('circle')
      .attr('r', d => 8 + Math.sqrt((d.links || 1)) * 2)
      .attr('fill', d => typeColors[d.type] || '#6b7280')
      .on('click', (event, d) => {
        event.stopPropagation();
        this.highlightNode(d);
        if (window.app && window.app.showDetail) {
          window.app.showDetail(d);
        }
      });
    
    nodeGroup.append('text')
      .attr('dx', 12)
      .attr('dy', 4)
      .text(d => d.name);
    
    this.nodeElements = nodeGroup;
    
    this.svg.on('click', () => {
      this.clearHighlight();
    });
    
    this.simulation.on('tick', () => {
      this.linkElements
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  highlightNode(selectedNode) {
    const neighborIds = new Set();
    neighborIds.add(selectedNode.id);
    
    this.edges.forEach(e => {
      if (e.source.id === selectedNode.id) neighborIds.add(e.target.id);
      if (e.target.id === selectedNode.id) neighborIds.add(e.source.id);
    });
    
    this.nodeElements.classed('dimmed', d => !neighborIds.has(d.id));
    this.linkElements.classed('dimmed', d => 
      d.source.id !== selectedNode.id && d.target.id !== selectedNode.id
    );
    this.linkElements.classed('highlighted', d => 
      d.source.id === selectedNode.id || d.target.id === selectedNode.id
    );
  }

  clearHighlight() {
    this.nodeElements.classed('dimmed', false);
    this.linkElements.classed('dimmed', false).classed('highlighted', false);
  }

  filterNodes(filterFn) {
    const visibleIds = new Set(this.nodes.filter(filterFn).map(n => n.id));
    this.nodeElements.style('display', d => visibleIds.has(d.id) ? null : 'none');
    this.linkElements.style('display', d => 
      visibleIds.has(d.source.id) && visibleIds.has(d.target.id) ? null : 'none'
    );
  }

  resetFilter() {
    this.nodeElements.style('display', null);
    this.linkElements.style('display', null);
  }

  resize() {
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.alpha(0.3).restart();
  }
}
