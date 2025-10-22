# 🇳🇿 NZ IT Job Market Analyzer

新西兰IT就业市场分析系统 - 自动抓取、智能分析、AI助手

## ✨ 功能特性

- 🕷️ **多源爬虫** - Seek, LinkedIn, Indeed, TradeMe
- 📄 **JD抓取** - 完整职位描述存储
- 🤖 **ChatGPT AI** - 智能数据分析问答
- 🌐 **Web界面** - 现代化单页应用
- ⏰ **定时任务** - 每天自动更新
- 🆕 **今日新增** - 自动标记新职位
- 🚀 **自动部署** - GitHub Actions自动部署到EC2

## 🚀 快速开始

### 0. 配置环境变量（首次使用）
```bash
# 设置OpenAI API Key（如果要使用AI功能）
export OPENAI_API_KEY='your_api_key_here'

# 或者在~/.bashrc或~/.zshrc中添加：
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.zshrc
```

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动Web界面
```bash
cd /Users/jin/scraper
python simple_app.py &
```
访问：http://localhost:8080

### 2. 运行爬虫
```bash
cd /Users/jin/scraper/scrapers

# 快速抓取（3分钟）
python integrated_scraper.py --sources seek

# 深度抓取含JD（8分钟）
python integrated_scraper.py --sources seek --fetch-descriptions --max-descriptions 50
```

### 3. 启动定时任务
```bash
cd /Users/jin/scraper
python scheduler_daemon.py &  # 每天12:00自动运行
```

## 📊 主要功能

### 职位浏览
- 查看所有IT职位列表
- 🆕 NEW标签显示今日新增
- 点击"📄 View JD"查看完整描述
- 搜索、过滤、分页

### AI智能助手
在Web界面下方提问，例如：
- "有多少Python相关的职位？"
- "最热门的技术栈是什么？"
- "成为全栈开发者应该学什么？"

AI会实时查询数据库并给出回答！

### 数据分析
```bash
# 分析技术趋势
python analyze_tech_trends.py
```

## ⚙️ 配置说明

### 修改定时任务时间
编辑 `scheduler_daemon.py` 第49行：
```python
schedule.every().day.at("12:00").do(run_scraper)  # 改为你想要的时间
```

### 修改爬虫参数
编辑 `scrapers/integrated_scraper.py` 或使用命令行参数：
```bash
--sources seek linkedin      # 数据源
--fetch-descriptions         # 是否抓取JD
--max-descriptions 50        # JD数量
```

## 📁 项目结构

```
/Users/jin/scraper/
├── simple_app.py              # Web应用
├── ai_assistant.py            # AI助手
├── scheduler_daemon.py        # 定时任务
├── analyze_tech_trends.py     # 数据分析
├── job_scraper.db            # SQLite数据库
├── scrapers/                 # 爬虫模块
│   ├── integrated_scraper.py # 主爬虫
│   ├── seek_scraper.py       # Seek爬虫
│   ├── linkedin_scraper.py   # LinkedIn爬虫
│   ├── indeed_scraper.py     # Indeed爬虫
│   └── trademe_scraper.py    # TradeMe爬虫
├── templates/                # HTML模板
└── static/                   # CSS/JS资源
```

## 🎯 常用命令

```bash
# 启动所有服务
python simple_app.py &
python scheduler_daemon.py &

# 查看日志
tail -f scheduler.log
tail -f app.log

# 查看数据库
sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs"
sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs WHERE is_new_today = 1"

# 停止服务
lsof -ti:8080 | xargs kill
pkill -f scheduler_daemon
```

## 💡 使用建议

**日常使用：**
1. 启动定时任务（后台自动运行）
2. 每天访问Web界面查看新职位
3. 使用AI助手分析市场趋势

**定时任务：**
- 每日12:00自动抓取
- 新职位自动标记并排在前面
- 日志记录在 `scheduler.log`

**AI助手：**
- 实时查询数据库
- 分析技术趋势
- 职业建议

## 🔧 故障排查

### Web界面打不开
```bash
# 检查进程
ps aux | grep simple_app

# 重启
lsof -ti:8080 | xargs kill
python simple_app.py &
```

### 定时任务没运行
```bash
# 查看日志
tail -50 scheduler.log

# 重启
pkill -f scheduler_daemon
python scheduler_daemon.py &
```

### AI不工作
确保OpenAI库已安装：
```bash
pip install openai
```

## 📈 数据库Schema

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    description TEXT,              -- 职位描述
    source TEXT DEFAULT 'seek',    -- 数据源
    is_new_today BOOLEAN,          -- 今日新增标记
    is_active BOOLEAN,
    created_at TIMESTAMP,
    ...
);
```

## 🚀 自动部署到EC2 (GitHub Actions)

本项目支持通过GitHub Actions自动部署到AWS EC2。

### 配置步骤

1. **添加GitHub Secrets**  
   在GitHub仓库的 `Settings` → `Secrets and variables` → `Actions` 中添加：
   - `EC2_HOST`: EC2公网IP
   - `EC2_USER`: EC2用户名（例如：`ec2-user`）
   - `EC2_SSH_KEY`: SSH私钥内容（.pem文件的完整内容）

2. **在EC2上配置环境**  
   ```bash
   # SSH到EC2
   ssh -i your-key.pem ec2-user@<EC2_IP>
   
   # 克隆仓库
   cd ~
   git clone https://github.com/your-username/scraper.git
   cd scraper
   
   # 安装依赖
   pip3 install -r requirements.txt --user
   
   # 创建环境变量文件
   cat > .env << 'EOF'
   OPENAI_API_KEY=your_openai_api_key_here
   EOF
   
   # 赋予脚本执行权限
   chmod +x start_services.sh stop_services.sh
   
   # 启动服务
   ./start_services.sh
   ```

3. **推送代码自动部署**  
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   # GitHub Actions会自动部署到EC2
   ```

4. **手动触发部署**  
   在GitHub仓库页面：`Actions` → `Deploy to EC2` → `Run workflow`

### 服务管理脚本

```bash
# 启动所有服务
./start_services.sh

# 停止所有服务
./stop_services.sh

# 查看服务状态
ps aux | grep python3

# 查看日志
tail -f app.log          # Web应用日志
tail -f scheduler.log    # 调度器日志
```

详细配置说明请查看：[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)

## 🎉 核心价值

✅ 全面了解NZ IT市场  
✅ 数据驱动职业决策  
✅ AI辅助智能分析  
✅ 自动化数据收集  
✅ 可视化趋势展示  
✅ 一键部署到云端  

---

**本地访问：** http://localhost:8080  
**EC2访问：** http://\<YOUR_EC2_IP\>:8080 🚀
