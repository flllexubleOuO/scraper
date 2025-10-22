# 定时任务和今日新增功能说明

## ✅ 已完成功能

### 1. 定时任务系统 ⏰
- 每天12:00自动运行爬虫
- 后台守护进程
- 完整的日志记录

### 2. 今日新增标记 🆕
- 数据库添加`is_new_today`字段
- 每次运行爬虫时重置标记
- 新职位自动标记为今日新增
- Web界面显示"NEW"标签
- 新职位排在列表最前面

## 🚀 如何使用

### 方式1：启动定时任务（推荐）

```bash
cd /Users/jin/scraper

# 启动定时任务守护进程
python scheduler_daemon.py &

# 查看日志
tail -f scheduler.log
```

**特点：**
- 每天12:00自动运行
- 后台运行，不需要一直开着终端
- 日志保存在`scheduler.log`

### 方式2：测试运行（立即执行一次）

```bash
cd /Users/jin/scraper

# 测试模式：立即运行一次，然后继续定时
python scheduler_daemon.py --test
```

### 方式3：手动运行（一次性）

```bash
cd /Users/jin/scraper/scrapers

# 手动运行爬虫
python integrated_scraper.py --sources seek --fetch-descriptions --max-descriptions 50
```

## 📊 今日新增功能说明

### 工作原理

```
1. 每次爬虫运行前
   → 将所有职位的is_new_today重置为0
   
2. 爬虫运行中
   → 检查职位是否已存在
   → 如果是新职位 → 标记is_new_today = 1
   → 如果是旧职位 → is_new_today = 0
   
3. Web界面显示
   → SQL查询按is_new_today DESC排序
   → 新职位自动排在最前面
   → 显示"🆕 NEW"标签和特殊样式
```

### 视觉效果

**今日新增职位：**
```
┌─────────────────────────────────────────────┐
│ 🆕 NEW  Senior Python Developer            │  ← NEW标签
│ Tech Company Ltd                            │
├─────────────────────────────────────────────┤
│ 🌐 seek  📍 Auckland  💼 Developer         │
└─────────────────────────────────────────────┘
```

- 粉红色渐变背景
- 左侧粉色边框（4px）
- "🆕 NEW"标签（渐变粉红色，带动画）
- 自动排在列表最上方

**普通职位：**
- 白色背景
- 正常显示
- 无NEW标签

## 🔧 定时任务配置

### 修改运行时间

编辑`scheduler_daemon.py`第49行：

```python
# 当前：每天12:00
schedule.every().day.at("12:00").do(run_scraper)

# 修改为每天早上8:00
schedule.every().day.at("08:00").do(run_scraper)

# 修改为每天晚上22:00
schedule.every().day.at("22:00").do(run_scraper)
```

### 修改运行频率

```python
# 每12小时运行一次
schedule.every(12).hours.do(run_scraper)

# 每6小时运行一次
schedule.every(6).hours.do(run_scraper)

# 每周一运行
schedule.every().monday.at("12:00").do(run_scraper)
```

### 修改爬虫参数

编辑`scheduler_daemon.py`第30-36行：

```python
cmd = [
    sys.executable,
    'integrated_scraper.py',
    '--sources', 'seek', 'linkedin', 'indeed',  # 数据源
    '--fetch-descriptions',                      # 是否抓取JD
    '--max-descriptions', '50'                   # JD数量
]
```

## 📝 日志管理

### 查看实时日志

```bash
# 实时查看最新日志
tail -f /Users/jin/scraper/scheduler.log

# 查看最后100行
tail -100 /Users/jin/scraper/scheduler.log

# 搜索错误
grep ERROR /Users/jin/scraper/scheduler.log
```

### 日志内容

```
2025-10-23 12:00:00 - INFO - ============================================================
2025-10-23 12:00:00 - INFO - 🚀 Starting scheduled scraping job...
2025-10-23 12:00:00 - INFO - ============================================================
2025-10-23 12:00:01 - INFO - Executing: python integrated_scraper.py --sources seek
2025-10-23 12:03:45 - INFO - ✅ Scraping job completed successfully!
2025-10-23 12:03:45 - INFO - Next run scheduled at 12:00 tomorrow
```

## 🎯 使用场景

### 场景1：每日自动更新（推荐）

```bash
# 1. 启动定时任务
python scheduler_daemon.py &

# 2. 查看是否正常运行
ps aux | grep scheduler_daemon

# 3. 每天12:00自动运行
# 4. 访问网页查看今日新增职位
```

### 场景2：测试新功能

```bash
# 1. 测试运行
python scheduler_daemon.py --test

# 2. 访问网页
# http://localhost:8080

# 3. 查看今日新增职位（带NEW标签）
```

