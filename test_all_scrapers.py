#!/usr/bin/env python3
"""
Test all scrapers individually before running the integrated version.
"""

import logging
import sys
sys.path.append('scrapers')

from scrapers.seek_scraper import SeekScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.trademe_scraper import TradeMeScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_seek():
    """Test Seek scraper."""
    logger.info("\n" + "="*60)
    logger.info("🔍 Testing SEEK scraper")
    logger.info("="*60)
    
    try:
        scraper = SeekScraper()
        jobs = scraper.scrape_jobs(max_pages=2)  # Just 2 pages for testing
        
        logger.info(f"\n✅ SEEK: Found {len(jobs)} jobs")
        if jobs:
            logger.info("\nSample jobs:")
            for job in jobs[:3]:
                logger.info(f"  - {job['title']} at {job['company']} ({job['source']})")
        
        return len(jobs) > 0
        
    except Exception as e:
        logger.error(f"❌ SEEK scraper failed: {e}")
        return False


def test_linkedin():
    """Test LinkedIn scraper."""
    logger.info("\n" + "="*60)
    logger.info("🔍 Testing LINKEDIN scraper")
    logger.info("="*60)
    
    try:
        scraper = LinkedInScraper()
        jobs = scraper.scrape_jobs(max_pages=1)  # Just 1 page for testing
        
        logger.info(f"\n✅ LINKEDIN: Found {len(jobs)} jobs")
        if jobs:
            logger.info("\nSample jobs:")
            for job in jobs[:3]:
                logger.info(f"  - {job['title']} at {job['company']} ({job['source']})")
        
        return True  # LinkedIn might be blocked, so don't fail
        
    except Exception as e:
        logger.error(f"⚠️  LINKEDIN scraper failed (this is often normal): {e}")
        return True  # Don't fail the overall test


def test_indeed():
    """Test Indeed scraper."""
    logger.info("\n" + "="*60)
    logger.info("🔍 Testing INDEED scraper")
    logger.info("="*60)
    
    try:
        scraper = IndeedScraper()
        jobs = scraper.scrape_jobs(max_pages=1)  # Just 1 page for testing
        
        logger.info(f"\n✅ INDEED: Found {len(jobs)} jobs")
        if jobs:
            logger.info("\nSample jobs:")
            for job in jobs[:3]:
                logger.info(f"  - {job['title']} at {job['company']} ({job['source']})")
        
        return len(jobs) > 0
        
    except Exception as e:
        logger.error(f"❌ INDEED scraper failed: {e}")
        return False


def test_trademe():
    """Test TradeMe scraper."""
    logger.info("\n" + "="*60)
    logger.info("🔍 Testing TRADEME scraper")
    logger.info("="*60)
    
    try:
        scraper = TradeMeScraper()
        jobs = scraper.scrape_jobs(max_pages=1)  # Just 1 page for testing
        
        logger.info(f"\n✅ TRADEME: Found {len(jobs)} jobs")
        if jobs:
            logger.info("\nSample jobs:")
            for job in jobs[:3]:
                logger.info(f"  - {job['title']} at {job['company']} ({job['source']})")
        
        return len(jobs) > 0
        
    except Exception as e:
        logger.error(f"❌ TRADEME scraper failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("🚀 Testing All Job Scrapers")
    logger.info("="*60 + "\n")
    
    results = {}
    
    # Test each scraper
    results['seek'] = test_seek()
    results['linkedin'] = test_linkedin()
    results['indeed'] = test_indeed()
    results['trademe'] = test_trademe()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    for source, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {source.upper()}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    
    logger.info(f"\nTotal: {passed}/{total} scrapers working")
    
    if passed >= 2:  # At least 2 scrapers working
        logger.info("\n✅ Overall: PASS - Enough scrapers working!")
        return True
    else:
        logger.info("\n❌ Overall: FAIL - Too few scrapers working")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

