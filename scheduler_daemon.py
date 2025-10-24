#!/usr/bin/env python3
"""
Job Scraper Scheduler - 定时任务守护进程
每天12:00自动运行爬虫
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime
import os
import sys

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, 'scheduler.log')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_scraper():
    """运行爬虫脚本"""
    logger.info("=" * 60)
    logger.info("🚀 Starting scheduled scraping job...")
    logger.info("=" * 60)
    
    try:
        # 切换到scrapers目录并运行爬虫
        scraper_path = os.path.join(SCRIPT_DIR, 'scrapers')
        scraper_script = 'integrated_scraper.py'
        
        # 运行爬虫：抓取所有源，包含所有JD
        cmd = [
            sys.executable,  # 使用当前Python解释器
            scraper_script,
            '--sources', 'seek', 'linkedin', 'indeed', 'trademe',
            '--fetch-descriptions'
            # 不设置 max-descriptions，抓取所有职位的JD
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        logger.info(f"Working directory: {scraper_path}")
        
        # 执行命令并捕获输出
        result = subprocess.run(
            cmd,
            cwd=scraper_path,
            capture_output=True,
            text=True,
            timeout=7200  # 2小时超时（抓取所有JD需要更多时间）
        )
        
        # 记录输出
        if result.stdout:
            logger.info(f"Scraper output:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"Scraper errors:\n{result.stderr}")
        
        # 检查返回码
        if result.returncode == 0:
            logger.info("✅ Scraping job completed successfully!")
            
            # 爬虫成功后，自动运行数据丰富脚本
            logger.info("=" * 60)
            logger.info("🔄 Running data enrichment to extract tech stack...")
            logger.info("=" * 60)
            
            try:
                enrich_cmd = [
                    sys.executable,
                    'enrich_job_data.py',
                    '--db', os.path.join(SCRIPT_DIR, 'job_scraper.db')
                ]
                
                enrich_result = subprocess.run(
                    enrich_cmd,
                    cwd=SCRIPT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10分钟超时
                )
                
                if enrich_result.returncode == 0:
                    logger.info("✅ Data enrichment completed successfully!")
                else:
                    logger.warning(f"⚠️ Data enrichment failed with return code: {enrich_result.returncode}")
                    
                if enrich_result.stdout:
                    logger.info(f"Enrichment output:\n{enrich_result.stdout}")
                    
            except Exception as e:
                logger.error(f"❌ Error running data enrichment: {e}")
        else:
            logger.error(f"❌ Scraping job failed with return code: {result.returncode}")
        
        logger.info("=" * 60)
        logger.info(f"Next run scheduled at 12:00 tomorrow")
        logger.info("=" * 60)
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Scraping job timed out after 1 hour")
    except Exception as e:
        logger.error(f"❌ Error running scraper: {e}", exc_info=True)

def test_run():
    """测试运行（立即执行一次）"""
    logger.info("🧪 Running test scraping job...")
    run_scraper()

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🤖 Job Scraper Scheduler Started")
    logger.info("=" * 60)
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Schedule: Every day at 12:00")
    logger.info("=" * 60)
    
    # 设置定时任务：每天12:00运行
    schedule.every().day.at("12:00").do(run_scraper)
    
    # 如果启动时已经过了今天的12:00，显示下次运行时间
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"⏰ Next run scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logger.info("Running in test mode (immediate execution)...")
        test_run()
        logger.info("Test completed. Scheduler will continue running...")
    
    # 主循环
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("\n👋 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}", exc_info=True)

if __name__ == '__main__':
    main()

