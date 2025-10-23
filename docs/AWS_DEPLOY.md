# AWS EC2 部署指南

## 📋 前置准备

### 1. AWS EC2实例要求

**推荐配置：**
- 实例类型: **t2.small** 或更高（至少2GB内存）
- 操作系统: **Ubuntu 22.04 LTS**
- 存储: 至少 **20GB**
- 安全组: 开放端口 **22** (SSH) 和 **8080** (Web)

**最低配置（适合测试）：**
- 实例类型: **t2.micro** (1GB内存)
- 操作系统: Ubuntu 22.04
- 存储: 10GB
- 注意: t2.micro运行Selenium可能较慢

### 2. 创建EC2实例

1. 登录AWS控制台
2. 进入EC2服务
3. 点击 "Launch Instance"
4. 选择 **Ubuntu Server 22.04 LTS**
5. 选择实例类型（推荐 t2.small）
6. 配置安全组：
   - SSH (22) - 你的IP
   - Custom TCP (8080) - 0.0.0.0/0（或你的IP）
7. 创建或选择密钥对（.pem文件）
8. 启动实例

### 3. 配置安全组

在EC2控制台 → 安全组 → 编辑入站规则：

```
类型          协议    端口范围    源
SSH           TCP     22         你的IP/32
Custom TCP    TCP     8080       0.0.0.0/0
```

## 🚀 部署步骤

### 方式1: 完整部署（推荐，适合t2.small及以上）

```bash
# 1. SSH连接到EC2
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. 下载部署脚本
wget https://raw.githubusercontent.com/flllexubleOuO/scraper/main/deploy.sh
chmod +x deploy.sh

# 3. 运行部署脚本
./deploy.sh

# 4. 配置环境变量
nano ~/scraper/.env
# 填入你的OPENAI_API_KEY

# 5. 重启服务
sudo systemctl restart scraper-web scraper-scheduler
```

### 方式2: 轻量级部署（适合t2.micro）

```bash
# 1. SSH连接
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. 下载轻量级部署脚本
wget https://raw.githubusercontent.com/flllexubleOuO/scraper/main/deploy_lightweight.sh
chmod +x deploy_lightweight.sh

# 3. 运行部署
./deploy_lightweight.sh

# 4. 配置API Key
cd ~/scraper
nano .env

# 5. 启动服务
./start.sh
```

### 方式3: 手动部署

```bash
# 1. 连接到EC2
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. 更新系统
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git

# 3. 克隆项目
cd ~
git clone https://github.com/flllexubleOuO/scraper.git
cd scraper

# 4. 安装依赖
pip3 install -r requirements.txt

# 5. 配置环境变量
echo 'export OPENAI_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc

# 6. 启动服务
nohup python3 simple_app.py > app.log 2>&1 &
nohup python3 scheduler_daemon.py > scheduler.log 2>&1 &
```

## 🔧 配置说明

### 环境变量配置

编辑 `~/scraper/.env`：

```bash
# OpenAI API Key（必需）
OPENAI_API_KEY=sk-your-actual-key-here

# 数据库路径
DATABASE_PATH=job_scraper.db

# Flask配置
FLASK_SECRET_KEY=随机字符串
FLASK_PORT=8080
```

### Selenium配置（可选）

如果不需要Chrome/Selenium（仅使用requests）：

编辑 `requirements.txt`，注释掉：
```
# selenium
```

## 📊 服务管理

### 使用systemd（完整部署）

```bash
# 查看服务状态
sudo systemctl status scraper-web
sudo systemctl status scraper-scheduler

# 启动服务
sudo systemctl start scraper-web
sudo systemctl start scraper-scheduler

# 停止服务
sudo systemctl stop scraper-web
sudo systemctl stop scraper-scheduler

# 重启服务
sudo systemctl restart scraper-web
sudo systemctl restart scraper-scheduler

# 查看日志
sudo journalctl -u scraper-web -f
sudo journalctl -u scraper-scheduler -f
```

### 使用脚本（轻量级部署）

