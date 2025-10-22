# 🚨 EC2上Chrome未安装 - 快速修复

## 问题
Selenium无法找到Chrome浏览器，导致所有爬虫都失败。

## 立即修复（在EC2上运行）

### 选项1: 使用自动安装脚本（推荐）

```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<YOUR_EC2_IP>

# 进入项目目录
cd ~/scraper

# 如果还没有最新代码，先拉取
git pull origin main

# 赋予安装脚本执行权限
chmod +x install_chrome.sh

# 运行安装脚本
./install_chrome.sh

# 验证安装
google-chrome --version

# 测试爬虫
python3 scrapers/integrated_scraper.py --sources seek
```

### 选项2: 手动安装Chrome

```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<YOUR_EC2_IP>

# 下载Chrome RPM包
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# 安装Chrome
sudo dnf install -y ./google-chrome-stable_current_x86_64.rpm

# 或者使用yum（如果dnf不可用）
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm

# 安装依赖
sudo dnf install -y liberation-fonts vulkan xdg-utils

# 验证安装
google-chrome --version

# 清理安装包
rm google-chrome-stable_current_x86_64.rpm
```

### 选项3: 使用Chromium（轻量级替代）

如果EC2资源有限（t2.micro等），可以使用更轻量的Chromium：

```bash
# Amazon Linux 2023
sudo dnf install -y chromium

# 验证
chromium-browser --version
```

**注意**: 如果使用Chromium，需要修改爬虫代码中的Chrome路径。

## 验证修复

运行以下命令确认一切正常：

```bash
# 1. 检查Chrome
google-chrome --version

# 2. 检查Python依赖
python3 -c "import selenium; print('Selenium:', selenium.__version__)"

# 3. 测试爬虫（快速测试，不抓JD）
cd ~/scraper
python3 scrapers/integrated_scraper.py --sources seek

# 应该看到类似输出：
# ✅ SEEK: Found XX jobs
```

## 重启服务

Chrome安装完成后，重启服务：

```bash
cd ~/scraper

# 停止旧服务
./stop_services.sh

# 启动新服务
./start_services.sh

# 查看日志
tail -f app.log
```

## 排查其他问题

### 问题1: Chrome安装后仍然无法运行

**症状**: "chrome not reachable" 或 "session not created"

**原因**: EC2实例资源不足或缺少依赖

**解决方案**:
```bash
# 检查内存使用
free -h

# 如果内存不足（<1GB可用），考虑：
# 1. 升级EC2实例类型（推荐至少t3.small）
# 2. 添加swap空间
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

### 问题2: ChromeDriver版本不匹配

**症状**: "This version of ChromeDriver only supports Chrome version XX"

**解决方案**:
```bash
# Selenium 4.6+ 会自动管理ChromeDriver，确保Selenium是最新版
pip3 install --upgrade selenium --user

# 查看版本
python3 -c "import selenium; print(selenium.__version__)"
```

### 问题3: 权限问题

**症状**: "Permission denied" 或 "cannot execute binary file"

**解决方案**:
```bash
# 确保Chrome可执行
sudo chmod +x /usr/bin/google-chrome
sudo chmod +x /opt/google/chrome/chrome

# 检查SELinux（如果启用）
getenforce
# 如果是Enforcing，可以临时设置为Permissive测试
sudo setenforce 0
```

## 使用无头模式优化

我们的爬虫已经使用了无头模式，但如果遇到性能问题，可以进一步优化：

- ✅ 已启用: `--headless=new`
- ✅ 已禁用: 图片加载
- ✅ 已禁用: JavaScript（部分）
- ✅ 已启用: 最小化资源使用

如果仍然太慢，考虑：
1. 减少并发页面数
2. 增加请求延迟
3. 使用更大的EC2实例

## 预防措施

为了避免将来遇到同样的问题，已在GitHub Actions中添加了自动检查和安装Chrome的步骤。

下次推送代码时，GitHub Actions会：
1. 检查Chrome是否安装
2. 如果没有，自动运行 `install_chrome.sh`
3. 确保依赖都是最新的

## 需要帮助？

如果以上步骤都无法解决问题，请收集以下信息：

```bash
# 系统信息
cat /etc/os-release
uname -a

# Chrome信息
google-chrome --version
which google-chrome

# Python和依赖
python3 --version
pip3 list | grep selenium

# 内存和资源
free -h
df -h

# 错误日志
tail -50 ~/scraper/app.log
```

将这些信息发送给我，我会帮你诊断问题。

