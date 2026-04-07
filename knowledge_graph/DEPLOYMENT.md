# 服务器部署指南

在服务器上部署知识图谱系统的完整步骤。

## 环境要求

- Linux/macOS/Windows Server
- Docker & Docker Compose (推荐)
- 或 Python 3.9+ + Pixi
- 内存: 至少 2GB (推荐 4GB)
- 磁盘: 至少 5GB 可用空间

---

## 方案 1: Docker 部署 (推荐)

最简单的部署方式，适合生产环境。

### 步骤 1: 拉取代码

```bash
# 在服务器上执行
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph
```

### 步骤 2: 启动完整栈

```bash
# 一键启动所有服务 (API + Open WebUI + Ollama)
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务将运行在:
- API: http://localhost:8000
- Open WebUI: http://localhost:3000
- Ollama: http://localhost:11434

### 步骤 3: 配置 Open WebUI

1. 访问 `http://服务器IP:3000`
2. 注册管理员账户
3. 导入知识图谱 Tool:
   - Admin Panel → Functions → Create Function
   - 粘贴 `open_webui_tools/kg_memory_tool_with_valves.py` 内容
   - 配置 API Base URL: `http://host.docker.internal:8000`

---

## 方案 2: 手动部署

适合需要自定义配置的场景。

### 步骤 1: 安装依赖

```bash
# 安装 Pixi
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc

# 验证
pixi --version
```

### 步骤 2: 拉取代码

```bash
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph
```

### 步骤 3: 安装项目依赖

```bash
pixi install
```

### 步骤 4: 构建知识库

```bash
# 构建图谱和记忆库
pixi run build
pixi run build-memory

# 验证
ls -la memory_store/
```

### 步骤 5: 启动 API 服务

```bash
# 前台运行 (调试)
pixi run serve-memory

# 或后台运行
nohup pixi run serve-memory > api.log 2>&1 &

# 验证
 curl http://localhost:8000/health
```

### 步骤 6: 配置 systemd 服务 (推荐)

创建服务文件 `/etc/systemd/system/kg-api.service`:

```ini
[Unit]
Description=Knowledge Graph API
After=network.target

[Service]
Type=simple
User=kguser
WorkingDirectory=/opt/OMICKnowledge/knowledge_graph
ExecStart=/usr/local/bin/pixi run serve-memory
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kg-api
sudo systemctl start kg-api
sudo systemctl status kg-api
```

---

## 方案 3: 裸机部署 (高级)

适合没有 Docker 的环境。

### 安装步骤

```bash
# 1. 创建用户
sudo useradd -m -s /bin/bash kguser
sudo su - kguser

# 2. 拉取代码
cd ~
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph

# 3. 安装 pixi
curl -fsSL https://pixi.sh/install.sh | bash
export PATH="$HOME/.pixi/bin:$PATH"

# 4. 安装依赖
pixi install

# 5. 构建
pixi run build-memory

# 6. 启动服务 (使用 PM2 或 screen)
# 安装 PM2
npm install -g pm2

# 启动
pm2 start "pixi run serve-memory" --name kg-api

# 保存配置
pm2 save
pm2 startup
```

---

## Nginx 反向代理 (生产必需)

### 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 配置文件

创建 `/etc/nginx/sites-available/kg-api`:

```nginx
upstream kg_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://kg_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Open WebUI
upstream openwebui {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name chat.yourdomain.com;

    location / {
        proxy_pass http://openwebui;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/kg-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### HTTPS (SSL)

使用 Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com -d chat.yourdomain.com
```

---

## 防火墙配置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # API (如直接暴露)
sudo ufw allow 3000/tcp  # Open WebUI (如直接暴露)
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

---

## 监控与维护

### 查看日志

```bash
# Docker
docker-compose logs -f kg-api

# systemd
sudo journalctl -u kg-api -f

# PM2
pm2 logs kg-api
```

### 备份

```bash
# 备份知识库
tar -czf backup-$(date +%Y%m%d).tar.gz memory_store/ content/ edges/

# 自动备份脚本 (添加到 crontab)
0 2 * * * cd /opt/OMICKnowledge/knowledge_graph && tar -czf backups/backup-$(date +\%Y\%m\%d).tar.gz memory_store/ content/ edges/ > /dev/null 2>&1
```

### 更新

```bash
# 拉取最新代码
git pull origin main

# 重建
pixi run build-memory

# 重启服务
sudo systemctl restart kg-api
# 或
docker-compose restart kg-api
```

---

## 故障排除

### API 无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
pixi run serve-memory  # 前台运行查看错误

# 重建记忆库
rm -rf memory_store/
pixi run build-memory
```

### Open WebUI 无法连接 API

```bash
# 检查网络
curl http://localhost:8000/health

# 检查防火墙
sudo ufw status

# Docker 网络问题
docker network ls
docker network inspect kg-network
```

### 内存不足

```bash
# 添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 快速检查清单

部署完成后验证:

- [ ] API 健康检查: `curl http://localhost:8000/health`
- [ ] Open WebUI 访问: `http://服务器IP:3000`
- [ ] Nginx 配置: `sudo nginx -t`
- [ ] HTTPS 证书: `curl -I https://api.yourdomain.com/health`
- [ ] 防火墙规则: `sudo ufw status` 或 `sudo firewall-cmd --list-all`
- [ ] 自动启动: 重启服务器验证服务自启
- [ ] 备份脚本: 手动运行一次验证

---

## 相关文档

- [快速开始](QUICK_START_OPENWEBUI.md)
- [Open WebUI 配置](OPEN_WEBUI_GUIDE.md)
- [CI/CD 指南](CI_CD_GUIDE.md)
- [Docker 文档](https://docs.docker.com/)
- [Nginx 文档](https://nginx.org/en/docs/)
