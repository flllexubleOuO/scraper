# 📂 项目结构说明

## 目录结构

```
scraper/
├── scrapers/              # 爬虫模块
│   ├── seek_scraper.py
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── trademe_scraper.py
│   └── integrated_scraper.py  # 统一调度器
│
├── scripts/               # 辅助脚本
│   ├── deployment/        # 部署相关
│   │   ├── deploy.sh
│   │   ├── deploy_lightweight.sh
│   │   └── install_chrome.sh
│   ├── maintenance/       # 维护和修复
│   │   ├── fix_database_columns.py
│   │   ├── fix_scheduler_ec2.sh
│   │   └── diagnose_ec2.sh
│   └── services/          # 服务管理
│       ├── start_services.sh
│       └── stop_services.sh
│
├── static/                # 前端静态文件
│   ├── app.js
│   └── style.css
│
├── templates/             # HTML模板
│   └── index.html
│
├── docs/                  # 文档
│   ├── AWS_DEPLOY.md
│   ├── GITHUB_ACTIONS_SETUP.md
│   ├── GITHUB_SECRETS_SETUP.md
│   └── PROJECT_STRUCTURE.md
│
├── .github/workflows/     # GitHub Actions
│   └── deploy.yml
│
├── simple_app.py          # Flask Web应用
├── scheduler_daemon.py    # 定时任务守护进程
├── ai_assistant.py        # ChatGPT集成
├── config.py              # 配置文件
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略文件
├── README.md             # 主文档
└── .env.example          # 环境变量示例

## 核心文件说明

### 应用层
- **simple_app.py** - Flask web应用，提供API和前端界面
- **scheduler_daemon.py** - 定时任务守护进程，每天12点自动运行爬虫
- **ai_assistant.py** - ChatGPT AI助手，提供智能数据分析

### 爬虫层
- **scrapers/integrated_scraper.py** - 主爬虫调度器，协调所有源
- **scrapers/*_scraper.py** - 各个招聘网站的具体爬虫实现

### 脚本层
- **scripts/deployment/** - 部署到EC2的自动化脚本
- **scripts/maintenance/** - 数据库维护和问题诊断工具
- **scripts/services/** - 服务启动/停止脚本

### 配置层
- **requirements.txt** - Python包依赖
- **.env** - 环境变量（包含API密钥，不提交到Git）
- **config.py** - 应用配置

## 数据流

```
1. Scheduler (scheduler_daemon.py)
   ↓ 每天12:00触发
2. Integrated Scraper (integrated_scraper.py)
   ↓ 调用各个源的爬虫
3. Individual Scrapers (seek_scraper.py等)
   ↓ 使用Selenium抓取数据
4. SQLite Database (job_scraper.db)
   ↓ 存储职位数据
5. Flask API (simple_app.py)
   ↓ 提供REST API
6. Web Frontend (templates/index.html + static/)
   ↓ 显示给用户
```

## 常用命令

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web应用
python simple_app.py

# 手动运行爬虫
python scrapers/integrated_scraper.py --sources seek

# 启动调度器
python scheduler_daemon.py
```

### EC2部署
```bash
# 启动所有服务
./scripts/services/start_services.sh

# 停止所有服务
./scripts/services/stop_services.sh

# 安装Chrome（首次部署）
./scripts/deployment/install_chrome.sh

# 诊断问题
./scripts/maintenance/diagnose_ec2.sh
```

## 维护指南

### 添加新的爬虫源
1. 在 `scrapers/` 创建新文件（例如：`newsite_scraper.py`）
2. 参考现有爬虫实现相同接口
3. 在 `integrated_scraper.py` 中注册新源
4. 更新 `scheduler_daemon.py` 的sources参数

### 修改定时任务
编辑 `scheduler_daemon.py` 第95行：
```python
schedule.every().day.at("12:00").do(run_scraper)
```

### 更新前端
- HTML: `templates/index.html`
- JavaScript: `static/app.js`
- CSS: `static/style.css`

## 部署流程

1. **本地开发** → 修改代码
2. **Git提交** → `git push origin main`
3. **GitHub Actions** → 自动部署到EC2
4. **EC2自动更新** → 拉取代码并重启服务

详见：[docs/GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)

