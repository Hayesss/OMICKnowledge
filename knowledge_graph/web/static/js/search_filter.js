class SearchFilter {
  constructor(graphData) {
    this.data = graphData;
    this.searchInput = document.getElementById('search-input');
    this.searchResults = document.getElementById('search-results');
    this.filterTypes = document.getElementById('filter-types');
    this.filterTags = document.getElementById('filter-tags');
    this.filterDifficulty = document.getElementById('filter-difficulty');
    
    this.initFilters();
    this.initSearch();
    this.onFilterChange = null;
    this.onSearchSelect = null;
  }

  initFilters() {
    // Type filters
    const types = [...new Set(this.data.nodes.map(n => n.type))];
    types.forEach(type => {
      const label = document.createElement('label');
      label.innerHTML = `<input type="checkbox" value="${type}" checked> ${this.typeLabel(type)}`;
      this.filterTypes.appendChild(label);
    });
    
    // Tag filters
    const allTags = new Set();
    this.data.nodes.forEach(n => {
      (n.tags || []).forEach(tag => allTags.add(tag));
    });
    const sortedTags = [...allTags].sort();
    sortedTags.forEach(tag => {
      const label = document.createElement('label');
      label.innerHTML = `<input type="checkbox" value="${tag}"> ${tag}`;
      this.filterTags.appendChild(label);
    });
    
    // Event listeners
    this.filterTypes.querySelectorAll('input').forEach(cb => {
      cb.addEventListener('change', () => this.emitFilterChange());
    });
    this.filterTags.querySelectorAll('input').forEach(cb => {
      cb.addEventListener('change', () => this.emitFilterChange());
    });
    this.filterDifficulty.querySelectorAll('input').forEach(rb => {
      rb.addEventListener('change', () => this.emitFilterChange());
    });
  }

  typeLabel(type) {
    const labels = {
      assay: '实验类型',
      stage: '分析阶段',
      step: '分析步骤',
      tool: '工具软件',
      concept: '概念参数',
      issue: '常见问题',
      resource: '外部资源'
    };
    return labels[type] || type;
  }

  emitFilterChange() {
    if (this.onFilterChange) {
      this.onFilterChange(this.getFilterState());
    }
  }

  getFilterState() {
    const selectedTypes = [...this.filterTypes.querySelectorAll('input:checked')].map(cb => cb.value);
    const selectedTags = [...this.filterTags.querySelectorAll('input:checked')].map(cb => cb.value);
    const selectedDifficulty = this.filterDifficulty.querySelector('input:checked')?.value || 'all';
    return { selectedTypes, selectedTags, selectedDifficulty };
  }

  initSearch() {
    this.searchInput.addEventListener('input', () => {
      const query = this.searchInput.value.trim().toLowerCase();
      if (!query) {
        this.searchResults.style.display = 'none';
        return;
      }
      
      const matches = this.data.nodes.filter(n => 
        n.name.toLowerCase().includes(query) ||
        (n.tags || []).some(tag => tag.toLowerCase().includes(query))
      ).slice(0, 10);
      
      this.searchResults.innerHTML = '';
      if (matches.length === 0) {
        this.searchResults.innerHTML = '<div class="result-item">无匹配结果</div>';
      } else {
        matches.forEach(node => {
          const div = document.createElement('div');
          div.className = 'result-item';
          div.innerHTML = `<strong>${node.name}</strong> <span style="color:#9ca3af;font-size:11px;">${this.typeLabel(node.type)}</span>`;
          div.addEventListener('click', () => {
            this.searchInput.value = node.name;
            this.searchResults.style.display = 'none';
            if (this.onSearchSelect) {
              this.onSearchSelect(node);
            }
          });
          this.searchResults.appendChild(div);
        });
      }
      this.searchResults.style.display = 'block';
    });
    
    document.addEventListener('click', (e) => {
      if (!this.searchInput.contains(e.target) && !this.searchResults.contains(e.target)) {
        this.searchResults.style.display = 'none';
      }
    });
  }
}
