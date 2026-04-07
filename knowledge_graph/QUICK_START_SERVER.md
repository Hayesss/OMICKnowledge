# 服务器快速启动指南

5 分钟内在服务器上部署知识图谱。

## 最低要求

- Linux 服务器 (Ubuntu 20.04+, CentOS 7+)
- Docker & Docker Compose
- 2GB 内存

## 一键部署

```bash
# 1. 克隆仓库
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 2. 运行部署脚本
./deploy.sh
```

选择 `1) 完整栈`，等待服务启动。

## 访问服务

```
Open WebUI: http://服务器IP:3000
API:        http://服务器IP:8000
```

## 配置 Open WebUI

1. 访问 `http://服务器IP:3000`
2. 注册管理员账户
3. Admin Panel → Functions → Create Function
4. 粘贴 `open_webui_tools/kg_memory_tool_with_valves.py`
5. 配置 API Base URL: `http://host.docker.internal:8000`
6. 创建模型并绑定 Tool

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重启
docker-compose restart

# 更新
git pull
docker-compose build
docker-compose up -d
```

## 详细文档

- [完整部署指南](DEPLOYMENT.md)
- [Open WebUI 配置](OPEN_WEBUI_GUIDE.md)
