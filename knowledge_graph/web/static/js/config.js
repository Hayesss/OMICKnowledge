// OMICKnowledge 配置文件
// 允许自定义 API 地址，支持多服务器部署

(function() {
  'use strict';
  
  // 从 localStorage 读取配置，或使用默认值
  const DEFAULT_API_HOST = 'localhost';
  const DEFAULT_API_PORT = '8000';
  
  // 读取保存的配置
  const savedHost = localStorage.getItem('omicknowledge_api_host');
  const savedPort = localStorage.getItem('omicknowledge_api_port');
  
  // 当前配置
  const config = {
    apiHost: savedHost || DEFAULT_API_HOST,
    apiPort: savedPort || DEFAULT_API_PORT,
    get apiBase() {
      return `http://${this.apiHost}:${this.apiPort}`;
    }
  };
  
  // 保存配置到 localStorage
  config.save = function() {
    localStorage.setItem('omicknowledge_api_host', this.apiHost);
    localStorage.setItem('omicknowledge_api_port', this.apiPort);
  };
  
  // 重置为默认
  config.reset = function() {
    this.apiHost = DEFAULT_API_HOST;
    this.apiPort = DEFAULT_API_PORT;
    this.save();
  };
  
  // 构建 API URL
  config.apiUrl = function(path) {
    // 确保路径以 / 开头
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    return this.apiBase + path;
  };
  
  // 暴露到全局
  window.OMICKnowledge = window.OMICKnowledge || {};
  window.OMICKnowledge.config = config;
  
  // 调试信息
  console.log('[OMICKnowledge] API 配置:', config.apiBase);
})();
