#!/usr/bin/env python3
"""
Integrated scraper that combines multiple job sources.
Supports: Seek, LinkedIn, Indeed, TradeMe
"""

import sys
import logging
import sqlite3
from datetime import datetime
from seek_scraper import SeekScraper
from linkedin_scraper import LinkedInScraper
from indeed_scraper import IndeedScraper
from trademe_scraper import TradeMeScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class IntegratedScraper:
    """Integrated scraper that collects jobs from multiple sources."""
    
    def __init__(self, db_path=None, sources=None):
        # 使用绝对路径，确保爬虫和Flask使用同一个数据库
        if db_path is None:
            import os
            # 获取项目根目录（scrapers的父目录）
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, 'job_scraper.db')
        self.db_path = db_path
        logger.info(f"Using database: {self.db_path}")
        
        # Initialize scrapers for requested sources
        self.scrapers = {}
        if sources is None:
            sources = ['seek', 'linkedin', 'indeed', 'trademe']
        
        if 'seek' in sources:
            self.scrapers['seek'] = SeekScraper()
        if 'linkedin' in sources:
            self.scrapers['linkedin'] = LinkedInScraper()
        if 'indeed' in sources:
            self.scrapers['indeed'] = IndeedScraper()
        if 'trademe' in sources:
            self.scrapers['trademe'] = TradeMeScraper()
        
        logger.info(f"Initialized scrapers for: {', '.join(self.scrapers.keys())}")
    
    def scrape_and_save(self, sources=None, fetch_descriptions=False, max_descriptions=None):
        """Scrape jobs from multiple sources and save to database.
        
        Args:
            sources: List of sources to scrape, or None for all
            fetch_descriptions: Whether to fetch full job descriptions
            max_descriptions: Maximum number of descriptions to fetch per source (None = fetch all)
        """
        logger.info("🚀 Starting integrated multi-source scraping...")
        
        all_jobs = []
        
        # Determine which sources to scrape
        if sources is None:
            sources = list(self.scrapers.keys())
        
        try:
            # Scrape from each source
            for source_name in sources:
                if source_name not in self.scrapers:
                    logger.warning(f"Scraper for '{source_name}' not initialized, skipping")
                    continue
                
                logger.info(f"\n📡 Scraping from {source_name.upper()}...")
                scraper = self.scrapers[source_name]
                
                try:
                    # Different scrapers may have different optimal page limits
                    if source_name == 'seek':
                        # Keep driver open if we need to fetch descriptions
                        jobs = scraper.scrape_jobs(max_pages=999, keep_driver=fetch_descriptions)
                    elif source_name == 'linkedin':
                        jobs = scraper.scrape_jobs(max_pages=5)  # LinkedIn is slower
                    elif source_name == 'indeed':
                        jobs = scraper.scrape_jobs(max_pages=10)
                    elif source_name == 'trademe':
                        jobs = scraper.scrape_jobs(max_pages=10)
                    else:
                        jobs = scraper.scrape_jobs()
                    
                    logger.info(f"✅ {source_name.upper()}: Found {len(jobs)} jobs")
                    
                    # Fetch descriptions if requested (currently only for Seek)
                    if fetch_descriptions and source_name == 'seek' and hasattr(scraper, 'enrich_jobs_with_descriptions'):
                        logger.info(f"\n📄 Fetching job descriptions for {source_name.upper()}...")
                        jobs = scraper.enrich_jobs_with_descriptions(jobs, max_jobs=max_descriptions)
                        # Close driver after fetching descriptions
                        if hasattr(scraper, 'close_driver'):
                            scraper.close_driver()
                    
                    all_jobs.extend(jobs)
                    
                except Exception as e:
                    logger.error(f"❌ {source_name.upper()} scraping failed: {e}")
                    continue
            
            logger.info(f"\n📊 Total jobs collected from all sources: {len(all_jobs)}")
            
            if not all_jobs:
                logger.warning("No jobs found from any source")
                return
            
            # Save to database
            saved_count = self._save_jobs_to_db(all_jobs)
            logger.info(f"💾 Saved {saved_count} new jobs to database")
            
        except Exception as e:
            logger.error(f"Integrated scraping failed: {e}")
            raise
    
    def _save_jobs_to_db(self, jobs):
        """Save jobs to database with smart deduplication and status tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                salary_range TEXT,
                job_type TEXT,
                description TEXT,
                url TEXT UNIQUE,
                category TEXT,
                skills TEXT,
                source TEXT DEFAULT 'seek',
                first_seen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                is_new_today BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 每次运行前，将所有is_new_today重置为0
        cursor.execute('UPDATE jobs SET is_new_today = 0')
        
        today = datetime.now().date().isoformat()
        new_count = 0
        updated_count = 0
        
        # Get all current active job URLs to mark inactive ones
        scraped_urls = {job['url'] for job in jobs}
        
        for job in jobs:
            try:
                # Clean URL (remove query parameters for comparison)
                clean_url = job['url'].split('?')[0] if '?' in job['url'] else job['url']
                
                # Check if job already exists (by URL or external_id)
                cursor.execute('''
                    SELECT id, first_seen_date, last_seen_date, is_active, company, title
                    FROM jobs 
                    WHERE url LIKE ? OR external_id = ?
                ''', (f"{clean_url}%", job['external_id']))
                
                existing = cursor.fetchone()
                
                if existing:
                    job_id, first_seen, last_seen, is_active, old_company, old_title = existing
                    last_seen_date = datetime.fromisoformat(last_seen).date() if last_seen else None
                    
                    # Check if this is today's first sighting
                    if last_seen_date != datetime.now().date():
                        # Update last_seen_date
                        cursor.execute('''
                            UPDATE jobs 
                            SET last_seen_date = ?,
                                is_active = 1,
                                updated_at = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), datetime.now().isoformat(), job_id))
                        
                        logger.info(f"📅 Updated job (still active): {job['title']}")
                        updated_count += 1
                    else:
                        logger.debug(f"Already seen today: {job['title']}")
                    
                else:
                    # Insert new job (标记为今日新增)
                    cursor.execute('''
                        INSERT INTO jobs (
                            external_id, title, company, location, description, 
                            url, category, job_type, salary_range, skills, 
                            source, first_seen_date, last_seen_date, is_new_today
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        job['external_id'],
                        job['title'],
                        job['company'],
                        job['location'],
                        job.get('description', ''),  # Use description from job if available
                        job['url'],
                        self._classify_job(job['title']),
                        job['job_type'],
                        job['salary_range'],
                        '',  # Skills will be empty for now
                        job.get('source', 'seek'),  # Source from job data
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        1  # is_new_today = 1 (今日新增)
                    ))
                    
                    new_count += 1
                    logger.info(f"✨ NEW job: {job['title']} at {job['company']}")
                
            except Exception as e:
                logger.error(f"Failed to save job {job.get('title', 'Unknown')}: {e}")
                continue
        
        # Mark jobs as inactive if they weren't seen today
        # (Only mark as inactive if they were active and last seen before today)
        cursor.execute('''
            UPDATE jobs 
            SET is_active = 0, updated_at = ?
            WHERE is_active = 1 
            AND date(last_seen_date) < date(?)
        ''', (datetime.now().isoformat(), datetime.now().isoformat()))
        
        inactive_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Summary: {new_count} new jobs, {updated_count} updated jobs, {inactive_count} marked inactive")
        return new_count
    
    def _classify_job(self, title):
        """Simple job classification based on title keywords."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['data', 'analyst', 'scientist']):
            return 'Data Analyst'
        elif any(word in title_lower for word in ['frontend', 'front-end', 'react', 'angular', 'vue']):
            return 'Software Developer (Frontend)'
        elif any(word in title_lower for word in ['backend', 'back-end', 'api', 'server']):
            return 'Software Developer (Backend)'
        elif any(word in title_lower for word in ['full stack', 'fullstack', 'full-stack']):
            return 'Software Developer (Full-stack)'
        elif any(word in title_lower for word in ['devops', 'cloud', 'aws', 'azure']):
            return 'DevOps Engineer'
        elif any(word in title_lower for word in ['qa', 'test', 'testing', 'quality']):
            return 'QA Engineer'
        elif any(word in title_lower for word in ['support', 'admin', 'system']):
            return 'IT Support'
        else:
            return 'Software Developer (General)'

