#!/bin/bash
# Pixi 方式启动知识图谱服务（无 Docker）

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
echo "║       OMICKnowledge - Pixi 启动脚本                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查环境
echo -e "${BLUE}检查环境...${NC}"

if ! command -v pixi &> /dev/null; then
    echo -e "${RED}❌ Pixi 未安装${NC}"
    echo "安装: curl -fsSL https://pixi.sh/install.sh | bash"
    exit 1
fi
echo -e "${GREEN}✓ Pixi 已安装${NC}"

# 检查依赖
if [ ! -d ".pixi/envs/default" ]; then
    echo -e "${YELLOW}⚠ 依赖未安装，正在安装...${NC}"
    pixi install
fi
echo -e "${GREEN}✓ 依赖已就绪${NC}"

# 检查记忆库
if [ ! -d "memory_store" ] || [ ! -f "memory_store/config.json" ]; then
    echo -e "${YELLOW}⚠ 记忆库未构建，正在构建...${NC}"
    pixi run build-memory
fi
echo -e "${GREEN}✓ 记忆库已就绪${NC}"

echo ""
echo "选择启动模式:"
echo "  1) API 服务 + 传统 Web 界面"
echo "  2) API 服务 + 语义搜索界面"
echo "  3) 仅 API 服务"
echo "  4) 停止所有服务"
echo ""
read -p "请输入 [1-4]: " MODE

MODE=${MODE:-1}

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 杀死占用端口的进程
kill_port() {
    local port=$1
    local pid=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}释放端口 $port (PID: $pid)${NC}"
        kill $pid 2>/dev/null || true
        sleep 1
    fi
}

case $MODE in
    1)
        echo -e "${BLUE}启动模式: API + 传统 Web 界面${NC}"
        
        # 检查端口
        if check_port 8000; then
            echo -e "${YELLOW}端口 8000 被占用，尝试释放...${NC}"
            kill_port 8000
        fi
        if check_port 8080; then
            echo -e "${YELLOW}端口 8080 被占用，尝试释放...${NC}"
            kill_port 8080
        fi
        
        # 启动 API
        echo -e "${BLUE}启动 API 服务 (端口 8000)...${NC}"
        nohup pixi run serve-memory > logs/api.log 2>&1 &
        API_PID=$!
        echo $API_PID > .api.pid
        
        # 等待 API 启动
        sleep 3
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 启动成功 (PID: $API_PID)${NC}"
        else
            echo -e "${YELLOW}⚠ API 可能还在启动中...${NC}"
        fi
        
        # 启动 Web 服务
        echo -e "${BLUE}启动 Web 服务 (端口 8080)...${NC}"
        cd web
        nohup python -m http.server 8080 > ../logs/web.log 2>&1 &
        WEB_PID=$!
        echo $WEB_PID > ../.web.pid
        cd ..
        echo -e "${GREEN}✓ Web 服务启动成功 (PID: $WEB_PID)${NC}"
        
        echo ""
        echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  服务已启动!${NC}"
        echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "访问地址:"
        echo "  API 文档:   http://localhost:8000/health"
        echo "  图谱界面:   http://localhost:8080"
        echo "  语义查询:   pixi run query-memory"
        echo ""
        echo "查看日志:"
        echo "  tail -f logs/api.log"
        echo "  tail -f logs/web.log"
        echo ""
        echo "停止服务:"
        echo "  ./start_pixi.sh 然后选择 4"
        ;;
        
    2)
        echo -e "${BLUE}启动模式: API + 语义搜索界面${NC}"
        
        # 检查端口
        if check_port 8000; then
            kill_port 8000
        fi
        if check_port 8081; then
            kill_port 8081
        fi
        
        # 启动 API
        echo -e "${BLUE}启动 API 服务 (端口 8000)...${NC}"
        nohup pixi run serve-memory > logs/api.log 2>&1 &
        API_PID=$!
        echo $API_PID > .api.pid
        
        sleep 3
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 启动成功 (PID: $API_PID)${NC}"
        fi
        
        # 启动语义搜索界面
        echo -e "${BLUE}启动语义搜索界面 (端口 8081)...${NC}"
        cd web_memory
        nohup python -m http.server 8081 > ../logs/memory_web.log 2>&1 &
        MEMWEB_PID=$!
        echo $MEMWEB_PID > ../.memory_web.pid
        cd ..
        echo -e "${GREEN}✓ 语义搜索界面启动成功 (PID: $MEMWEB_PID)${NC}"
        
        echo ""
        echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  服务已启动!${NC}"
        echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "访问地址:"
        echo "  API 文档:       http://localhost:8000/health"
        echo "  语义搜索界面:   http://localhost:8081"
        echo ""
        ;;
        
    3)
        echo -e "${BLUE}启动模式: 仅 API 服务${NC}"
        
        if check_port 8000; then
            kill_port 8000
        fi
        
        echo -e "${BLUE}启动 API 服务 (端口 8000)...${NC}"
        nohup pixi run serve-memory > logs/api.log 2>&1 &
        API_PID=$!
        echo $API_PID > .api.pid
        
        sleep 3
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API 启动成功 (PID: $API_PID)${NC}"
        fi
        
        echo ""
        echo "API 地址: http://localhost:8000"
        echo "查看日志: tail -f logs/api.log"
        ;;
        
    4)
        echo -e "${BLUE}停止所有服务...${NC}"
        
        # 停止 API
        if [ -f ".api.pid" ]; then
            kill $(cat .api.pid) 2>/dev/null && echo "✓ API 已停止" || echo "✗ API 未运行"
            rm -f .api.pid
        fi
        
        # 停止 Web
        if [ -f ".web.pid" ]; then
            kill $(cat .web.pid) 2>/dev/null && echo "✓ Web 已停止" || echo "✗ Web 未运行"
            rm -f .web.pid
        fi
        
        # 停止语义搜索
        if [ -f ".memory_web.pid" ]; then
            kill $(cat .memory_web.pid) 2>/dev/null && echo "✓ 语义搜索已停止" || echo "✗ 语义搜索未运行"
            rm -f .memory_web.pid
        fi
        
        # 确保端口释放
        kill_port 8000 2>/dev/null || true
        kill_port 8080 2>/dev/null || true
        kill_port 8081 2>/dev/null || true
        
        echo -e "${GREEN}✓ 所有服务已停止${NC}"
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
