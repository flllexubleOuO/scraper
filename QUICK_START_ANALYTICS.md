# 🚀 Analytics 快速开始指南

## 📋 前置步骤

### 1. 丰富数据（必须！）

在使用Analytics功能前，需要先提取技术栈数据：

```bash
cd /Users/jin/scraper

# 安装依赖
pip3 install pandas plotly tqdm

# 提取技术栈
python3 enrich_job_data.py
```

**预期输出**：
```
📚 Opening database: job_scraper.db
➕ Adding column: tech_stack
➕ Adding column: work_type
➕ Adding column: experience_level
📊 Found 527 jobs with descriptions to enrich
Enriching jobs: 100%|████████| 527/527 [00:15<00:00]
🎉 Successfully enriched 527 jobs!
```

### 2. 启动Web应用

```bash
python3 simple_app.py
```

### 3. 访问Analytics

打开浏览器访问：`http://localhost:8080`

点击顶部的 **"Analytics"** 标签即可查看：
- 💻 最受欢迎的编程语言
- ⚛️ 热门前端框架
- ⚙️ 后端框架趋势
- ☁️ 云平台使用率
- 🗄️ 数据库技术
- 🚀 DevOps工具
- 📈 90天职位趋势
- 🎓 经验等级分布
- 🏠 工作类型(远程/混合/现场)

## 🔄 更新数据

当有新的职位数据时：

```bash
# 1. 运行爬虫（自动每天12:00运行）
python3 scrapers/integrated_scraper.py --sources seek linkedin

# 2. 重新提取技术栈
python3 enrich_job_data.py

# 3. 刷新Analytics页面
# 点击页面上的"Refresh Analytics"按钮
```

## 📊 API 端点

如果想自定义可视化，可以直接调用API：

### 技术栈统计
```
GET http://localhost:8080/api/analytics/tech-stack
```

**返回示例**：
```json
{
  "programming_languages": [
    {"name": "Python", "count": 150},
    {"name": "JavaScript", "count": 120}
  ],
  "frontend": [
    {"name": "React", "count": 80}
  ]
}
```

### 职位趋势
```
GET http://localhost:8080/api/analytics/trends
```

### 经验等级
```
GET http://localhost:8080/api/analytics/experience-levels
```

### 工作类型
```
GET http://localhost:8080/api/analytics/work-types
```

## 💡 建议

1. **定期运行** `enrich_job_data.py`（建议每周一次）
2. **监控数据质量** - 检查技能提取准确率
3. **自定义关键词** - 编辑 `tech_stack_extractor.py` 添加新技术
4. **导出报告** - 使用 `visualization_dashboard.py` 生成HTML报告

## 🐛 故障排查

### 问题：Analytics页面显示"No data"

**解决**：
1. 确认已运行 `python3 enrich_job_data.py`
2. 检查数据库中是否有tech_stack数据：
   ```bash
   sqlite3 job_scraper.db "SELECT COUNT(*) FROM jobs WHERE tech_stack IS NOT NULL"
   ```
3. 如果返回0，重新运行数据丰富脚本

### 问题：某些技术没有被识别

**解决**：编辑 `tech_stack_extractor.py`，在相应类别中添加关键词：
```python
self.tech_keywords = {
    'programming_languages': {
        'Python', 'Java', 'YourNewLanguage'  # 添加这里
    }
}
```

## 📈 下一步

- [完整数据分析指南](docs/DATA_ANALYSIS_GUIDE.md)
- [技术栈提取器文档](tech_stack_extractor.py)
- [可视化仪表板生成](visualization_dashboard.py)

---

**Happy Analyzing! 🎉**

