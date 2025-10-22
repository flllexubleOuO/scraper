#!/usr/bin/env python3
"""
技术需求趋势分析工具
分析职位描述（JD）中的技术栈、技能要求等
"""

import sqlite3
import re
from collections import Counter
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class TechTrendAnalyzer:
    """分析职位描述中的技术趋势"""
    
    def __init__(self, db_path='job_scraper.db'):
        self.db_path = db_path
        
        # 定义要跟踪的技术关键词
        self.tech_keywords = {
            # 编程语言
            'Python': ['python'],
            'Java': ['java', r'\bjava\b'],
            'JavaScript': ['javascript', 'js'],
            'TypeScript': ['typescript', 'ts'],
            'C#': ['c#', 'c-sharp', 'csharp'],
            'C++': ['c++', 'cpp'],
            'Go': [r'\bgo\b', 'golang'],
            'Rust': ['rust'],
            'PHP': ['php'],
            'Ruby': ['ruby'],
            'Swift': ['swift'],
            'Kotlin': ['kotlin'],
            'R': [r'\b r \b', r'\br\b'],
            'Scala': ['scala'],
            
            # 前端框架
            'React': ['react', 'react.js', 'reactjs'],
            'Angular': ['angular'],
            'Vue': ['vue', 'vue.js', 'vuejs'],
            'Next.js': ['next.js', 'nextjs'],
            'Svelte': ['svelte'],
            
            # 后端框架
            'Node.js': ['node.js', 'nodejs', 'node'],
            'Django': ['django'],
            'Flask': ['flask'],
            'Spring': ['spring boot', 'spring'],
            '.NET': ['.net', 'dotnet', 'asp.net'],
            'Express': ['express.js', 'express'],
            'FastAPI': ['fastapi'],
            
            # 数据库
            'PostgreSQL': ['postgresql', 'postgres'],
            'MySQL': ['mysql'],
            'MongoDB': ['mongodb', 'mongo'],
            'Redis': ['redis'],
            'SQL Server': ['sql server', 'mssql'],
            'Oracle': ['oracle db', 'oracle'],
            'SQLite': ['sqlite'],
            'Elasticsearch': ['elasticsearch', 'elastic'],
            
            # 云平台
            'AWS': ['aws', 'amazon web services'],
            'Azure': ['azure', 'microsoft azure'],
            'GCP': ['gcp', 'google cloud'],
            'Alibaba Cloud': ['alibaba cloud', 'aliyun'],
            
            # DevOps & 工具
            'Docker': ['docker'],
            'Kubernetes': ['kubernetes', 'k8s'],
            'Jenkins': ['jenkins'],
            'GitLab CI': ['gitlab ci', 'gitlab-ci'],
            'GitHub Actions': ['github actions'],
            'Terraform': ['terraform'],
            'Ansible': ['ansible'],
            
            # 数据科学 & AI
            'Machine Learning': ['machine learning', 'ml'],
            'Deep Learning': ['deep learning', 'dl'],
            'TensorFlow': ['tensorflow'],
            'PyTorch': ['pytorch'],
            'Pandas': ['pandas'],
            'NumPy': ['numpy'],
            'Scikit-learn': ['scikit-learn', 'sklearn'],
            'Data Science': ['data science'],
            'AI': ['artificial intelligence', r'\bai\b'],
            
            # 其他技术
            'REST API': ['rest api', 'restful'],
            'GraphQL': ['graphql'],
            'Microservices': ['microservices', 'micro-services'],
            'CI/CD': ['ci/cd', 'continuous integration'],
            'Agile': ['agile', 'scrum'],
            'Git': ['git', 'github', 'gitlab'],
        }
    
    def get_jobs_with_descriptions(self) -> List[Dict]:
        """获取所有包含JD的职位"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, company, description, category, source, created_at
            FROM jobs
            WHERE description != '' AND description IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def count_tech_mentions(self, jobs: List[Dict]) -> Counter:
        """统计各技术在JD中出现的次数"""
        tech_counter = Counter()
        
        for job in jobs:
            description = job['description'].lower()
            
            # 检查每个技术关键词
            for tech_name, patterns in self.tech_keywords.items():
                for pattern in patterns:
                    if re.search(pattern, description, re.IGNORECASE):
                        tech_counter[tech_name] += 1
                        break  # 找到一个就够了，避免重复计数
        
        return tech_counter
    
    def analyze_by_category(self, jobs: List[Dict]) -> Dict[str, Counter]:
        """按职位类别分析技术需求"""
        category_tech = {}
        
        # 按类别分组
        category_jobs = {}
        for job in jobs:
            category = job.get('category', 'Unknown')
            if category not in category_jobs:
                category_jobs[category] = []
            category_jobs[category].append(job)
        
        # 分析每个类别
        for category, cat_jobs in category_jobs.items():
            category_tech[category] = self.count_tech_mentions(cat_jobs)
        
        return category_tech
    
    def analyze_by_source(self, jobs: List[Dict]) -> Dict[str, Counter]:
        """按数据源分析技术需求"""
        source_tech = {}
        
        # 按来源分组
        source_jobs = {}
        for job in jobs:
            source = job.get('source', 'seek')
            if source not in source_jobs:
                source_jobs[source] = []
            source_jobs[source].append(job)
        
        # 分析每个来源
        for source, src_jobs in source_jobs.items():
            source_tech[source] = self.count_tech_mentions(src_jobs)
        
        return source_tech
    
    def print_top_technologies(self, tech_counter: Counter, top_n=20):
        """打印最热门的技术"""
        logger.info(f"\n🔥 Top {top_n} 热门技术:")
        logger.info("=" * 60)
        
        for i, (tech, count) in enumerate(tech_counter.most_common(top_n), 1):
            percentage = (count / len(self.get_jobs_with_descriptions())) * 100
            bar = '█' * int(percentage / 2)
            logger.info(f"{i:2d}. {tech:20s} | {count:3d} 次 ({percentage:5.1f}%) {bar}")
    
    def print_category_analysis(self, category_tech: Dict[str, Counter], top_n=10):
        """打印按类别的技术需求分析"""
        logger.info("\n📊 按职位类别分析:")
        logger.info("=" * 60)
        
        for category, tech_counter in sorted(category_tech.items()):
            if not tech_counter:
                continue
            
            logger.info(f"\n【{category}】 - {sum(tech_counter.values())} 个技术提及")
            for i, (tech, count) in enumerate(tech_counter.most_common(top_n), 1):
                logger.info(f"  {i:2d}. {tech:20s} - {count:3d} 次")
    
    def generate_report(self):
        """生成完整的技术趋势报告"""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 新西兰IT市场技术需求分析报告")
        logger.info("=" * 60)
        
        # 获取数据
        jobs = self.get_jobs_with_descriptions()
        
        if not jobs:
            logger.warning("⚠️  没有找到包含JD的职位数据！")
            logger.info("\n提示：运行以下命令抓取JD：")
            logger.info("  cd scrapers && python integrated_scraper.py --sources seek --fetch-descriptions --max-descriptions 50")
            return
        
        logger.info(f"\n📈 数据统计:")
        logger.info(f"  - 总职位数（含JD）: {len(jobs)}")
        
        # 按来源统计
        source_counts = Counter(job['source'] for job in jobs)
        logger.info(f"  - 数据源分布: {dict(source_counts)}")
        
        # 按类别统计
        category_counts = Counter(job['category'] for job in jobs)
        logger.info(f"  - 职位类别分布:")
        for category, count in category_counts.most_common():
            logger.info(f"    • {category}: {count}")
        
        # 整体技术需求分析
        overall_tech = self.count_tech_mentions(jobs)
        self.print_top_technologies(overall_tech, top_n=20)
        
        # 按类别分析
        category_tech = self.analyze_by_category(jobs)
        self.print_category_analysis(category_tech, top_n=10)
        
        # 技术栈组合分析
        logger.info("\n🔗 常见技术栈组合:")
        logger.info("=" * 60)
        self.analyze_tech_stacks(jobs)
        
        # 新兴技术趋势
        logger.info("\n🌟 新兴技术关注度:")
        logger.info("=" * 60)
        emerging_tech = {k: v for k, v in overall_tech.items() 
                        if k in ['Rust', 'Go', 'Kubernetes', 'GraphQL', 'Next.js', 
                                'FastAPI', 'Svelte', 'PyTorch', 'TensorFlow']}
        for tech, count in sorted(emerging_tech.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                logger.info(f"  • {tech:20s} - {count:3d} 次")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 分析完成！")
        logger.info("=" * 60)
    
    def analyze_tech_stacks(self, jobs: List[Dict]):
        """分析常见的技术栈组合"""
        # 定义一些技术栈组合
        stacks = {
            'MERN (MongoDB + Express + React + Node)': ['mongodb', 'express', 'react', 'node'],
            'MEAN (MongoDB + Express + Angular + Node)': ['mongodb', 'express', 'angular', 'node'],
            'Django + PostgreSQL + React': ['django', 'postgres', 'react'],
            'Spring Boot + MySQL': ['spring', 'mysql'],
            '.NET + SQL Server': ['.net', 'sql server'],
            'Python + Machine Learning': ['python', 'machine learning'],
            'AWS + Docker + Kubernetes': ['aws', 'docker', 'kubernetes'],
        }
        
        stack_counts = Counter()
        
        for job in jobs:
            description = job['description'].lower()
            
            for stack_name, tech_list in stacks.items():
                # 检查是否所有技术都出现
                if all(any(re.search(pattern, description, re.IGNORECASE) 
                          for pattern in self.tech_keywords.get(tech, [tech.lower()]))
                      for tech in tech_list):
                    stack_counts[stack_name] += 1
        
        for stack, count in stack_counts.most_common(10):
            if count > 0:
                logger.info(f"  • {stack:45s} - {count:3d} 次")


def main():
    """主函数"""
    analyzer = TechTrendAnalyzer()
    analyzer.generate_report()


if __name__ == '__main__':
    main()

