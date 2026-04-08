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
  try {
    // Show loading indicator
    const svg = document.getElementById('viz-svg');
    if (svg) {
      svg.innerHTML = `
        <foreignObject width="100%" height="100%">
          <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;align-items:center;justify-content:center;height:100%;">
            <div style="text-align:center;color:#666;">
              <div style="width:40px;height:40px;border:3px solid #333;border-top-color:#3b82f6;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 12px;"></div>
              <p>加载知识图谱...</p>
            </div>
          </div>
        </foreignObject>
        <style>
          @keyframes spin { to { transform: rotate(360deg); } }
        </style>
      `;
    }
    
    // Try to load from API first (with cache-busting), fallback to static file
    const timestamp = Date.now();
    let response = await fetch(`http://localhost:8000/api/graph?t=${timestamp}`, {
      cache: 'no-store'
    });
    if (!response.ok) {
      console.log('API not available, falling back to static data...');
      response = await fetch('data/graph.json');
    }
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const graphData = await response.json();
    
    // Log which KB is loaded
    console.log(`Loaded graph for KB: ${graphData.kb_name || 'unknown'} (${graphData.kb_id || 'unknown'})`);
    console.log(`Total nodes: ${graphData.nodes?.length || 0}, edges: ${graphData.edges?.length || 0}`);
    
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
    
    // Update KB info display
    const kbBadge = document.getElementById('kbBadge');
    if (kbBadge && graphData.kb_name) {
      kbBadge.textContent = graphData.kb_name;
      kbBadge.title = `知识库: ${graphData.kb_name}\n节点数: ${graphData.nodes?.length || 0}\n边数: ${graphData.edges?.length || 0}`;
    }
  } catch (err) {
    console.error('Failed to load graph data:', err);
    const svg = document.getElementById('viz-svg');
    if (svg) {
      svg.innerHTML = `
        <foreignObject width="100%" height="100%">
          <div xmlns="http://www.w3.org/1999/xhtml" style="display:flex;align-items:center;justify-content:center;height:100%;font-family:sans-serif;">
            <div style="text-align:center;color:#6b7280;max-width:400px;padding:20px;">
              <p style="font-size:18px;font-weight:600;color:#ef4444;margin-bottom:12px;">无法加载图谱数据</p>
              <p style="font-size:14px;line-height:1.6;margin-bottom:16px;">
                如果你是通过 <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;">file://</code> 协议直接打开本页面，
                浏览器安全策略会阻止加载本地 JSON 数据。
              </p>
              <p style="font-size:14px;line-height:1.6;margin-bottom:8px;">请通过本地服务器访问：</p>
              <code style="display:block;background:#1f2937;color:#e5e7eb;padding:12px;border-radius:6px;font-size:12px;text-align:left;">cd web && python3 -m http.server 8080</code>
              <p style="font-size:12px;margin-top:12px;color:#9ca3af;">然后打开 <a href="http://localhost:8080" style="color:#2563eb;">http://localhost:8080</a></p>
            </div>
          </div>
        </foreignObject>
      `;
    }
  }
});

class App {
  constructor(graphData) {
    this.data = graphData;
    this.assays = graphData.nodes.filter(n => n.type === 'assay').sort((a, b) => a.name.localeCompare(b.name));
    this.currentAssay = this.assays.length ? this.assays[0].id : null;
    this.currentView = 'network';
    
    this.networkView = new NetworkView('#viz-svg', '.viz-container');
    this.flowView = new FlowView('#viz-svg', '.viz-container');
    this.searchFilter = new SearchFilter(graphData);
    
    this.detailPanel = document.getElementById('detail-panel');
    
    this.initAssaySelector();
    this.initViewSwitcher();
    this.initFilters();
    this.switchAssay(this.currentAssay);
  }

  initAssaySelector() {
    const select = document.getElementById('assay-select');
    select.innerHTML = '';
    this.assays.forEach(assay => {
      const option = document.createElement('option');
      option.value = assay.id;
      option.textContent = assay.name;
      select.appendChild(option);
    });
    select.addEventListener('change', (e) => {
      this.switchAssay(e.target.value);
    });
  }

