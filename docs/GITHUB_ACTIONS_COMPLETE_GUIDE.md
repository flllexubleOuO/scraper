# GitHub Actions 完整配置指南

## 📋 概述

本项目使用GitHub Actions实现自动部署到AWS EC2。每次推送代码到`main`分支时，会自动：
1. 连接到EC2实例
2. 拉取最新代码
3. 安装/更新依赖
4. 重启服务

## 🔐 第一步：配置GitHub Secrets

### 1. 进入仓库设置

1. 打开你的GitHub仓库: https://github.com/flllexubleOuO/scraper
2. 点击 **Settings** 标签
3. 在左侧菜单找到 **Secrets and variables** > **Actions**
4. 点击 **New repository secret** 按钮

### 2. 添加必需的Secrets

#### Secret 1: EC2_HOST
- **Name**: `EC2_HOST`
- **Value**: 你的EC2公网IP地址（例如：`13.239.123.45`）
- 💡 **如何获取**：
  ```bash
  # 在EC2上运行
  curl http://169.254.169.254/latest/meta-data/public-ipv4
  ```
  或在AWS控制台 > EC2 > 实例详情中查看

#### Secret 2: EC2_USER
- **Name**: `EC2_USER`
- **Value**: `ec2-user`
- 💡 Amazon Linux默认用户名是`ec2-user`，Ubuntu是`ubuntu`

#### Secret 3: EC2_SSH_KEY
- **Name**: `EC2_SSH_KEY`
- **Value**: 你的SSH私钥完整内容
- 💡 **如何获取**：
  ```bash
  # 在Mac上运行（假设你的密钥文件是 my-key.pem）
  cat ~/Downloads/my-key.pem
  ```
  复制**全部内容**，包括：
  ```
  -----BEGIN RSA PRIVATE KEY-----
  MIIEpAIBAAKCAQEA...
  ... (中间很多行)
  ...
  -----END RSA PRIVATE KEY-----
  ```

#### Secret 4: OPENAI_API_KEY (可选)
- **Name**: `OPENAI_API_KEY`
- **Value**: 你的OpenAI API密钥（如果使用AI功能）

## ✅ 第二步：验证EC2配置

### 1. 确保EC2安全组配置正确

在AWS控制台：
1. 进入 **EC2** > **安全组**
2. 找到你的实例使用的安全组
3. 确保**入站规则**包含：
   - **SSH (22)**: 来源 = GitHub Actions IP范围或 0.0.0.0/0
   - **HTTP (8080)**: 来源 = 0.0.0.0/0（或你的IP）

### 2. 确保EC2上的项目已初始化

SSH到EC2，运行：
```bash
cd ~/scraper
git status
# 应该显示：On branch main

ls -la
# 应该看到 simple_app.py, scheduler_daemon.py 等文件
```

如果项目不存在，克隆它：
```bash
cd ~
git clone https://github.com/flllexubleOuO/scraper.git
cd scraper
pip3 install -r requirements.txt --user
```

### 3. 配置.env文件（如果使用AI功能）

```bash
cd ~/scraper
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key-here
EOF
```

## 🚀 第三步：测试部署

### 方法1：推送代码触发（自动）

```bash
# 在本地Mac上
cd /Users/jin/scraper
git add .
git commit -m "Test GitHub Actions deployment"
git push origin main
```

### 方法2：手动触发

1. 进入GitHub仓库
2. 点击 **Actions** 标签
3. 在左侧选择 **Deploy to EC2** 工作流
4. 点击右上角 **Run workflow** 按钮
5. 选择 `main` 分支
6. 点击绿色的 **Run workflow** 按钮

## 📊 第四步：查看部署日志

1. 在 **Actions** 标签页
2. 点击最新的工作流运行
3. 点击 **deploy** 作业
4. 查看每个步骤的详细日志

### 成功的日志示例：
```
🚀 Starting deployment...
📥 Pulling latest code from GitHub...
Already up to date.
✅ Chrome already installed: Google Chrome 141.0.7390.122
🔄 Restarting services...
✅ Web app is running
✅ Scheduler is running
✅ Deployment completed successfully!
```

## 🐛 常见问题排查

### 问题1: "Error: missing server host"
**原因**: 未配置`EC2_HOST` secret  
**解决**: 按照上面步骤添加secret

### 问题2: "Permission denied (publickey)"
**原因**: SSH密钥配置错误  
**解决**:
- 检查`EC2_SSH_KEY` secret是否包含完整的密钥内容
- 确保包含BEGIN和END行
- 密钥格式应该是RSA或ED25519

### 问题3: "git pull failed"
**原因**: EC2上有未提交的本地更改  
**解决**:
```bash
# SSH到EC2
cd ~/scraper
git status
# 如果有改动，重置它们
git reset --hard origin/main
git pull origin main
```

### 问题4: "Web app failed to start"
**原因**: 依赖缺失或代码错误  
**解决**:
```bash
# SSH到EC2查看日志
cd ~/scraper
tail -50 app.log
tail -50 scheduler.log

# 重新安装依赖
pip3 install -r requirements.txt --user --upgrade
```

### 问题5: "Chrome not found"
**原因**: Chrome未安装  
**解决**: 工作流会自动安装，如果失败手动运行：
```bash
cd ~/scraper
chmod +x scripts/deployment/install_chrome.sh
./scripts/deployment/install_chrome.sh
```

## 🔄 工作流配置详解

### 触发条件
```yaml
on:
  push:
    branches:
      - main          # 推送到main分支时自动触发
  workflow_dispatch:  # 允许手动触发
```

### 关键步骤

1. **拉取代码**: `git pull origin main`
2. **安装Chrome**: 仅在未安装时执行
3. **更新依赖**: 仅在`requirements.txt`变化时执行
4. **重启服务**: 使用服务脚本优雅重启

### 服务管理

工作流优先使用服务脚本：
- `scripts/services/stop_services.sh` - 停止服务
- `scripts/services/start_services.sh` - 启动服务

如果脚本不存在，会回退到手动进程管理。

## 📈 监控和维护

### 查看服务状态

```bash
# SSH到EC2
cd ~/scraper

# 查看运行进程
ps aux | grep python3

# 查看实时日志
tail -f app.log
tail -f scheduler.log

# 查看爬虫历史
sqlite3 job_scraper.db "SELECT COUNT(*), source FROM jobs GROUP BY source"
```

### 手动重启服务

```bash
cd ~/scraper
./scripts/services/stop_services.sh
./scripts/services/start_services.sh
```

### 手动运行爬虫

```bash
cd ~/scraper
python3 scrapers/integrated_scraper.py --sources seek linkedin indeed
```

## 🎯 最佳实践

1. **小改动频繁提交**: 每次提交会触发部署，小改动更容易回滚
2. **查看日志**: 每次部署后检查GitHub Actions日志
3. **监控资源**: t2.micro实例资源有限，定期检查内存和CPU使用
4. **备份数据库**: 定期备份`job_scraper.db`
5. **更新依赖**: 定期更新Python包和Chrome版本

## 📞 需要帮助？

如果遇到问题：
1. 查看GitHub Actions日志
2. 查看EC2上的`app.log`和`scheduler.log`
3. 运行诊断脚本：`scripts/maintenance/diagnose_ec2.sh`
4. 检查项目结构文档：`docs/PROJECT_STRUCTURE.md`

---

**配置完成后，你的部署流程应该完全自动化！** 🎉

每次推送代码 → GitHub Actions自动部署 → EC2服务自动更新 → 网站立即生效

