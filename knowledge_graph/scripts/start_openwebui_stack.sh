#!/bin/bash
# 启动知识图谱 + Open WebUI 完整栈

set -e

echo "=========================================="
echo "  多组学知识图谱 + Open WebUI 启动脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 pixi 是否安装
if ! command -v pixi &> /dev/null; then
    echo -e "${RED}错误: Pixi 未安装${NC}"
    echo "请先安装 Pixi: https://pixi.sh/"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}项目目录: $PROJECT_ROOT${NC}"
echo ""

# 检查记忆库是否存在
if [ ! -d "$PROJECT_ROOT/memory_store" ]; then
    echo -e "${YELLOW}记忆库未构建，正在构建...${NC}"
    pixi run build-memory
else
    echo -e "${GREEN}✓ 记忆库已存在${NC}"
fi

echo ""
echo "=========================================="
echo "  启动知识图谱 API 服务 (端口 8000)"
echo "=========================================="

# 检查 API 是否已在运行
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API 服务已在运行${NC}"
else
    echo "正在启动 API 服务..."
    pixi run serve-memory &
    API_PID=$!
    
    # 等待服务启动
    echo "等待 API 服务就绪..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 服务已启动 (PID: $API_PID)${NC}"
            break
        fi
        sleep 1
    done
    
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${RED}✗ API 服务启动失败${NC}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  启动 Open WebUI (端口 3000)"
echo "=========================================="

# 检查 Open WebUI 容器是否已存在
if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
    if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
        echo -e "${GREEN}✓ Open WebUI 容器已在运行${NC}"
    else
        echo "启动已有容器..."
        docker start open-webui
        echo -e "${GREEN}✓ Open WebUI 已启动${NC}"
    fi
else
    echo "创建 Open WebUI 容器..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux 需要添加 host 映射
        docker run -d \
            -p 3000:8080 \
            --add-host=host.docker.internal:host-gateway \
            -v open-webui:/app/backend/data \
            --name open-webui \
            ghcr.io/open-webui/open-webui:main
    else
        # macOS 和 Windows 不需要
        docker run -d \
            -p 3000:8080 \
            -v open-webui:/app/backend/data \
            --name open-webui \
            ghcr.io/open-webui/open-webui:main
    fi
    
    echo -e "${GREEN}✓ Open WebUI 容器已创建${NC}"
fi

echo ""
echo "=========================================="
echo "  启动完成！"
echo "=========================================="
echo ""
echo -e "📚 知识图谱 API: ${GREEN}http://localhost:8000${NC}"
echo -e "🌐 Open WebUI:    ${GREEN}http://localhost:3000${NC}"
echo ""
echo "首次使用 Open WebUI:"
echo "1. 访问 http://localhost:3000"
echo "2. 注册第一个账户（自动成为管理员）"
echo "3. 按 OPEN_WEBUI_GUIDE.md 配置知识图谱 Tool"
echo ""
echo "查看日志:"
echo "  - API 服务: 当前终端"
echo "  - Open WebUI: docker logs -f open-webui"
echo ""
echo "停止服务:"
echo "  - API 服务: Ctrl+C 或 kill $API_PID"
echo "  - Open WebUI: docker stop open-webui"
echo ""

# 保持脚本运行（如果 API 是在后台启动的）
if [ -n "$API_PID" ]; then
    wait $API_PID
fi
