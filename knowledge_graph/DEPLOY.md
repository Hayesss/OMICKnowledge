# OMICKnowledge 部署指南

## 系统要求

- Python 3.10+
- 4GB+ RAM (用于向量嵌入)
- Linux/macOS/Windows WSL

## 部署步骤

### 1. 克隆代码

```bash
git clone https://github.com/Hayesss/OMICKnowledge.git
cd OMICKnowledge/knowledge_graph
```

### 2. 安装 Pixi (包管理器)

```bash
# Linux/macOS
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc

# 或使用 conda 安装
conda install -c conda-forge pixi
```

### 3. 安装项目依赖

```bash
pixi install
```

### 4. 启动后端服务器

```bash
# 默认使用 kb/omics/memory_store
pixi run python -m memory_core.server --store kb/omics/memory_store

# 或使用绝对路径
pixi run python -m memory_core.server --store $(pwd)/kb/omics/memory_store
```

服务器将在 `http://0.0.0.0:8000` 启动。

### 5. 启动前端 (新终端)

```bash
cd web

# 方式1: Python 自带服务器
python3 -m http.server 8080

# 方式2: Node.js http-server (如果有 Node)
npx http-server -p 8080

# 方式3: Nginx (生产环境)
# 配置 nginx 指向 web/ 目录
```

访问 `http://服务器IP:8080` 即可使用。

## 生产环境部署

### 使用 Docker

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl python3 python3-pip

# 安装 Pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

WORKDIR /app
COPY . .

RUN pixi install

EXPOSE 8000 8080

CMD ["pixi", "run", "python", "-m", "memory_core.server"]
```

### 使用 Systemd 服务

创建 `/etc/systemd/system/omicknowledge.service`:

```ini
[Unit]
Description=OMICKnowledge API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/knowledge_graph
ExecStart=/root/.pixi/bin/pixi run python -m memory_core.server --store kb/omics/memory_store
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl enable omicknowledge
sudo systemctl start omicknowledge
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/knowledge_graph/web;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PORT` | API 服务器端口 | 8000 |
| `STORE_DIR` | 向量存储目录 | memory_store |

## 数据备份

重要数据目录:
```
kb/                    # 知识库数据
├── omics/
│   ├── content/       # YAML 实体文件
│   ├── wiki/          # Markdown Wiki
│   └── memory_store/  # 向量嵌入
└── .import_records/   # 导入历史
```

备份命令:
```bash
tar -czvf omicknowledge-backup-$(date +%Y%m%d).tar.gz kb/
```

## 故障排查

### 端口被占用
```bash
# 检查端口
lsof -i :8000

# 更换端口
pixi run python -m memory_core.server --port 8001
```

### 权限问题
```bash
# 确保目录可写
chmod -R 755 kb/
```

### 依赖问题
```bash
# 重新安装依赖
pixi clean
pixi install
```
