#!/usr/bin/env python3
"""
一键启动 OMICKnowledge 前后端服务
"""

import subprocess
import sys
import time
import signal
import os
import argparse
import socket
import json
from pathlib import Path

# 默认配置
DEFAULT_API_PORT = int(os.environ.get('API_PORT', 8000))
DEFAULT_WEB_PORT = int(os.environ.get('WEB_PORT', 8080))
WEB_DIR = Path(__file__).parent.parent / "web"

def is_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

def find_available_port(start_port, max_port=65535):
    """查找可用端口"""
    for port in range(start_port, min(max_port, start_port + 100)):
        if is_port_available(port):
            return port
    return None

def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def generate_config(api_port, web_port):
    """生成前端配置文件"""
    local_ip = get_local_ip()
    config = {
        "apiHost": local_ip,
        "apiPort": api_port,
        "webPort": web_port,
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 写入 web 目录
    config_path = WEB_DIR / "api_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return local_ip

def get_parser():
    parser = argparse.ArgumentParser(description='启动 OMICKnowledge 服务')
    parser.add_argument('--api-port', type=int, default=DEFAULT_API_PORT, help='API 端口 (默认: 8000)')
    parser.add_argument('--web-port', type=int, default=DEFAULT_WEB_PORT, help='Web 端口 (默认: 8080)')
    parser.add_argument('--store', type=str, default='kb/omics/memory_store', help='Memory store 路径')
    parser.add_argument('--auto-port', action='store_true', help='自动查找可用端口')
    return parser

def log(msg):
    print(f"[OMICKnowledge] {msg}")

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    api_port = args.api_port
    web_port = args.web_port
    store_path = args.store
    
    # 检查端口是否可用（API端口）
    if args.auto_port or not is_port_available(api_port):
        new_port = find_available_port(api_port)
        if new_port and new_port != api_port:
            log(f"API端口 {api_port} 被占用，使用端口 {new_port}")
            api_port = new_port
        elif not is_port_available(api_port):
            log(f"错误: 无法找到可用API端口")
            return 1
    
    # 检查端口是否可用（Web端口）- 确保API和Web端口不同
    if args.auto_port or not is_port_available(web_port):
        new_port = find_available_port(web_port)
        # 确保不与API端口冲突
        if new_port == api_port:
            new_port = find_available_port(api_port + 1)
        if new_port and new_port != web_port:
            log(f"Web端口 {web_port} 被占用，使用端口 {new_port}")
            web_port = new_port
        elif not is_port_available(web_port):
            log(f"错误: 无法找到可用Web端口")
            return 1
    
    # 生成配置文件
    local_ip = generate_config(api_port, web_port)
    
    API_CMD = [sys.executable, "-m", "memory_core.server", "--store", store_path, "--port", str(api_port)]
    WEB_CMD = [sys.executable, "-m", "http.server", str(web_port)]
    
    log(f"启动服务 (API端口={api_port}, Web端口={web_port})...")
    
    # 启动 API 服务器
    log(f"启动 API 服务 (端口 {api_port})...")
    api_proc = subprocess.Popen(
        API_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # 等待 API 启动
    time.sleep(2)
    if api_proc.poll() is not None:
        log("API 启动失败！")
        return 1
    
    # 启动 Web 服务器
    log(f"启动 Web 服务 (端口 {web_port})...")
    web_proc = subprocess.Popen(
        WEB_CMD,
        cwd=WEB_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    time.sleep(1)
    if web_proc.poll() is not None:
        log("Web 启动失败！")
        api_proc.terminate()
        return 1
    
    log("=" * 60)
    log("✅ 服务已启动!")
    log("")
    log(f"📍 本机访问:")
    log(f"   API: http://localhost:{api_port}")
    log(f"   Web: http://localhost:{web_port}")
    log("")
    log(f"🌐 远程访问 (其他机器):")
    log(f"   API: http://{local_ip}:{api_port}")
    log(f"   Web: http://{local_ip}:{web_port}")
    log("")
    log(f"💡 配置文件已生成: web/api_config.json")
    log("=" * 60)
    log("按 Ctrl+C 停止所有服务")
    log("-" * 60)
    
    # 信号处理
    def shutdown(signum, frame):
        log("\n正在停止服务...")
        api_proc.terminate()
        web_proc.terminate()
        try:
            api_proc.wait(timeout=3)
            web_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            api_proc.kill()
            web_proc.kill()
        log("服务已停止")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # 实时输出日志
    import select
    
    api_proc.stdout.readline()
    web_proc.stdout.readline()
    
    try:
        while True:
            # 检查进程是否存活
            if api_proc.poll() is not None:
                log("API 服务意外退出!")
                web_proc.terminate()
                return 1
            if web_proc.poll() is not None:
                log("Web 服务意外退出!")
                api_proc.terminate()
                return 1
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    sys.exit(main())
