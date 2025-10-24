#!/usr/bin/env python3
"""
丰富现有职位数据 - 提取技术栈和其他特征
"""

import sqlite3
import json
import logging
from tech_stack_extractor import TechStackExtractor
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enrich_jobs(db_path='job_scraper.db', batch_size=100):
    """为现有职位提取技术栈信息"""
    
    logger.info(f"📚 Opening database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否需要添加新列
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = [
        ('tech_stack', 'TEXT'),  # JSON格式的技术栈
        ('work_type', 'TEXT'),   # remote/hybrid/onsite
        ('experience_level', 'TEXT'),  # junior/mid/senior/expert
        ('benefits', 'TEXT'),    # JSON数组
        ('skills_count', 'INTEGER')  # 技能总数
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            logger.info(f"➕ Adding column: {col_name}")
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    
    # 获取所有有描述的职位
    cursor.execute("""
        SELECT id, title, description
        FROM jobs 
        WHERE description IS NOT NULL AND description != ''
        ORDER BY id
    """)
    
    jobs = cursor.fetchall()
    logger.info(f"📊 Found {len(jobs)} jobs with descriptions to enrich")
    
    if not jobs:
        logger.warning("No jobs found to process!")
        return
    
    extractor = TechStackExtractor()
    updated_count = 0
    
    # 处理职位
    for job in tqdm(jobs, desc="Enriching jobs"):
        job_id, title, description = job
        
        try:
            # 提取信息
            extracted = extractor.extract_all({
                'title': title or '',
                'description': description or ''
            })
            
            # 更新数据库
            cursor.execute("""
                UPDATE jobs 
                SET tech_stack = ?,
                    work_type = ?,
                    experience_level = ?,
                    benefits = ?,
                    skills_count = ?
                WHERE id = ?
            """, (
                json.dumps(extracted['tech_stack']),
                json.dumps(extracted['work_type']),
                extracted['experience_level'],
                json.dumps(extracted['benefits']),
                extracted['skills_count'],
                job_id
            ))
            
            updated_count += 1
            
            # 定期提交
            if updated_count % batch_size == 0:
                conn.commit()
                logger.info(f"✅ Processed {updated_count}/{len(jobs)} jobs")
        
        except Exception as e:
            logger.error(f"❌ Error processing job {job_id}: {e}")
            continue
    
    # 最终提交
    conn.commit()
    logger.info(f"🎉 Successfully enriched {updated_count} jobs!")
    
    # 生成统计报告
    generate_stats(cursor)
    
    conn.close()


def generate_stats(cursor):
    """生成统计报告"""
    logger.info("\n📊 === 数据统计报告 ===")
    
    # 经验等级分布
    cursor.execute("""
        SELECT experience_level, COUNT(*) 
        FROM jobs 
        WHERE experience_level IS NOT NULL
        GROUP BY experience_level
        ORDER BY COUNT(*) DESC
    """)
    
    logger.info("\n经验等级分布:")
    for level, count in cursor.fetchall():
        logger.info(f"  {level}: {count}")
    
    # 工作类型分布
    cursor.execute("""
        SELECT work_type, COUNT(*) 
        FROM jobs 
        WHERE work_type IS NOT NULL AND work_type != '[]'
        GROUP BY work_type
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    
    logger.info("\n工作类型分布:")
    for work_type, count in cursor.fetchall():
        try:
            types = json.loads(work_type)
            logger.info(f"  {', '.join(types)}: {count}")
        except:
            continue
    
    # 平均技能数
    cursor.execute("""
        SELECT AVG(skills_count), MIN(skills_count), MAX(skills_count)
        FROM jobs 
        WHERE skills_count IS NOT NULL
    """)
    
    avg, min_skills, max_skills = cursor.fetchone()
    logger.info(f"\n技能统计:")
    logger.info(f"  平均: {avg:.1f}")
    logger.info(f"  最少: {min_skills}")
    logger.info(f"  最多: {max_skills}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich job data with tech stack information')
    parser.add_argument('--db', default='job_scraper.db', help='Database path')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for commits')
    
    args = parser.parse_args()
    
    enrich_jobs(args.db, args.batch_size)

