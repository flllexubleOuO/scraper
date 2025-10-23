# GitHub Actions 快速配置指南 ⚡

> 完整文档请查看: [docs/GITHUB_ACTIONS_COMPLETE_GUIDE.md](docs/GITHUB_ACTIONS_COMPLETE_GUIDE.md)

## 🎯 5分钟快速配置

### 步骤1: 添加GitHub Secrets (2分钟)

1. 打开 https://github.com/flllexubleOuO/scraper/settings/secrets/actions
2. 点击 **New repository secret**，添加以下3个secrets：

| Secret Name | Value | 如何获取 |
|-------------|-------|---------|
| `EC2_HOST` | 你的EC2公网IP | AWS控制台或运行`curl http://169.254.169.254/latest/meta-data/public-ipv4` |
| `EC2_USER` | `ec2-user` | Amazon Linux默认用户 |
| `EC2_SSH_KEY` | 完整的.pem文件内容 | `cat your-key.pem` 并复制全部内容 |

### 步骤2: 验证EC2安全组 (1分钟)

确保EC2安全组允许：
- ✅ **端口22 (SSH)** - 来源: 0.0.0.0/0
- ✅ **端口8080 (Web)** - 来源: 0.0.0.0/0

### 步骤3: 测试部署 (2分钟)

**方法A - 自动触发**:
```bash
git push origin main
```

**方法B - 手动触发**:
1. 进入 https://github.com/flllexubleOuO/scraper/actions
2. 选择 **Deploy to EC2** workflow
3. 点击 **Run workflow**

### 步骤4: 查看结果

1. 在 **Actions** 标签页查看运行状态
2. 部署成功后访问: `http://你的EC2_IP:8080`

## ✅ 成功标志

GitHub Actions日志应显示：
```
✅ Chrome already installed
✅ Web app is running
✅ Scheduler is running
✅ Deployment completed successfully!
```

## ❌ 常见错误

| 错误信息 | 解决方法 |
|---------|---------|
| `missing server host` | 未配置`EC2_HOST` secret |
| `Permission denied` | `EC2_SSH_KEY`格式错误，确保包含BEGIN/END行 |
| `Connection refused` | 安全组未开放22端口 |
| `git pull failed` | SSH到EC2运行`git reset --hard origin/main` |

## 🔍 调试命令

如果部署失败，SSH到EC2运行：
```bash
cd ~/scraper
tail -50 app.log           # 查看Web应用日志
tail -50 scheduler.log     # 查看调度器日志
ps aux | grep python3      # 查看运行进程
./scripts/maintenance/diagnose_ec2.sh  # 运行诊断脚本
```

## 📚 详细文档

- [完整配置指南](docs/GITHUB_ACTIONS_COMPLETE_GUIDE.md)
- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [EC2部署指南](docs/AWS_DEPLOY.md)

---

**配置完成后，每次push到main分支都会自动部署！** 🚀