  filterDataByAssay(assayId) {
    if (!assayId) return this.data;
    const visibleIds = new Set([assayId]);
    const queue = [assayId];
    while (queue.length) {
      const id = queue.shift();
      this.data.edges.forEach(e => {
        if (e.source === id && !visibleIds.has(e.target)) {
          visibleIds.add(e.target);
          queue.push(e.target);
        }
        if (e.target === id && !visibleIds.has(e.source)) {
          visibleIds.add(e.source);
          queue.push(e.source);
        }
      });
    }
    const nodes = this.data.nodes.filter(n => visibleIds.has(n.id));
    const edges = this.data.edges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target));
    return { nodes, edges };
  }

  switchAssay(assayId) {
    this.currentAssay = assayId;
    this.filteredData = this.filterDataByAssay(assayId);
    
    // Update search/filter to use filtered data
    this.searchFilter.rebuild(this.filteredData);
    this.initFilters();
    
    // Clear detail panel
    this.detailPanel.innerHTML = `<div class="empty-state"><p>点击节点查看详情</p></div>`;
    
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
      this.networkView.render(this.filteredData);
      this.applyFilters();
    } else {
      this.flowView.render(this.filteredData, this.currentAssay);
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
    
    // 1. Detailed explanation (universal)
    if (node.detailed_explanation) {
      extraHtml += this.renderSection('详细解释', this.formatMultiline(node.detailed_explanation));
    }
    
    // 2. Type-specific fields
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
      // Auto-fetched info
      if (node.auto_fetched) {
        const af = node.auto_fetched;
        let afHtml = '';
        if (af.latest_version) afHtml += `<div><strong>最新版本:</strong> ${escapeHtml(af.latest_version)}</div>`;
        if (af.published_at) afHtml += `<div><strong>发布时间:</strong> ${escapeHtml(af.published_at)}</div>`;
        if (af.release_url) afHtml += `<div><strong>发布页:</strong> <a href="${escapeHtml(af.release_url)}" target="_blank">${escapeHtml(af.release_url)}</a></div>`;
        if (af.fetched_at) afHtml += `<div style="color:#9ca3af;font-size:11px;margin-top:4px;">抓取于 ${escapeHtml(af.fetched_at)}</div>`;
        if (afHtml) extraHtml += `<div class="detail-section"><h4>自动更新信息</h4><div style="font-size:13px;line-height:1.6;">${afHtml}</div></div>`;
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
      if (node.common_misconceptions && node.common_misconceptions.length) {
        extraHtml += this.renderListSection('常见误区', node.common_misconceptions);
      }
    }
    
    if (node.type === 'issue') {
      extraHtml += this.renderSection('解决方案', node.solution ? this.formatMultiline(node.solution) : '暂无');
      if (node.related_tools && node.related_tools.length) {
        extraHtml += `<div class="detail-section"><h4>相关工具</h4>`;
        node.related_tools.forEach(tid => {
          const tnode = this.data.nodes.find(n => n.id === tid);
          const tname = tnode ? tnode.name : tid;
          extraHtml += `<div class="related-node" onclick="app.showDetailById('${escapeHtml(tid)}')">${escapeHtml(tname)}</div>`;
        });
        extraHtml += `</div>`;
      }
    }
    
    if (node.type === 'resource') {
      if (node.url) {
        extraHtml += this.renderSection('链接', `<a href="${escapeHtml(node.url)}" target="_blank">${escapeHtml(node.url)}</a>`);
      }
      if (node.resource_type) {
        extraHtml += this.renderSection('资源类型', node.resource_type);
      }
    }
    
    // 3. Edge properties (notes on connected edges)
    const connectedEdges = this.data.edges.filter(e => e.source === node.id || e.target === node.id);
    const edgesWithNotes = connectedEdges.filter(e => e.properties && (e.properties.note || e.properties.recommended));
    if (edgesWithNotes.length) {
      extraHtml += `<div class="detail-section"><h4>连接备注</h4>`;
      edgesWithNotes.forEach(e => {
        const other = this.data.nodes.find(n => n.id === (e.source === node.id ? e.target : e.source));
        const otherName = other ? other.name : (e.source === node.id ? e.target : e.source);
        const badge = e.properties.recommended ? '<span style="background:#dbeafe;color:#1e40af;padding:1px 5px;border-radius:4px;font-size:11px;margin-right:4px;">推荐</span>' : '';
        const note = e.properties.note || '';
        extraHtml += `<div style="font-size:13px;background:#f9fafb;padding:8px 10px;border-radius:4px;margin-bottom:6px;">${badge}<strong>${escapeHtml(otherName)}</strong> <span style="color:#9ca3af">(${e.relation})</span>${note ? `<div style="margin-top:2px;color:#4b5563;">${escapeHtml(note)}</div>` : ''}</div>`;
      });
      extraHtml += `</div>`;
    }
    
    // 4. Related nodes
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
    
    // 5. Metadata
    let metaHtml = '';
    if (node.source) metaHtml += `<div style="font-size:11px;color:#9ca3af;margin-top:2px;">来源: ${escapeHtml(node.source)}</div>`;
    if (node.last_updated) metaHtml += `<div style="font-size:11px;color:#9ca3af;">更新于: ${escapeHtml(node.last_updated)}</div>`;
    
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
      ${metaHtml ? `<div class="detail-section" style="border-top:1px solid #e5e7eb;padding-top:12px;margin-top:20px;">${metaHtml}</div>` : ''}
    `;
  }

  showDetailById(nodeId) {
    const node = this.data.nodes.find(n => n.id === nodeId);
    if (node) this.showDetail(node);
  }

  formatMultiline(text) {
    if (!text) return '';
    return escapeHtml(text)
      .split('\n')
      .map(line => line.trim() ? `<p style="margin-bottom:8px;">${line}</p>` : '')
      .join('');
  }

  renderSection(title, content) {
    return `<div class="detail-section"><h4>${escapeHtml(title)}</h4><div>${content}</div></div>`;
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
