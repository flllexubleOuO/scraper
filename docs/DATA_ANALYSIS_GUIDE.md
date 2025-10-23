# 📊 数据分析与可视化指南

## 概述

本项目包含完整的新西兰IT职位市场数据收集和分析工具链，可以长期追踪行业趋势。

## 🎯 数据收集维度

### 已实现的数据字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `title` | 职位标题 | "Senior Python Developer" |
| `company` | 公司名称 | "Xero" |
| `location` | 工作地点 | "Auckland" |
| `salary_range` | 薪资范围 | "$80k-$120k" |
| `category` | 职位类别 | "Software Developer (Backend)" |
| `description` | 职位描述 | 完整JD文本 |
| `source` | 数据来源 | "seek", "linkedin" |
| `tech_stack` | 技术栈（JSON） | {"programming_languages": ["Python", "Java"]} |
| `work_type` | 工作类型 | ["remote", "hybrid"] |
| `experience_level` | 经验等级 | "senior" |
| `benefits` | 福利列表 | ["visa_support", "flexible hours"] |
| `skills_count` | 技能总数 | 8 |
| `first_seen_date` | 首次发现日期 | "2025-01-15" |
| `last_seen_date` | 最后活跃日期 | "2025-01-20" |
| `is_active` | 是否活跃 | true/false |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/jin/scraper
pip3 install -r requirements.txt
```

### 2. 丰富现有数据（提取技术栈）

```bash
# 为所有现有职位提取技术栈信息
python3 enrich_job_data.py

# 指定数据库路径
python3 enrich_job_data.py --db job_scraper.db
```

**输出示例**：
```
📚 Opening database: job_scraper.db
➕ Adding column: tech_stack
➕ Adding column: work_type
📊 Found 527 jobs with descriptions to enrich
Enriching jobs: 100%|██████████| 527/527 [00:15<00:00, 34.12it/s]
🎉 Successfully enriched 527 jobs!

📊 === 数据统计报告 ===
经验等级分布:
  mid: 350
  senior: 120
  junior: 57

技能统计:
  平均: 6.3
  最少: 1
  最多: 18
```

### 3. 生成可视化仪表板

```bash
# 生成HTML仪表板
python3 visualization_dashboard.py

# 指定输出文件
python3 visualization_dashboard.py --output my_dashboard.html
```

**输出**：
- 生成 `dashboard.html` 文件
- 在浏览器中打开即可查看交互式图表

### 4. 测试技术栈提取器

```bash
python3 tech_stack_extractor.py
```

## 📈 可视化仪表板内容

生成的仪表板包含以下图表：

1. **📈 职位数量趋势** - 时间序列图，显示每日新增职位
2. **💼 职位类别分布** - 饼图，显示不同职位类型占比
3. **📍 地域分布** - 柱状图，Top 10城市
4. **💻 技术栈需求热度** - 多子图，显示各类技术的需求
   - 编程语言
   - 前端框架
   - 后端框架
   - 云平台
   - 数据库
5. **🎓 经验等级分布** - 柱状图
6. **🏢 最活跃招聘公司** - 横向柱状图，Top 15

## 🔍 技术栈提取器功能

`TechStackExtractor` 可以从JD中自动提取：

### 支持的技术类别

- **编程语言**: Python, Java, JavaScript, TypeScript, C#, Go, Rust等
- **前端框架**: React, Vue, Angular, Next.js等
- **后端框架**: Django, Flask, Spring Boot, .NET等
- **数据库**: PostgreSQL, MySQL, MongoDB, Redis等
- **云平台**: AWS, Azure, GCP
- **DevOps工具**: Docker, Kubernetes, Jenkins, Terraform等
- **数据工具**: Spark, Airflow, Tableau, Power BI等
- **版本控制**: Git, GitHub, GitLab
- **方法论**: Agile, Scrum, Microservices, REST API等

### 工作类型识别

- Remote (远程)
- Hybrid (混合)
- Onsite (现场)

### 经验等级识别

- Junior (初级)
- Mid (中级)
- Senior (高级)
- Expert (专家/架构师)

## 📊 数据分析示例

### Python分析脚本示例

```python
import sqlite3
import pandas as pd
import json

