# GitHub Actions 自动部署设置指南

本指南帮助你配置GitHub Actions，实现代码自动部署到AWS EC2。

## 📋 前提条件

1. ✅ 代码已推送到GitHub
2. ✅ EC2实例正在运行
3. ✅ 你有EC2的SSH密钥文件（.pem）

## 🔧 配置步骤

### 1. 添加GitHub Secrets

在你的GitHub仓库中添加以下secrets：

1. 进入GitHub仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加以下三个secrets：

#### Secret 1: `EC2_HOST`
- **Name**: `EC2_HOST`
- **Value**: 你的EC2公网IP地址
  ```
  例如: 54.123.45.67
  ```

#### Secret 2: `EC2_USER`
- **Name**: `EC2_USER`
- **Value**: EC2用户名
  ```
  对于Amazon Linux 2023: ec2-user
  对于Ubuntu: ubuntu
  ```

#### Secret 3: `EC2_SSH_KEY`
- **Name**: `EC2_SSH_KEY`
- **Value**: 你的.pem私钥文件的完整内容
  
  **如何获取**:
  ```bash
  # 在Mac上运行
  cat /path/to/your-key.pem
  ```
  
  然后复制**完整内容**（包括 `-----BEGIN RSA PRIVATE KEY-----` 和 `-----END RSA PRIVATE KEY-----`）

### 2. 在EC2上配置环境变量

确保EC2上有环境变量文件：

```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<EC2_IP>

# 创建环境变量文件
cd ~/scraper
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
EOF

# 修改启动脚本以加载环境变量
```

### 3. 修改服务启动方式

为了让GitHub Actions能正确重启服务并加载环境变量，需要创建启动脚本：

```bash
# 在EC2上创建启动脚本
cd ~/scraper
cat > start_services.sh << 'EOF'
#!/bin/bash
cd ~/scraper

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 停止旧进程
pkill -f simple_app.py || true
pkill -f scheduler_daemon.py || true
sleep 2

# 启动新进程
nohup python3 simple_app.py > app.log 2>&1 &
nohup python3 scheduler_daemon.py > scheduler.log 2>&1 &

echo "Services started"
EOF

chmod +x start_services.sh
```

### 4. 更新GitHub Actions配置

修改 `.github/workflows/deploy.yml` 来使用启动脚本（如果需要）。

### 5. 测试自动部署

1. **推送代码到GitHub**:
   ```bash
   git add .
   git commit -m "Test auto-deployment"
   git push origin main
   ```

2. **查看部署进度**:
   - 进入GitHub仓库
   - 点击 **Actions** 标签
   - 查看最新的workflow运行状态

3. **手动触发部署**:
   - 进入 **Actions** → **Deploy to EC2**
   - 点击 **Run workflow** → **Run workflow**

## ✅ 验证部署成功

部署完成后：

1. **检查GitHub Actions日志**:
   - 应该显示绿色的勾 ✅
   - 日志中显示 "Deployment completed successfully!"

2. **访问网站**:
   ```
   http://<YOUR_EC2_IP>:8080
   ```

3. **SSH到EC2检查**:
   ```bash
   ssh -i your-key.pem ec2-user@<EC2_IP>
   cd ~/scraper
   
   # 查看进程
   ps aux | grep python3
   
   # 查看日志
   tail -f app.log
   tail -f scheduler.log
   ```

## 🔍 故障排查

### 问题1: GitHub Actions失败 "Permission denied"

**原因**: SSH密钥配置不正确

**解决**:
1. 确认 `EC2_SSH_KEY` secret包含完整的私钥内容
2. 确认私钥格式正确（包括开头和结尾的标记行）
3. 确认EC2安全组允许GitHub Actions的IP访问（建议开放0.0.0.0/0的22端口）

### 问题2: 服务重启失败

**原因**: 环境变量未加载或端口占用

**解决**:
```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<EC2_IP>

# 手动停止所有进程
pkill -f python3

# 检查端口占用
lsof -i :8080

# 手动启动
cd ~/scraper
./start_services.sh
```

### 问题3: "git pull" 失败

**原因**: EC2上的仓库状态有冲突

**解决**:
```bash
# SSH到EC2
cd ~/scraper

# 重置本地更改
git reset --hard HEAD
git clean -fd

# 重新拉取
git pull origin main
```

## 📝 工作流说明

GitHub Actions会在以下情况自动运行：

1. **代码推送到main分支**: 自动触发部署
2. **手动触发**: 在GitHub Actions页面手动运行

部署流程：
1. 拉取最新代码
2. 检查依赖是否变化
3. 如果依赖变化，更新Python包
4. 停止旧服务
5. 启动新服务
6. 验证服务运行状态

## 🎯 最佳实践

1. **先在本地测试**: 确保代码在本地运行正常
2. **查看日志**: 部署后检查EC2上的app.log和scheduler.log
3. **版本标签**: 使用git tag标记重要版本
4. **回滚策略**: 保留上一个可用版本的备份

## 🔒 安全建议

1. **最小权限原则**: 
   - 只开放必要的EC2端口（22, 8080）
   - 考虑使用EC2的IAM角色而不是直接使用SSH密钥

2. **密钥管理**:
   - 定期轮换SSH密钥
   - 定期轮换OpenAI API密钥

3. **监控**:
   - 设置CloudWatch监控EC2资源使用
   - 配置日志告警

## 📚 相关资源

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [SSH Action文档](https://github.com/appleboy/ssh-action)
- [AWS EC2安全最佳实践](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security.html)

