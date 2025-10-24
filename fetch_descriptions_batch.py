#!/usr/bin/env python3
"""
批量抓取职位描述 - 针对低内存环境优化
每抓取N个职位就重启浏览器，避免内存泄漏
"""

import sqlite3
import logging
import time
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_jobs_without_description(db_path: str, limit: int = None) -> List[Tuple]:
    """获取没有描述的职位"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
        SELECT id, job_id, url, title, company
        FROM jobs 
        WHERE (description IS NULL OR description = '') 
        AND url IS NOT NULL
        AND source = 'seek'
        ORDER BY id DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    jobs = cursor.fetchall()
    conn.close()
    return jobs

def fetch_description_batch(db_path: str, batch_size: int = 5, max_total: int = None, delay: float = 3.0):
    """分批抓取职位描述（低内存优化）"""
    
    # 获取需要抓取的职位
    jobs = get_jobs_without_description(db_path, max_total)
    
    if not jobs:
        logger.info("✅ All jobs already have descriptions!")
        return
    
    logger.info(f"📊 Found {len(jobs)} jobs without descriptions")
    logger.info(f"📦 Processing in batches of {batch_size}")
    
    total_success = 0
    total_failed = 0
    
    # 分批处理
    for batch_start in range(0, len(jobs), batch_size):
        batch_end = min(batch_start + batch_size, len(jobs))
        batch = jobs[batch_start:batch_end]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing batch {batch_start//batch_size + 1}/{(len(jobs)-1)//batch_size + 1}")
        logger.info(f"   Jobs {batch_start+1}-{batch_end} of {len(jobs)}")
        logger.info(f"{'='*60}")
        
        # 初始化爬虫（每批次新建）
        from scrapers.seek_scraper import SeekScraper
        scraper = SeekScraper()
        
        try:
            # 处理本批次
            for job_id, job_external_id, url, title, company in batch:
                try:
                    logger.info(f"📄 Fetching: {title} at {company}")
                    
                    # 抓取描述
                    description = scraper.fetch_job_description(url)
                    
                    if description:
                        # 保存到数据库
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE jobs SET description = ? WHERE id = ?",
                            (description, job_id)
                        )
                        conn.commit()
                        conn.close()
                        
                        total_success += 1
                        logger.info(f"   ✅ Success (length: {len(description)})")
                    else:
                        total_failed += 1
                        logger.warning(f"   ⚠️ No description found")
                    
                    # 延迟，减少内存压力
                    time.sleep(delay)
                    
                except Exception as e:
                    total_failed += 1
                    logger.error(f"   ❌ Error: {e}")
                    continue
            
        finally:
            # 关闭浏览器
            try:
                scraper.close_driver()
                logger.info(f"🔌 Browser closed for batch {batch_start//batch_size + 1}")
            except:
                pass
        
        # 批次间休息，让系统充分恢复内存
        if batch_end < len(jobs):
            rest_time = 10
            logger.info(f"😴 Resting {rest_time} seconds before next batch (memory recovery)...")
            time.sleep(rest_time)
    
    # 最终统计
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Final Statistics")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successful: {total_success}")
    logger.info(f"❌ Failed: {total_failed}")
    logger.info(f"📈 Success rate: {total_success/(total_success+total_failed)*100:.1f}%")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch job descriptions in batches (memory-optimized)')
    parser.add_argument('--db', default='job_scraper.db', help='Database path')
    parser.add_argument('--batch-size', type=int, default=5, help='Jobs per batch (default: 5 for low memory)')
    parser.add_argument('--max-total', type=int, default=None, help='Maximum total jobs to process')
    parser.add_argument('--delay', type=float, default=3.0, help='Delay between jobs in seconds (default: 3)')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting batch description fetcher (LOW MEMORY MODE)")
    logger.info(f"   Database: {args.db}")
    logger.info(f"   Batch size: {args.batch_size} (smaller = less memory)")
    logger.info(f"   Delay per job: {args.delay}s (longer = safer)")
    logger.info(f"   Max total: {args.max_total or 'unlimited'}")
    logger.info(f"   ⏱️  Estimated time: ~{(args.max_total or 500) * (args.delay + 2) / 60:.0f} minutes")
    
    fetch_description_batch(args.db, args.batch_size, args.max_total, args.delay)
    
    logger.info("\n🎉 Batch processing completed!")