def main():
    """Main function for running the integrated scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape IT jobs from multiple sources')
    parser.add_argument('--sources', nargs='+', 
                        choices=['seek', 'linkedin', 'indeed', 'trademe', 'all'],
                        default=['all'],
                        help='Job sources to scrape (default: all)')
    parser.add_argument('--db', default='../job_scraper.db',
                        help='Database path (default: ../job_scraper.db)')
    parser.add_argument('--fetch-descriptions', action='store_true',
                        help='Fetch full job descriptions (slower but more detailed)')
    parser.add_argument('--max-descriptions', type=int, default=None,
                        help='Maximum number of job descriptions to fetch (default: None = fetch all)')
    
    args = parser.parse_args()
    
    # Parse sources
    sources = None
    if 'all' not in args.sources:
        sources = args.sources
    
    logger.info(f"🎯 Starting scraper with sources: {sources or 'all'}")
    if args.fetch_descriptions:
        if args.max_descriptions:
            logger.info(f"📄 Will fetch job descriptions (max: {args.max_descriptions})")
        else:
            logger.info(f"📄 Will fetch ALL job descriptions (unlimited)")
    
    scraper = IntegratedScraper(db_path=args.db, sources=sources)
    
    try:
        scraper.scrape_and_save(
            fetch_descriptions=args.fetch_descriptions,
            max_descriptions=args.max_descriptions
        )
        logger.info("✅ Integrated scraping completed successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Integrated scraping failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
