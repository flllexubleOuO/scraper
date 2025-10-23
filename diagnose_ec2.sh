#!/bin/bash
# EC2诊断脚本 - 检查Web应用和数据库状态

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 🔍 EC2 诊断脚本                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd ~/scraper || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  检查进程状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ps aux | grep -E "(simple_app|scheduler)" | grep -v grep
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  检查端口监听"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v netstat &> /dev/null; then
    netstat -tuln | grep 8080
else
    ss -tuln | grep 8080
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  检查数据库文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f job_scraper.db ]; then
    echo "✅ 数据库文件存在"
    ls -lh job_scraper.db
else
    echo "❌ 数据库文件不存在！"
    echo "解决方案: 运行爬虫创建数据库"
    echo "  python3 scrapers/integrated_scraper.py --sources seek"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  检查数据库中的数据"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL_JOBS=$(sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs;" 2>/dev/null || echo "0")
echo "总职位数: $TOTAL_JOBS"

if [ "$TOTAL_JOBS" -eq 0 ]; then
    echo "⚠️  数据库中没有数据！"
    echo "解决方案: 运行爬虫抓取数据"
    echo "  python3 scrapers/integrated_scraper.py --sources seek"
else
    echo "✅ 数据库中有 $TOTAL_JOBS 个职位"
    echo ""
    echo "最新5个职位:"
    sqlite3 job_scraper.db "SELECT id, title, company, source FROM jobs ORDER BY created_at DESC LIMIT 5;"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  测试API端点"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "测试 /api/stats ..."
STATS_RESPONSE=$(curl -s http://localhost:8080/api/stats 2>&1)
if echo "$STATS_RESPONSE" | grep -q "total_jobs"; then
    echo "✅ Stats API 正常"
    echo "$STATS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATS_RESPONSE"
else
    echo "❌ Stats API 失败"
    echo "$STATS_RESPONSE"
fi
echo ""

echo "测试 /api/jobs ..."
JOBS_RESPONSE=$(curl -s http://localhost:8080/api/jobs?limit=2 2>&1)
if echo "$JOBS_RESPONSE" | grep -q "jobs"; then
    echo "✅ Jobs API 正常"
    echo "$JOBS_RESPONSE" | python3 -m json.tool 2>/dev/null | head -30
else
    echo "❌ Jobs API 失败"
    echo "$JOBS_RESPONSE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  检查应用日志（最后20行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f app.log ]; then
    tail -20 app.log
else
    echo "⚠️  app.log 不存在"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  检查环境变量"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f .env ]; then
    echo "✅ .env 文件存在"
    if grep -q "OPENAI_API_KEY" .env; then
        echo "✅ OPENAI_API_KEY 已配置"
    else
        echo "⚠️  OPENAI_API_KEY 未配置"
    fi
else
    echo "⚠️  .env 文件不存在"
    echo "AI功能将不可用"
fi
echo ""

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                      诊断完成                                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔍 问题排查建议:"
echo ""
echo "如果数据库为空:"
echo "  python3 scrapers/integrated_scraper.py --sources seek"
echo ""
echo "如果API无响应:"
echo "  ./stop_services.sh"
echo "  ./start_services.sh"
echo ""
echo "如果端口被占用:"
echo "  lsof -ti:8080 | xargs kill -9"
echo "  ./start_services.sh"
echo ""
echo "查看完整日志:"
echo "  tail -f app.log"
echo ""

