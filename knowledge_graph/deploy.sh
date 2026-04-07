#!/bin/bash
# 服务器一键部署脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       OMICKnowledge 服务器部署脚本                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo "请先安装 Docker:"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose"
    exit 1
fi

echo -e "${GREEN}✓ Docker 已安装${NC}"

# 选择部署模式
echo ""
echo "选择部署模式:"
echo "  1) 完整栈 (API + Open WebUI + Ollama) - 推荐"
echo "  2) 仅 API"
echo "  3) 仅 API + Open WebUI (无 Ollama)"
echo ""
read -p "请输入 [1-3]: " DEPLOY_MODE

DEPLOY_MODE=${DEPLOY_MODE:-1}

# 创建 docker-compose 覆盖文件
case $DEPLOY_MODE in
    1)
        echo -e "${BLUE}部署模式: 完整栈${NC}"
        docker-compose up -d
        ;;
    2)
        echo -e "${BLUE}部署模式: 仅 API${NC}"
        docker-compose up -d kg-api
        ;;
    3)
        echo -e "${BLUE}部署模式: API + Open WebUI${NC}"
        docker-compose up -d kg-api open-webui
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

# 等待服务启动
echo ""
echo -e "${BLUE}等待服务启动...${NC}"
sleep 5

# 健康检查
echo ""
echo -e "${BLUE}检查服务状态...${NC}"

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API 服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠ API 服务可能还在启动中${NC}"
fi

if [ "$DEPLOY_MODE" == "1" ] || [ "$DEPLOY_MODE" == "3" ]; then
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Open WebUI 运行正常${NC}"
    else
        echo -e "${YELLOW}⚠ Open WebUI 可能还在启动中${NC}"
    fi
fi

# 显示状态
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  部署完成!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$DEPLOY_MODE" == "2" ]; then
    echo "API 地址: http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "Open WebUI: http://$(hostname -I | awk '{print $1}'):3000"
    echo "API 地址:   http://$(hostname -I | awk '{print $1}'):8000"
fi

if [ "$DEPLOY_MODE" == "1" ]; then
    echo "Ollama:     http://$(hostname -I | awk '{print $1}'):11434"
fi

echo ""
echo "管理命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "配置文件:"
echo "  编辑 docker-compose.yml 自定义配置"
echo ""

if [ "$DEPLOY_MODE" == "1" ] || [ "$DEPLOY_MODE" == "3" ]; then
    echo -e "${YELLOW}首次使用 Open WebUI:${NC}"
    echo "  1. 访问 http://服务器IP:3000"
    echo "  2. 注册管理员账户"
    echo "  3. 按 OPEN_WEBUI_GUIDE.md 配置知识图谱 Tool"
    echo ""
fi

echo -e "${BLUE}详细文档: DEPLOYMENT.md${NC}"
