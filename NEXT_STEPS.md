# 🚀 下一步操作指南

代码已经准备好了！现在需要完成以下配置步骤来启用自动部署。

## ✅ 已完成

- ✅ 创建GitHub Actions工作流 (`.github/workflows/deploy.yml`)
- ✅ 创建服务管理脚本 (`start_services.sh`, `stop_services.sh`)
- ✅ 更新文档和说明
- ✅ 本地Git提交

## 📝 待完成步骤

### 步骤1: 推送代码到GitHub

```bash
cd /Users/jin/scraper
git push origin main
```

**如果推送失败**，使用Personal Access Token：
1. 生成Token：https://github.com/settings/tokens/new
   - Note: `scraper-deployment`
   - Expiration: 90天或自定义
   - Scopes: 勾选 `repo` 和 `workflow`
2. 复制生成的token
3. 推送时输入：
   - Username: `flllexubleOuO`
   - Password: `粘贴你的token`

### 步骤2: 配置GitHub Secrets

1. **打开GitHub仓库页面**:
   ```
   https://github.com/flllexubleOuO/scraper
   ```

2. **进入Settings**:
   - 点击仓库顶部的 `Settings`
   - 左侧菜单选择 `Secrets and variables` → `Actions`
   - 点击 `New repository secret`

3. **添加以下3个Secrets**:

   **Secret #1: EC2_HOST**
   ```
   Name: EC2_HOST
   Value: 你的EC2公网IP地址 (例如: 54.123.45.67)
   ```
   在EC2控制台或运行：`curl http://169.254.169.254/latest/meta-data/public-ipv4`

   **Secret #2: EC2_USER**
   ```
   Name: EC2_USER
   Value: ec2-user
   ```
   (Amazon Linux使用 `ec2-user`，Ubuntu使用 `ubuntu`)

   **Secret #3: EC2_SSH_KEY**
   ```
   Name: EC2_SSH_KEY
   Value: 你的.pem私钥文件的完整内容
   ```
   
   **获取私钥内容**:
   ```bash
   # 在Mac上运行（替换成你的实际路径）
   cat /path/to/your-ec2-key.pem
   
   # 复制从 -----BEGIN RSA PRIVATE KEY----- 
   # 到 -----END RSA PRIVATE KEY----- 的所有内容
   ```

### 步骤3: 在EC2上准备环境

SSH连接到EC2并运行：

```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<YOUR_EC2_PUBLIC_IP>

# 如果仓库已存在，删除旧的
rm -rf ~/scraper

# 克隆仓库（如果是私有仓库，需要先设置为公开或使用token）
cd ~
git clone https://github.com/flllexubleOuO/scraper.git

# 进入目录
cd scraper

# 安装依赖
pip3 install -r requirements.txt --user

# 创建.env文件
nano .env
# 输入以下内容（替换成你的实际API key）:
# OPENAI_API_KEY=sk-xxxxxxxxxxxxx
# 保存：Ctrl+O, 回车, Ctrl+X

# 赋予脚本执行权限
chmod +x start_services.sh stop_services.sh

# 测试启动服务
./start_services.sh

# 检查服务是否运行
ps aux | grep python3

# 查看日志
tail -20 app.log
tail -20 scheduler.log
```

### 步骤4: 确保EC2安全组开放端口

在AWS控制台：
1. **EC2 Dashboard** → **Security Groups**
2. 找到你的实例的安全组
3. **Edit inbound rules** → **Add rule**:
   - Type: `Custom TCP`
   - Port: `8080`
   - Source: `0.0.0.0/0` (或你的IP)
   - Description: `Web scraper app`
4. **Save rules**

### 步骤5: 测试自动部署

1. **访问GitHub Actions页面**:
   ```
   https://github.com/flllexubleOuO/scraper/actions
   ```

2. **手动触发一次部署**:
   - 点击 `Deploy to EC2` workflow
   - 点击 `Run workflow` → `Run workflow`
   - 等待运行完成（约30秒）

3. **查看部署日志**:
   - 点击正在运行的workflow
   - 查看每个步骤的输出
   - 确认显示 "✅ Deployment completed successfully!"

4. **验证部署结果**:
   ```bash
   # SSH到EC2
   ssh -i your-key.pem ec2-user@<EC2_IP>
   
   # 检查进程
   ps aux | grep python3
   
   # 检查日志
   tail -f ~/scraper/app.log
   ```

5. **访问网站**:
   ```
   http://<YOUR_EC2_PUBLIC_IP>:8080
   ```

### 步骤6: 运行第一次爬虫

在EC2上：

```bash
cd ~/scraper

# 方案1: 快速抓取所有网站（不含JD，5分钟）
python scrapers/integrated_scraper.py --sources all

# 方案2: 深度抓取Seek（含所有JD，30-60分钟）
# 建议使用screen以便断开SSH后继续运行
screen -S scraper
python scrapers/integrated_scraper.py --sources seek --fetch-descriptions
# 按 Ctrl+A 然后 D 分离会话
# 重新连接: screen -r scraper

# 方案3: 只抓取前50个JD测试（10分钟）
python scrapers/integrated_scraper.py --sources seek --fetch-descriptions --max-descriptions 50
```

## 🎉 完成后的效果

1. **本地开发**: 修改代码 → `git push` → GitHub Actions自动部署到EC2
2. **自动更新**: 每天12点自动运行爬虫
3. **Web访问**: `http://<EC2_IP>:8080` 查看职位和数据分析
4. **AI助手**: 在网页上直接提问，ChatGPT实时分析数据

## 🔍 故障排查

### GitHub Actions失败

1. **检查Secrets配置**:
   - EC2_HOST 是否是公网IP
   - EC2_SSH_KEY 是否包含完整的私钥（包括头尾）
   - EC2安全组是否允许SSH (端口22)

2. **查看详细日志**:
   - GitHub Actions页面 → 点击失败的workflow → 查看每一步的输出

### EC2服务启动失败

```bash
# SSH到EC2
ssh -i your-key.pem ec2-user@<EC2_IP>

# 检查错误日志
cd ~/scraper
cat app.log
cat scheduler.log

# 手动启动测试
./stop_services.sh
./start_services.sh

# 检查Python依赖
python3 -c "import flask, selenium, openai; print('All imports OK')"

# 检查端口占用
lsof -i :8080
```

### 无法访问网站

1. **确认服务运行**: `ps aux | grep python3`
2. **确认端口监听**: `lsof -i :8080`
3. **确认安全组**: AWS控制台检查入站规则
4. **确认公网IP**: `curl http://169.254.169.254/latest/meta-data/public-ipv4`
5. **测试本地访问**: 在EC2上运行 `curl http://localhost:8080`

## 📚 相关文档

- [GitHub Actions详细配置](./GITHUB_ACTIONS_SETUP.md)
- [完整项目文档](./README.md)
- [AWS部署指南](./AWS_DEPLOY.md)

---

**祝部署顺利！🚀**

