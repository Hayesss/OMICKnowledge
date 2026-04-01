let app = null;

function escapeHtml(text) {
  if (text == null) return '';
  return text.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', async () => {
  const response = await fetch('data/graph.json');
  const graphData = await response.json();
  
  // Precompute link counts for node sizing
  const linkCounts = {};
  graphData.edges.forEach(e => {
    linkCounts[e.source] = (linkCounts[e.source] || 0) + 1;
    linkCounts[e.target] = (linkCounts[e.target] || 0) + 1;
  });
  graphData.nodes.forEach(n => {
    n.links = linkCounts[n.id] || 0;
  });
  
  app = new App(graphData);
  window.app = app;
});

class App {
  constructor(graphData) {
    this.data = graphData;
    this.currentView = 'network';
    
    this.networkView = new NetworkView('#viz-svg', '.viz-container');
    this.flowView = new FlowView('#viz-svg', '.viz-container');
    this.searchFilter = new SearchFilter(graphData);
    
    this.detailPanel = document.getElementById('detail-panel');
    
    this.initViewSwitcher();
    this.initFilters();
    this.renderCurrentView();
  }

  initViewSwitcher() {
    document.getElementById('btn-network').addEventListener('click', () => {
      this.switchView('network');
    });
    document.getElementById('btn-flow').addEventListener('click', () => {
      this.switchView('flow');
    });
  }

  switchView(view) {
    this.currentView = view;
    document.getElementById('btn-network').classList.toggle('active', view === 'network');
    document.getElementById('btn-network').setAttribute('aria-pressed', view === 'network');
    document.getElementById('btn-flow').classList.toggle('active', view === 'flow');
    document.getElementById('btn-flow').setAttribute('aria-pressed', view === 'flow');
    this.renderCurrentView();
  }

  renderCurrentView() {
    d3.select('#viz-svg').selectAll('*').remove();
    if (this.currentView === 'network') {
      this.networkView.render(this.data);
      this.applyFilters();
    } else {
      this.flowView.render(this.data, 'atac-seq');
    }
  }

  initFilters() {
    this.searchFilter.onFilterChange = (state) => {
      if (this.currentView === 'network') {
        this.applyFilters(state);
      }
    };
    
    this.searchFilter.onSearchSelect = (node) => {
      if (this.currentView === 'network') {
        this.networkView.highlightNode(node);
      }
      this.showDetail(node);
    };
  }

  applyFilters(state = null) {
    if (!state) state = this.searchFilter.getFilterState();
    
    this.networkView.resetFilter();
    this.networkView.filterNodes(node => {
      const typeMatch = state.selectedTypes.includes(node.type);
      const tagMatch = state.selectedTags.length === 0 || 
        (node.tags || []).some(tag => state.selectedTags.includes(tag));
      const diffMatch = state.selectedDifficulty === 'all' || 
        node.difficulty === state.selectedDifficulty;
      return typeMatch && tagMatch && diffMatch;
    });
  }

