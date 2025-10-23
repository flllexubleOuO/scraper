#!/usr/bin/env python3
"""
数据可视化仪表板 - 新西兰IT市场分析
使用Plotly创建交互式图表
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class JobMarketDashboard:
    """IT职位市场可视化仪表板"""
    
    def __init__(self, db_path='job_scraper.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def load_data(self):
        """加载数据"""
        query = """
        SELECT 
            id, title, company, location, salary_range,
            category, source, is_active,
            tech_stack, work_type, experience_level, benefits, skills_count,
            first_seen_date, last_seen_date,
            strftime('%Y-%m-%d', first_seen_date) as date
        FROM jobs
        WHERE description IS NOT NULL
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # 解析JSON字段
        df['tech_stack_parsed'] = df['tech_stack'].apply(
            lambda x: json.loads(x) if x else {}
        )
        df['work_type_parsed'] = df['work_type'].apply(
            lambda x: json.loads(x) if x else []
        )
        df['benefits_parsed'] = df['benefits'].apply(
            lambda x: json.loads(x) if x else []
        )
        
        return df
    
    def create_time_series_chart(self, df):
        """创建时间序列图 - 每日新增职位"""
        daily_counts = df.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_counts['date'],
            y=daily_counts['count'],
            mode='lines+markers',
            name='每日新增职位',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='📈 新西兰IT职位数量趋势',
            xaxis_title='日期',
            yaxis_title='职位数量',
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def create_category_pie_chart(self, df):
        """创建职位类别饼图"""
        category_counts = df['category'].value_counts().head(8)
        
        fig = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig.update_layout(
            title='💼 职位类别分布',
            template='plotly_white'
        )
        
        return fig
    
    def create_location_bar_chart(self, df):
        """创建地域分布柱状图"""
        location_counts = df['location'].value_counts().head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=location_counts.index,
            y=location_counts.values,
            marker=dict(color='#10b981')
        )])
        
        fig.update_layout(
            title='📍 职位地域分布 Top 10',
            xaxis_title='城市',
            yaxis_title='职位数量',
            template='plotly_white'
        )
        
        return fig
    
    def create_tech_stack_chart(self, df):
        """创建技术栈需求图"""
        all_skills = {}
        
        for tech_dict in df['tech_stack_parsed']:
            for category, skills in tech_dict.items():
                if category not in all_skills:
                    all_skills[category] = Counter()
                all_skills[category].update(skills)
        
        # 选择几个主要类别
        categories_to_show = ['programming_languages', 'frontend', 'backend', 'cloud', 'database']
        
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[cat.replace('_', ' ').title() for cat in categories_to_show] + [''],
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}, {"type": "domain"}]]
        )
        
        positions = [(1,1), (1,2), (1,3), (2,1), (2,2)]
        
        for idx, category in enumerate(categories_to_show):
            if category in all_skills:
                top_skills = dict(all_skills[category].most_common(10))
                
                row, col = positions[idx]
                fig.add_trace(
                    go.Bar(
                        x=list(top_skills.keys()),
                        y=list(top_skills.values()),
                        name=category,
                        showlegend=False
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            title_text='💻 技术栈需求热度 Top 10',
            showlegend=False,
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def create_experience_level_chart(self, df):
        """创建经验等级分布图"""
        exp_counts = df['experience_level'].value_counts()
        
        fig = go.Figure(data=[go.Bar(
            x=exp_counts.index,
            y=exp_counts.values,
            marker=dict(
                color=exp_counts.values,
                colorscale='Viridis'
            ),
            text=exp_counts.values,
            textposition='auto'
        )])
        
        fig.update_layout(
            title='🎓 职位经验等级分布',
            xaxis_title='经验等级',
            yaxis_title='职位数量',
            template='plotly_white'
        )
        
        return fig
    
    def create_company_ranking(self, df):
        """创建公司招聘排行榜"""
        company_counts = df['company'].value_counts().head(15)
        
        fig = go.Figure(data=[go.Bar(
            y=company_counts.index,
            x=company_counts.values,
            orientation='h',
            marker=dict(color='#f59e0b')
        )])
        
        fig.update_layout(
            title='🏢 最活跃招聘公司 Top 15',
            xaxis_title='职位数量',
            yaxis_title='公司',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def generate_html_dashboard(self, output_file='dashboard.html'):
        """生成完整的HTML仪表板"""
        print("📊 Loading data...")
        df = self.load_data()
        
        print(f"✅ Loaded {len(df)} jobs")
        print("📈 Creating visualizations...")
        
        # 创建所有图表
        charts = {
            'time_series': self.create_time_series_chart(df),
            'category': self.create_category_pie_chart(df),
            'location': self.create_location_bar_chart(df),
            'tech_stack': self.create_tech_stack_chart(df),
            'experience': self.create_experience_level_chart(df),
            'companies': self.create_company_ranking(df)
        }
        
        # 生成HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>新西兰IT市场分析仪表板</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f3f4f6;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #3b82f6;
        }}
        .stat-label {{
            color: #6b7280;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🇳🇿 新西兰IT职位市场分析仪表板</h1>
        <p>数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{len(df)}</div>
            <div class="stat-label">总职位数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{df['company'].nunique()}</div>
            <div class="stat-label">招聘公司数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{df[df['is_active']==1].shape[0]}</div>
            <div class="stat-label">活跃职位</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{df['skills_count'].mean():.1f}</div>
            <div class="stat-label">平均技能要求数</div>
        </div>
    </div>
    
    <div class="chart-container" id="time_series"></div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="chart-container" id="category"></div>
        <div class="chart-container" id="location"></div>
    </div>
    <div class="chart-container" id="tech_stack"></div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="chart-container" id="experience"></div>
        <div class="chart-container" id="companies"></div>
    </div>
    
    <script>
    """
        
        for name, fig in charts.items():
            html_content += f"Plotly.newPlot('{name}', {fig.to_json()}, {{}});\n"
        
        html_content += """
    </script>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard saved to {output_file}")
        return output_file
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate IT job market dashboard')
    parser.add_argument('--db', default='job_scraper.db', help='Database path')
    parser.add_argument('--output', default='dashboard.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    dashboard = JobMarketDashboard(args.db)
    dashboard.generate_html_dashboard(args.output)
    dashboard.close()
    
    print(f"\n🌐 Open {args.output} in your browser to view the dashboard!")

