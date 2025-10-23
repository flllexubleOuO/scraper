#!/bin/bash

# Chrome和ChromeDriver安装脚本
# 适用于Amazon Linux 2023 / Amazon Linux 2

set -e

echo "🔧 Installing Chrome and ChromeDriver for Selenium..."

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

echo "📋 Detected OS: $OS $VERSION"

# 根据不同的系统安装Chrome
if [[ "$OS" == "amzn" ]]; then
    echo "📦 Installing Chrome on Amazon Linux..."
    
    # 下载Chrome RPM
    if [ ! -f /tmp/google-chrome-stable_current_x86_64.rpm ]; then
        wget -P /tmp https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    fi
    
    # 安装Chrome（可能需要sudo）
    if command -v google-chrome &> /dev/null; then
        echo "✅ Chrome already installed"
    else
        echo "Installing Chrome (may require sudo)..."
        sudo dnf install -y /tmp/google-chrome-stable_current_x86_64.rpm || \
        sudo yum install -y /tmp/google-chrome-stable_current_x86_64.rpm
    fi
    
    # 安装依赖
    sudo dnf install -y \
        liberation-fonts \
        liberation-narrow-fonts \
        liberation-mono-fonts \
        liberation-sans-fonts \
        liberation-serif-fonts \
        vulkan \
        xdg-utils || true

elif [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    echo "📦 Installing Chrome on Ubuntu/Debian..."
    
    # 添加Google Chrome源
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    
    # 更新并安装
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable

else
    echo "⚠️  Unsupported OS: $OS"
    echo "Please install Chrome manually"
    exit 1
fi

# 验证Chrome安装
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version)
    echo "✅ Chrome installed: $CHROME_VERSION"
else
    echo "❌ Chrome installation failed"
    exit 1
fi

# ChromeDriver会由Selenium自动管理（selenium >= 4.6.0）
echo "✅ ChromeDriver will be managed automatically by Selenium"

# 验证Selenium版本
echo ""
echo "🔍 Checking Selenium version..."
SELENIUM_VERSION=$(python3 -c "import selenium; print(selenium.__version__)" 2>/dev/null || echo "Not installed")
echo "Selenium version: $SELENIUM_VERSION"

if [[ "$SELENIUM_VERSION" != "Not installed" ]]; then
    # 检查是否支持自动驱动管理
    MAJOR_VERSION=$(echo $SELENIUM_VERSION | cut -d. -f1)
    if [ "$MAJOR_VERSION" -ge 4 ]; then
        echo "✅ Selenium $SELENIUM_VERSION supports automatic driver management"
    else
        echo "⚠️  Selenium $SELENIUM_VERSION may need manual ChromeDriver installation"
        echo "Consider upgrading: pip3 install --upgrade selenium"
    fi
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Test Chrome: google-chrome --version"
echo "2. Test scraper: python3 scrapers/integrated_scraper.py --sources seek"
echo ""