```bash
# 启动
cd ~/scraper
./start.sh

# 停止
./stop.sh

# 查看日志
tail -f app.log
tail -f scheduler.log

# 查看进程
ps aux | grep python
```

## 🌐 访问应用

部署完成后，访问：

```
http://your-ec2-public-ip:8080
```

获取EC2公网IP：
```bash
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

## 🔍 故障排查

### 1. 无法访问Web界面

**检查服务状态：**
```bash
sudo systemctl status scraper-web
# 或
ps aux | grep simple_app
```

**检查端口：**
```bash
sudo netstat -tlnp | grep 8080
```

**检查日志：**
```bash
tail -50 ~/scraper/app.log
```

### 2. 安全组配置

确保8080端口已开放：
- AWS控制台 → EC2 → 安全组
- 入站规则中添加 8080 端口

### 3. 内存不足（t2.micro）

如果遇到内存问题，创建swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. Chrome/Selenium问题

如果Selenium失败，可以禁用需要浏览器的爬虫：

编辑 `~/scraper/scrapers/integrated_scraper.py`，只使用不需要Selenium的源。

## 📈 性能优化

### 1. 减少资源占用

```bash
# 只运行必要的服务
sudo systemctl disable scraper-scheduler  # 不需要定时任务时

# 减少爬取频率
# 编辑 scheduler_daemon.py，改为每天运行一次
```

### 2. 使用RDS数据库（可选）

如果数据量大，可以使用AWS RDS：
- 创建RDS实例（PostgreSQL）
- 更新数据库连接配置
- 修改代码使用PostgreSQL

### 3. 使用Nginx反向代理（推荐）

```bash
# 安装Nginx
sudo apt-get install -y nginx

# 配置反向代理
sudo nano /etc/nginx/sites-available/scraper

# 添加配置
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 安全建议

### 1. 更新系统

```bash
# 定期更新
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. 配置防火墙

```bash
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw enable
```

### 3. 使用环境变量

不要在代码中硬编码敏感信息，使用环境变量或.env文件。

### 4. 限制SSH访问

在安全组中，只允许你的IP访问SSH (22端口)。

## 💰 成本估算

### EC2实例成本（按需定价，美国东部）

- **t2.micro**: ~$0.0116/小时 (~$8.5/月)
- **t2.small**: ~$0.023/小时 (~$17/月)
- **t2.medium**: ~$0.046/小时 (~$34/月)

### 其他成本

- EBS存储: ~$0.10/GB/月
- 数据传输: 出站流量 $0.09/GB（前1GB免费）
- OpenAI API: 使用量计费

### 节省成本

- 使用预留实例（节省40-60%）
- 使用Savings Plans
- 不用时停止实例

## 📝 维护建议

### 每日检查

```bash
# 检查服务状态
sudo systemctl status scraper-web scraper-scheduler

# 检查磁盘空间
df -h

# 检查日志文件大小
du -sh ~/scraper/*.log
```

### 每周任务

```bash
# 更新代码
cd ~/scraper
git pull
sudo systemctl restart scraper-web scraper-scheduler

# 清理日志
> app.log
> scheduler.log
```

### 备份数据库

```bash
# 定期备份
cp ~/scraper/job_scraper.db ~/backups/job_scraper_$(date +%Y%m%d).db

# 或上传到S3
aws s3 cp ~/scraper/job_scraper.db s3://your-bucket/backups/
```

## 🎉 部署清单

部署前确认：

- [ ] EC2实例已创建并运行
- [ ] 安全组已配置（22, 8080端口）
- [ ] 密钥对已下载（.pem文件）
- [ ] OpenAI API Key已准备
- [ ] GitHub仓库已更新

部署后验证：

- [ ] 可以SSH连接到EC2
- [ ] Web界面可以访问
- [ ] AI助手正常工作
- [ ] 定时任务已启动
- [ ] 数据库正常读写

---

**完成部署后访问：** `http://your-ec2-ip:8080` 🚀

