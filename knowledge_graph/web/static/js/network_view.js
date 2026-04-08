var typeColors = {
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
    this.svgSelector = svgSelector;
    this.containerSelector = containerSelector;
    this.svg = null;
    this.container = null;
    this.width = 0;
    this.height = 0;
    
    // Initialize zoom behavior
    this.currentTransform = d3.zoomIdentity;
    this.zoom = null;
    this.scale = 1;  // Manual scale for fallback
    this.translateX = 0;
    this.translateY = 0;
    
    this.simulation = null;
    this.nodes = [];
    this.edges = [];
    this.nodeElements = null;
    this.linkElements = null;
    this.g = null;
    
    // Bind wheel handler
    this._wheelHandler = this._handleWheel.bind(this);
  }
  
  // Manual wheel handler as fallback
  _handleWheel(event) {
    event.preventDefault();
    event.stopPropagation();
    
    // Debug log (remove in production)
    console.log('Wheel event:', event.deltaY, 'Current scale:', this.scale);
    
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    this.scale *= delta;
    this.scale = Math.max(0.1, Math.min(4, this.scale));
    
    console.log('New scale:', this.scale);
    this._applyTransform();
  }
  
  _applyTransform() {
    if (this.g) {
      this.g.attr('transform', `translate(${this.translateX},${this.translateY}) scale(${this.scale})`);
    }
  }
  
  initZoom() {
    if (!this.svg) return;
    
    // Get the raw SVG element
    const svgElement = this.svg.node();
    if (!svgElement) return;
    
    // Remove any existing wheel listeners
    svgElement.removeEventListener('wheel', this._wheelHandler);
    
    // Add manual wheel listener (direct DOM API for reliability)
    svgElement.addEventListener('wheel', this._wheelHandler, { passive: false });
    
    // Also try D3 zoom as primary method
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        this.currentTransform = event.transform;
        this.scale = event.transform.k;
        this.translateX = event.transform.x;
        this.translateY = event.transform.y;
        if (this.g) {
          this.g.attr('transform', event.transform);
        }
      });
    
    // Apply zoom to SVG
    this.svg.call(this.zoom)
      .on('dblclick.zoom', null);  // Disable double-click zoom
  }
  
  // Public methods for zoom control
  zoomIn() {
    this.scale *= 1.3;
    this.scale = Math.min(4, this.scale);
    this._applyTransform();
    
    // Also update D3 zoom if available
    if (this.svg && this.zoom) {
      this.svg.transition().duration(300).call(this.zoom.scaleBy, 1.3);
    }
  }
  
  zoomOut() {
    this.scale *= 0.7;
    this.scale = Math.max(0.1, this.scale);
    this._applyTransform();
    
    // Also update D3 zoom if available
    if (this.svg && this.zoom) {
      this.svg.transition().duration(300).call(this.zoom.scaleBy, 0.7);
    }
  }
  
  resetZoom() {
    this.scale = 1;
    this.translateX = 0;
    this.translateY = 0;
    this._applyTransform();
    
    // Also update D3 zoom if available
    if (this.svg && this.zoom) {
      this.svg.transition().duration(500).call(this.zoom.transform, d3.zoomIdentity);
    }
    this.currentTransform = d3.zoomIdentity;
  }

  render(graphData) {
    if (this.simulation) {
      this.simulation.stop();
    }
    
    // Re-initialize SVG reference (in case it was cleared)
    this.svg = d3.select(this.svgSelector);
    this.container = document.querySelector(this.containerSelector);
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    
    this.nodes = graphData.nodes.map(n => ({...n}));
    this.edges = graphData.edges.map(e => ({...e}));

    // Compute link counts for node sizing
    const linkCounts = {};
    this.edges.forEach(e => {
      linkCounts[e.source] = (linkCounts[e.source] || 0) + 1;
      linkCounts[e.target] = (linkCounts[e.target] || 0) + 1;
    });
    this.nodes.forEach(n => {
      n.links = linkCounts[n.id] || 0;
    });

    // Clear and re-setup
    this.svg.selectAll('*').remove();
    
    // Add a background rect first to capture events
    const bgRect = this.svg.append('rect')
      .attr('width', this.width)
      .attr('height', this.height)
      .attr('fill', 'transparent')
      .style('pointer-events', 'all');
    
    // Create group for graph content
    this.g = this.svg.append('g');
    
    // Initialize zoom after elements are created
    this.initZoom();
    
    // Make sure the rect doesn't block node interactions
    bgRect.lower();
    
    // Re-apply current transform if exists
    if (this.currentTransform && this.currentTransform !== d3.zoomIdentity) {
      this.g.attr('transform', this.currentTransform);
    }
    
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
    if (!this.nodeElements || !this.linkElements) return;
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
    if (!this.nodeElements || !this.linkElements) return;
    this.nodeElements.classed('dimmed', false);
    this.linkElements.classed('dimmed', false).classed('highlighted', false);
  }

  filterNodes(filterFn) {
    if (!this.nodeElements || !this.linkElements) return;
    const visibleIds = new Set(this.nodes.filter(filterFn).map(n => n.id));
    this.nodeElements.style('display', d => visibleIds.has(d.id) ? null : 'none');
    this.linkElements.style('display', d => 
      visibleIds.has(d.source.id) && visibleIds.has(d.target.id) ? null : 'none'
    );
  }

  resetFilter() {
    if (!this.nodeElements || !this.linkElements) return;
    this.nodeElements.style('display', null);
    this.linkElements.style('display', null);
  }

  resize() {
    if (!this.simulation) return;
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
    this.simulation.alpha(0.3).restart();
  }
}
