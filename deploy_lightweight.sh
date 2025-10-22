#!/bin/bash
# 轻量级部署脚本 - 适合低配置EC2实例（t2.micro等）

set -e

echo "🚀 轻量级部署模式..."

# 更新系统
sudo apt-get update -y

# 安装基本工具
sudo apt-get install -y python3 python3-pip git

# 克隆代码
cd ~
if [ ! -d "scraper" ]; then
    git clone https://github.com/flllexubleOuO/scraper.git
fi
cd scraper

# 安装依赖（最小化）
pip3 install flask requests beautifulsoup4 sqlalchemy python-dotenv schedule openai selenium

# 创建.env文件
if [ ! -f .env ]; then
    echo "OPENAI_API_KEY=your_key_here" > .env
    echo "⚠️  请编辑 .env 文件填入API Key: nano ~/.scraper/.env"
fi

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd ~/scraper
export $(cat .env | xargs)
nohup python3 simple_app.py > app.log 2>&1 &
nohup python3 scheduler_daemon.py > scheduler.log 2>&1 &
echo "✅ 服务已启动"
echo "Web: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
EOF

chmod +x start.sh

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f simple_app.py
pkill -f scheduler_daemon.py
echo "✅ 服务已停止"
EOF

chmod +x stop.sh

echo ""
echo "✅ 部署完成！"
echo ""
echo "📝 下一步："
echo "1. 编辑环境变量: nano .env"
echo "2. 启动服务:     ./start.sh"
echo "3. 查看日志:     tail -f app.log"
echo "4. 停止服务:     ./stop.sh"
echo ""
echo "⚠️  记得在AWS安全组开放8080端口！"