# 连接数据库
conn = sqlite3.connect('job_scraper.db')

# 1. 加载数据
df = pd.read_sql_query("""
    SELECT * FROM jobs 
    WHERE tech_stack IS NOT NULL
""", conn)

# 2. 解析技术栈
df['tech_stack_parsed'] = df['tech_stack'].apply(json.loads)

# 3. 统计最受欢迎的编程语言
from collections import Counter
all_languages = Counter()
for tech_dict in df['tech_stack_parsed']:
    if 'programming_languages' in tech_dict:
        all_languages.update(tech_dict['programming_languages'])

print("Top 10 编程语言:")
for lang, count in all_languages.most_common(10):
    print(f"  {lang}: {count}")

# 4. 按地域分析薪资
location_salary = df.groupby('location')['salary_range'].value_counts()
print("\n各地区薪资分布:")
print(location_salary.head(20))

# 5. 经验等级 vs 技能数量
exp_skills = df.groupby('experience_level')['skills_count'].agg(['mean', 'median'])
print("\n经验等级 vs 平均技能要求:")
print(exp_skills)

conn.close()
```

## 🔮 未来数据分析方向

### 短期（1-3个月）

1. **技能组合分析**: 哪些技能常一起出现？
2. **薪资预测模型**: 基于技能和经验预测薪资
3. **公司画像**: 各公司的技术栈偏好
4. **地域趋势**: Auckland vs Wellington的职位特点

### 中期（3-6个月）

1. **趋势预测**: 使用时间序列预测未来职位需求
2. **职位生命周期分析**: 哪类职位最快被填补？
3. **技能价值评估**: 稀缺技能 + 高薪资组合
4. **竞争度指数**: 职位供需比分析

### 长期（6-12个月）

1. **行业报告生成**: 自动生成季度/年度IT市场报告
2. **求职者匹配系统**: 基于技能匹配推荐职位
3. **薪资谈判助手**: 提供数据支持的薪资建议
4. **技能发展路径**: 基于市场需求推荐学习路线

## 🛠️ 自定义扩展

### 添加新的技术关键词

编辑 `tech_stack_extractor.py`：

```python
self.tech_keywords = {
    # ... 现有类别
    'new_category': {
        'Keyword1', 'Keyword2', 'Keyword3'
    }
}
```

### 添加新的可视化图表

编辑 `visualization_dashboard.py`，添加新方法：

```python
def create_custom_chart(self, df):
    # 你的图表逻辑
    fig = go.Figure(...)
    return fig
```

## 📝 数据更新频率

- **爬虫运行**: 每天12:00自动运行
- **数据丰富**: 需要手动运行`enrich_job_data.py`（建议每周一次）
- **仪表板更新**: 可随时生成最新版本

## 🤝 集成到Web界面

可以将可视化集成到现有Flask应用：

```python
# 在 simple_app.py 中添加
@app.route('/dashboard')
def dashboard():
    from visualization_dashboard import JobMarketDashboard
    dashboard = JobMarketDashboard()
    charts_html = dashboard.generate_charts_html()
    return render_template('dashboard.html', charts=charts_html)
```

## 📚 相关资源

- [Plotly文档](https://plotly.com/python/)
- [Pandas教程](https://pandas.pydata.org/docs/)
- [SQLite查询参考](https://www.sqlite.org/lang.html)

## 💡 建议

1. **定期运行数据丰富**: 每周运行一次`enrich_job_data.py`确保新数据被处理
2. **备份数据库**: 定期备份`job_scraper.db`
3. **监控数据质量**: 检查技能提取准确度，调整关键词列表
4. **分享洞察**: 将发现的趋势分享给社区

---

**Happy Analyzing! 📊✨**