### 场景3：手动更新

```bash
# 有重要职位发布时，立即手动更新
cd /Users/jin/scraper/scrapers
python integrated_scraper.py --sources seek --fetch-descriptions --max-descriptions 10
```

## 🌟 NEW标签特性

### CSS动画效果

NEW标签有脉冲动画：
- 2秒循环
- 轻微缩放（1.0 → 1.05 → 1.0）
- 透明度变化（1.0 → 0.9 → 1.0）
- 吸引用户注意

### 响应式设计

- 桌面：标签正常大小
- 移动端：标签自适应缩小
- 始终清晰可见

## 📈 数据库Schema

```sql
CREATE TABLE jobs (
    ...
    is_new_today BOOLEAN DEFAULT 0,  -- 新增字段
    ...
);
```

**说明：**
- `is_new_today = 1` → 今日新增
- `is_new_today = 0` → 非今日新增
- 每次爬虫运行前自动重置

## 🔍 SQL查询示例

```sql
-- 查看今日新增职位
SELECT * FROM jobs WHERE is_new_today = 1;

-- 统计今日新增数量
SELECT COUNT(*) FROM jobs WHERE is_new_today = 1;

-- 按来源统计今日新增
SELECT source, COUNT(*) 
FROM jobs 
WHERE is_new_today = 1 
GROUP BY source;
```

## 🐛 故障排查

### 问题1：定时任务没运行

**检查：**
```bash
# 查看进程
ps aux | grep scheduler_daemon

# 查看日志
tail -50 /Users/jin/scraper/scheduler.log
```

**解决：**
```bash
# 重启定时任务
pkill -f scheduler_daemon
python /Users/jin/scraper/scheduler_daemon.py &
```

### 问题2：NEW标签不显示

**原因：** 数据库没有is_new_today字段

**解决：**
```bash
# 运行一次爬虫，会自动创建字段
cd /Users/jin/scraper/scrapers
python integrated_scraper.py --sources seek
```

### 问题3：所有职位都显示NEW

**原因：** is_new_today没有重置

**解决：**
- 正常情况下每次运行爬虫会自动重置
- 如果不正常，检查`integrated_scraper.py`第146行

## 📱 系统监控

### 检查定时任务状态

```bash
# 方式1：查看进程
ps aux | grep scheduler

# 方式2：查看日志最后一行
tail -1 /Users/jin/scraper/scheduler.log

# 方式3：查看下次运行时间
grep "Next run" /Users/jin/scraper/scheduler.log | tail -1
```

### 性能监控

```bash
# 查看数据库大小
ls -lh /Users/jin/scraper/job_scraper.db

# 统计总职位数
sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs"

# 统计今日新增
sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs WHERE is_new_today = 1"
```

## 🎉 完整工作流

### 初次设置

```bash
cd /Users/jin/scraper

# 1. 启动Web服务器
python simple_app.py &

# 2. 启动定时任务
python scheduler_daemon.py &

# 3. 测试运行（可选）
python scheduler_daemon.py --test &
```

### 日常使用

```bash
# 早上访问网页
http://localhost:8080

# 查看今日新增职位（自动排在最前，带NEW标签）
# 定时任务每天12:00自动更新
```

### 停止服务

```bash
# 停止Web服务器
lsof -ti:8080 | xargs kill

# 停止定时任务
pkill -f scheduler_daemon
```

## 💡 最佳实践

### 1. 日志管理

```bash
# 定期清理旧日志（保留最近1000行）
tail -1000 /Users/jin/scraper/scheduler.log > /tmp/scheduler.log
mv /tmp/scheduler.log /Users/jin/scraper/scheduler.log
```

### 2. 备份数据库

```bash
# 每周备份一次
cp /Users/jin/scraper/job_scraper.db /Users/jin/scraper/backups/job_scraper_$(date +%Y%m%d).db
```

### 3. 监控异常

```bash
# 检查错误日志
grep ERROR /Users/jin/scraper/scheduler.log

# 检查今日是否运行成功
grep "$(date +%Y-%m-%d)" /Users/jin/scraper/scheduler.log | grep "completed successfully"
```

## 🚀 总结

现在你有了完整的自动化系统：

✅ **定时自动运行** - 每天12:00自动抓取  
✅ **今日新增标记** - 新职位自动标记  
✅ **优先显示** - 新职位排在最前面  
✅ **视觉突出** - NEW标签和特殊样式  
✅ **后台运行** - 无需人工干预  
✅ **完整日志** - 方便监控和调试  

开始使用：
```bash
cd /Users/jin/scraper
python scheduler_daemon.py &
```

然后访问 http://localhost:8080 查看效果！🎉