  showDetail(node) {
    const typeClass = `type-${node.type}`;
    const diffClass = `difficulty-${node.difficulty}`;
    
    let extraHtml = '';
    
    if (node.type === 'tool') {
      extraHtml += this.renderSection('版本', node.version || '未指定');
      extraHtml += this.renderSection('安装命令', node.install_cmd ? `<code>${escapeHtml(node.install_cmd)}</code>` : '未指定');
      extraHtml += this.renderSection('官方文档', node.doc_url ? `<a href="${escapeHtml(node.doc_url)}" target="_blank">${escapeHtml(node.doc_url)}</a>` : '未指定');
      if (node.pros && node.pros.length) {
        extraHtml += this.renderListSection('优点', node.pros);
      }
      if (node.cons && node.cons.length) {
        extraHtml += this.renderListSection('缺点', node.cons);
      }
      if (node.key_params && node.key_params.length) {
        extraHtml += this.renderParamsSection('关键参数', node.key_params);
      }
    }
    
    if (node.type === 'step') {
      extraHtml += this.renderSection('输入', node.input || '未指定');
      extraHtml += this.renderSection('输出', node.output || '未指定');
      if (node.key_params && node.key_params.length) {
        extraHtml += this.renderParamsSection('关键参数', node.key_params);
      }
    }
    
    if (node.type === 'concept') {
      extraHtml += this.renderSection('详细解释', node.detailed_explanation || '暂无');
      if (node.common_misconceptions && node.common_misconceptions.length) {
        extraHtml += this.renderListSection('常见误区', node.common_misconceptions);
      }
    }
    
    if (node.type === 'issue') {
      extraHtml += this.renderSection('解决方案', node.solution || '暂无');
    }
    
    // Related nodes
    const incoming = this.data.edges.filter(e => e.target === node.id);
    const outgoing = this.data.edges.filter(e => e.source === node.id);
    
    if (incoming.length) {
      extraHtml += `<div class="detail-section"><h4>上游关系</h4>`;
      incoming.forEach(e => {
        const src = this.data.nodes.find(n => n.id === e.source);
        if (src) {
          extraHtml += `<div class="related-node" onclick="app.showDetailById('${escapeHtml(src.id)}')">${escapeHtml(src.name)} <span style="color:#9ca3af">(${e.relation})</span></div>`;
        }
      });
      extraHtml += `</div>`;
    }
    
    if (outgoing.length) {
      extraHtml += `<div class="detail-section"><h4>下游关系</h4>`;
      outgoing.forEach(e => {
        const tgt = this.data.nodes.find(n => n.id === e.target);
        if (tgt) {
          extraHtml += `<div class="related-node" onclick="app.showDetailById('${escapeHtml(tgt.id)}')">${escapeHtml(tgt.name)} <span style="color:#9ca3af">(${e.relation})</span></div>`;
        }
      });
      extraHtml += `</div>`;
    }
    
    this.detailPanel.innerHTML = `
      <div class="detail-header">
        <span class="detail-type ${typeClass}">${this.typeLabel(node.type)}</span>
        <span class="difficulty-badge ${diffClass}">${this.diffLabel(node.difficulty)}</span>
        <h2>${escapeHtml(node.name)}</h2>
      </div>
      <div class="detail-section">
        <h4>描述</h4>
        <p>${escapeHtml(node.description)}</p>
      </div>
      <div class="detail-section">
        <h4>标签</h4>
        <p>${(node.tags || []).map(t => `<span style="background:#f3f4f6;padding:2px 6px;border-radius:4px;font-size:12px;margin-right:4px;">${escapeHtml(t)}</span>`).join('') || '无'}</p>
      </div>
      ${extraHtml}
    `;
  }

  showDetailById(nodeId) {
    const node = this.data.nodes.find(n => n.id === nodeId);
    if (node) this.showDetail(node);
  }

  renderSection(title, content) {
    return `<div class="detail-section"><h4>${escapeHtml(title)}</h4><p>${escapeHtml(content)}</p></div>`;
  }

  renderListSection(title, items) {
    return `<div class="detail-section"><h4>${escapeHtml(title)}</h4><ul>${items.map(i => `<li>${escapeHtml(i)}</li>`).join('')}</ul></div>`;
  }

  renderParamsSection(title, params) {
    const rows = params.map(p => `<tr><td style="font-weight:500">${escapeHtml(p.name)}</td><td>${escapeHtml(p.description)}</td><td style="color:#6b7280">默认: ${escapeHtml(p.default)}</td></tr>`).join('');
    return `<div class="detail-section"><h4>${escapeHtml(title)}</h4><table style="width:100%;font-size:12px;border-collapse:collapse"><tbody>${rows}</tbody></table></div>`;
  }

  typeLabel(type) {
    const labels = {
      assay: '实验类型', stage: '分析阶段', step: '分析步骤',
      tool: '工具软件', concept: '概念参数', issue: '常见问题', resource: '外部资源'
    };
    return labels[type] || type;
  }

  diffLabel(diff) {
    const labels = { beginner: '入门', intermediate: '进阶', advanced: '高级' };
    return labels[diff] || diff;
  }
}
