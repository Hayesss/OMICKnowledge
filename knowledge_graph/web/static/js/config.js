// OMICKnowledge 配置文件
// 自动检测服务器地址，支持远程部署

(function() {
  'use strict';
  
  // 尝试从服务器获取自动生成的配置
  let serverConfig = null;
  
  // 同步获取配置（首次加载时）
  try {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/api_config.json', false);  // 同步请求
    xhr.send();
    if (xhr.status === 200) {
      serverConfig = JSON.parse(xhr.responseText);
      console.log('[OMICKnowledge] 从服务器加载配置:', serverConfig);
    }
  } catch (e) {
    console.log('[OMICKnowledge] 未找到服务器配置，使用自动检测');
  }
  
  // 检测当前访问的服务器地址
  const currentHost = window.location.hostname;
  const currentPort = window.location.port;
  
  // 确定API主机和端口（优先级：serverConfig > localStorage > 自动检测 > 默认值）
  let apiHost, apiPort;
  
  // 1. 优先使用服务器生成的配置
  if (serverConfig) {
    apiHost = serverConfig.apiHost;
    apiPort = serverConfig.apiPort;
  } 
  // 2. 其次使用 localStorage 中保存的用户配置
  else {
    const savedHost = localStorage.getItem('omicknowledge_api_host');
    const savedPort = localStorage.getItem('omicknowledge_api_port');
    
    if (savedHost && savedPort) {
      apiHost = savedHost;
      apiPort = savedPort;
    } 
    // 3. 自动检测：如果当前不是通过 localhost 访问，则使用当前主机
    else if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      apiHost = currentHost;
      // Web端口已知，API端口需要猜测（通常是Web端口-80或自动检测）
      apiPort = String(parseInt(currentPort) - 80);  // 默认假设API端口=Web端口-80
    } 
    // 4. 默认值
    else {
      apiHost = 'localhost';
      apiPort = '8000';
    }
  }
  
  // 当前配置
  const config = {
    apiHost: apiHost,
    apiPort: apiPort,
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
    localStorage.removeItem('omicknowledge_api_host');
    localStorage.removeItem('omicknowledge_api_port');
    location.reload();
  };
  
  // 构建 API URL
  config.apiUrl = function(path) {
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    return this.apiBase + path;
  };
  
  // 暴露到全局
  window.OMICKnowledge = window.OMICKnowledge || {};
  window.OMICKnowledge.config = config;
  window.OMICKnowledge.serverConfig = serverConfig;
  
  // 调试信息
  console.log('[OMICKnowledge] API 配置:', config.apiBase);
  console.log('[OMICKnowledge] 当前访问:', window.location.host);
})();
