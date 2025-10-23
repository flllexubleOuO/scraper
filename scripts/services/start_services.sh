#!/bin/bash

# 服务启动脚本
# 用于启动Web应用和调度器，同时加载环境变量

set -e

# 获取项目根目录（scripts/services的上上级目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting services in directory: $PROJECT_ROOT"

# 加载环境变量
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "⚠️  Warning: .env file not found. Some features may not work."
fi

# 停止旧进程
echo "🛑 Stopping old processes..."
pkill -f simple_app.py || true
pkill -f scheduler_daemon.py || true
sleep 2

# 清理端口（如果被占用）
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
sleep 1

# 启动Web应用
echo "🌐 Starting web application..."
nohup python3 simple_app.py > app.log 2>&1 &
WEB_PID=$!
echo "Web app started with PID: $WEB_PID"

# 启动调度器
echo "⏰ Starting scheduler daemon..."
nohup python3 scheduler_daemon.py > scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "Scheduler started with PID: $SCHEDULER_PID"

# 等待服务启动
sleep 3

# 检查服务状态
echo ""
echo "🔍 Checking service status..."
if pgrep -f simple_app.py > /dev/null; then
    echo "✅ Web application is running"
else
    echo "❌ Web application failed to start"
    echo "Check app.log for details:"
    tail -20 app.log
    exit 1
fi

if pgrep -f scheduler_daemon.py > /dev/null; then
    echo "✅ Scheduler daemon is running"
else
    echo "❌ Scheduler daemon failed to start"
    echo "Check scheduler.log for details:"
    tail -20 scheduler.log
    exit 1
fi

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📊 Running processes:"
ps aux | grep -E "(simple_app|scheduler_daemon)" | grep -v grep
echo ""
echo "📝 To view logs:"
echo "  Web app:   tail -f app.log"
echo "  Scheduler: tail -f scheduler.log"
echo ""
echo "🌐 Access web interface at: http://localhost:8080"

