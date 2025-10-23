#!/usr/bin/env python3
"""
技术栈提取器 - 从职位描述中提取技术关键词
"""

import re
from typing import List, Dict, Set

class TechStackExtractor:
    """从JD中提取技术栈信息"""
    
    def __init__(self):
        # 技术栈字典
        self.tech_keywords = {
            'programming_languages': {
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C#', 'C++', 'Go', 'Rust',
                'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl'
            },
            'frontend': {
                'React', 'Vue', 'Vue.js', 'Angular', 'Next.js', 'Nuxt', 'Svelte',
                'jQuery', 'Bootstrap', 'Tailwind', 'Material-UI', 'Redux', 'Webpack',
                'Vite', 'HTML', 'CSS', 'SASS', 'LESS'
            },
            'backend': {
                'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Spring', '.NET', 'ASP.NET',
                'Node.js', 'Express', 'NestJS', 'Rails', 'Laravel', 'Symfony',
                'Gin', 'Echo', 'Actix'
            },
            'database': {
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'SQL Server',
                'Oracle', 'DynamoDB', 'Cassandra', 'Neo4j', 'SQLite', 'MariaDB',
                'Snowflake', 'BigQuery'
            },
            'cloud': {
                'AWS', 'Azure', 'GCP', 'Google Cloud', 'Heroku', 'DigitalOcean',
                'Lambda', 'EC2', 'S3', 'CloudFront', 'RDS', 'ECS', 'EKS'
            },
            'devops': {
                'Docker', 'Kubernetes', 'K8s', 'Jenkins', 'GitLab CI', 'GitHub Actions',
                'CircleCI', 'Terraform', 'Ansible', 'Chef', 'Puppet', 'Prometheus',
                'Grafana', 'ELK', 'Datadog', 'New Relic', 'CI/CD'
            },
            'data_tools': {
                'Spark', 'Hadoop', 'Kafka', 'Airflow', 'Tableau', 'Power BI',
                'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
                'Jupyter', 'Databricks', 'dbt'
            },
            'version_control': {
                'Git', 'GitHub', 'GitLab', 'Bitbucket', 'SVN'
            },
            'methodologies': {
                'Agile', 'Scrum', 'Kanban', 'DevOps', 'CI/CD', 'TDD', 'BDD',
                'Microservices', 'REST API', 'GraphQL', 'gRPC'
            }
        }
        
        # 工作类型关键词
        self.job_types = {
            'remote': ['remote', 'work from home', 'wfh', 'distributed'],
            'hybrid': ['hybrid', 'flexible location'],
            'onsite': ['on-site', 'office-based', 'in-office']
        }
        
        # 经验等级关键词
        self.experience_levels = {
            'junior': ['junior', 'graduate', 'entry level', 'entry-level', 'intern'],
            'mid': ['mid level', 'mid-level', 'intermediate', '2-5 years'],
            'senior': ['senior', 'lead', 'principal', 'staff', '5+ years', '5-10 years'],
            'expert': ['architect', 'director', 'head of', 'vp', 'chief', '10+ years']
        }
        
        # 福利关键词
        self.benefits = {
            'visa_support', 'health insurance', 'flexible hours', 'professional development',
            'stock options', 'bonus', 'kiwisaver', 'parental leave', 'gym membership'
        }
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取技术栈"""
        if not text:
            return {}
        
        text_lower = text.lower()
        result = {}
        
        for category, keywords in self.tech_keywords.items():
            found = []
            for keyword in keywords:
                # 使用词边界匹配，避免误匹配
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found.append(keyword)
            
            if found:
                result[category] = sorted(list(set(found)))
        
        return result
    
    def extract_work_type(self, text: str) -> List[str]:
        """提取工作类型"""
        if not text:
            return []
        
        text_lower = text.lower()
        types = []
        
        for work_type, keywords in self.job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                types.append(work_type)
        
        return types
    
    def extract_experience_level(self, title: str, description: str) -> str:
        """提取经验等级"""
        combined_text = f"{title} {description}".lower()
        
        for level, keywords in self.experience_levels.items():
            if any(keyword in combined_text for keyword in keywords):
                return level
        
        return 'mid'  # 默认为中级
    
    def extract_benefits(self, text: str) -> List[str]:
        """提取福利关键词"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_benefits = []
        
        for benefit in self.benefits:
            if benefit.replace('_', ' ') in text_lower:
                found_benefits.append(benefit)
        
        return found_benefits
    
    def extract_all(self, job_data: Dict) -> Dict:
        """提取所有信息"""
        title = job_data.get('title', '')
        description = job_data.get('description', '')
        combined_text = f"{title} {description}"
        
        return {
            'tech_stack': self.extract_skills(combined_text),
            'work_type': self.extract_work_type(description),
            'experience_level': self.extract_experience_level(title, description),
            'benefits': self.extract_benefits(description),
            'skills_count': sum(len(v) for v in self.extract_skills(combined_text).values())
        }


def test_extractor():
    """测试提取器"""
    extractor = TechStackExtractor()
    
    # 测试样本
    sample_jd = """
    We are looking for a Senior Full Stack Developer to join our team.
    
    Requirements:
    - 5+ years experience with Python, Django, and React
    - Strong knowledge of AWS, Docker, and Kubernetes
    - Experience with PostgreSQL and Redis
    - Familiar with CI/CD pipelines using GitHub Actions
    
    Benefits:
    - Flexible hours and hybrid working
    - Health insurance
    - Visa support available
    - Professional development budget
    """
    
    result = extractor.extract_all({
        'title': 'Senior Full Stack Developer',
        'description': sample_jd
    })
    
    print("🔍 技术栈提取测试结果:")
    print(f"\n技术栈: {result['tech_stack']}")
    print(f"工作类型: {result['work_type']}")
    print(f"经验等级: {result['experience_level']}")
    print(f"福利: {result['benefits']}")
    print(f"技能总数: {result['skills_count']}")


if __name__ == '__main__':
    test_extractor()

