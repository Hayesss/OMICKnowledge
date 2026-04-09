#!/usr/bin/env python3
"""
一键启动 OMICKnowledge 前后端服务
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# 配置
API_PORT = 8000
WEB_PORT = 8080
API_CMD = [sys.executable, "-m", "memory_core.server", "--store", "kb/omics/memory_store"]
WEB_CMD = [sys.executable, "-m", "http.server", str(WEB_PORT)]
WEB_DIR = Path(__file__).parent.parent / "web"

def log(msg):
    print(f"[OMICKnowledge] {msg}")

def main():
    log("启动服务...")
    
    # 启动 API 服务器
    log(f"启动 API 服务 (端口 {API_PORT})...")
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
    log(f"启动 Web 服务 (端口 {WEB_PORT})...")
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
    
    log("=" * 50)
    log("✅ 服务已启动!")
    log(f"   API: http://localhost:{API_PORT}")
    log(f"   Web: http://localhost:{WEB_PORT}")
    log("=" * 50)
    log("按 Ctrl+C 停止所有服务")
    log("-" * 50)
    
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
