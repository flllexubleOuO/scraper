#!/bin/bash
# AWS EC2 部署脚本

set -e  # 遇到错误立即退出

echo "🚀 Starting deployment to AWS EC2..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}请不要使用root用户运行此脚本${NC}"
    exit 1
fi

# 更新系统
echo -e "${GREEN}📦 更新系统包...${NC}"
sudo apt-get update -y
sudo apt-get upgrade -y

# 安装Python 3和pip
echo -e "${GREEN}🐍 安装Python 3...${NC}"
sudo apt-get install -y python3 python3-pip python3-venv

# 安装Git（如果还没有）
echo -e "${GREEN}📥 安装Git...${NC}"
sudo apt-get install -y git

# 安装Chrome和ChromeDriver（用于Selenium）
echo -e "${GREEN}🌐 安装Chrome和ChromeDriver...${NC}"
sudo apt-get install -y wget unzip
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# 安装ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
echo "Chrome version: $CHROME_VERSION"
wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O /tmp/chromedriver_version
CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

# 克隆或更新代码
APP_DIR="$HOME/scraper"
if [ -d "$APP_DIR" ]; then
    echo -e "${GREEN}📂 更新代码...${NC}"
    cd "$APP_DIR"
    git pull origin main
else
    echo -e "${GREEN}📂 克隆代码仓库...${NC}"
    cd "$HOME"
    git clone https://github.com/flllexubleOuO/scraper.git
    cd scraper
fi

# 创建虚拟环境
echo -e "${GREEN}🔧 创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo -e "${GREEN}📦 安装Python依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 创建环境变量文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  创建.env文件...${NC}"
    cat > .env << EOF
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_PATH=job_scraper.db

# Flask
FLASK_SECRET_KEY=$(openssl rand -hex 32)
FLASK_PORT=8080
EOF
    echo -e "${YELLOW}⚠️  请编辑 .env 文件并填入你的OpenAI API Key${NC}"
    echo -e "${YELLOW}   nano ~/.env${NC}"
fi

# 创建systemd服务文件（Web应用）
echo -e "${GREEN}🔧 配置systemd服务...${NC}"
sudo tee /etc/systemd/system/scraper-web.service > /dev/null << EOF
[Unit]
Description=NZ IT Job Market Analyzer Web App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/simple_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 创建systemd服务文件（定时任务）
sudo tee /etc/systemd/system/scraper-scheduler.service > /dev/null << EOF
[Unit]
Description=NZ IT Job Market Analyzer Scheduler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/scheduler_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd
sudo systemctl daemon-reload

# 启动服务
echo -e "${GREEN}🚀 启动服务...${NC}"
sudo systemctl enable scraper-web
sudo systemctl start scraper-web
sudo systemctl enable scraper-scheduler
sudo systemctl start scraper-scheduler

# 配置防火墙（如果使用UFW）
if command -v ufw &> /dev/null; then
    echo -e "${GREEN}🔒 配置防火墙...${NC}"
    sudo ufw allow 8080/tcp
    sudo ufw allow 22/tcp  # SSH
fi

# 显示状态
echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "📊 服务状态："
sudo systemctl status scraper-web --no-pager
echo ""
sudo systemctl status scraper-scheduler --no-pager
echo ""
echo "🌐 访问地址："
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
echo ""
echo "📝 有用的命令："
echo "   查看Web日志:       sudo journalctl -u scraper-web -f"
echo "   查看Scheduler日志: sudo journalctl -u scraper-scheduler -f"
echo "   重启Web服务:       sudo systemctl restart scraper-web"
echo "   重启Scheduler:     sudo systemctl restart scraper-scheduler"
echo "   停止服务:          sudo systemctl stop scraper-web scraper-scheduler"
echo ""
echo -e "${YELLOW}⚠️  别忘了在AWS安全组中开放8080端口！${NC}"

