#!/bin/bash

# 服务停止脚本
# 用于停止Web应用和调度器

set -e

echo "🛑 Stopping all services..."

# 停止进程
pkill -f simple_app.py || echo "  simple_app.py not running"
pkill -f scheduler_daemon.py || echo "  scheduler_daemon.py not running"

# 等待进程完全停止
sleep 2

# 清理端口
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

# 检查是否还有残留进程
if pgrep -f "simple_app.py|scheduler_daemon.py" > /dev/null; then
    echo "⚠️  Warning: Some processes are still running"
    ps aux | grep -E "(simple_app|scheduler_daemon)" | grep -v grep
    echo ""
    echo "Force killing remaining processes..."
    pkill -9 -f simple_app.py || true
    pkill -9 -f scheduler_daemon.py || true
    sleep 1
fi

echo "✅ All services stopped"

