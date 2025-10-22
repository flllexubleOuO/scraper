"""
LinkedIn NZ IT Jobs Scraper
"""

import logging
import time
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scraper for LinkedIn New Zealand IT jobs."""
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com"
        self.driver = None
        
    def _setup_driver(self):
        """Setup Selenium driver with anti-detection measures."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            # Basic headless settings
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Anti-detection
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Unique user data directory
            import tempfile
            import os
            user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_linkedin_{os.getpid()}')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            logger.info("LinkedIn scraper driver initialized")
            return True
            
        except ImportError:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False
    
    def scrape_jobs(self, max_pages: int = 10) -> List[Dict]:
        """
        Scrape IT jobs from LinkedIn NZ.
        
        LinkedIn requires login for full access, so this implementation
        uses the public job search without authentication.
        
        Args:
            max_pages: Maximum pages to scrape
        """
        if not self._setup_driver():
            return []
        
        try:
            jobs = []
            
            # LinkedIn NZ IT jobs search URL (public, no login required)
            # geoId=105490917 is New Zealand (more precise)
            # f_TPR=r86400 means last 24 hours
            # Note: LinkedIn may still show nearby locations based on search results availability
            search_urls = [
                # Try Auckland specifically (geoId=104115568)
                f"{self.base_url}/jobs/search?keywords=software%20developer&location=Auckland%2C%20New%20Zealand&geoId=104115568",
                f"{self.base_url}/jobs/search?keywords=IT%20developer&location=Wellington%2C%20New%20Zealand&geoId=102932717",
                f"{self.base_url}/jobs/search?keywords=software%20engineer&location=New%20Zealand&geoId=105490917",
            ]
            
            for search_url in search_urls:
                try:
                    logger.info(f"Searching LinkedIn: {search_url}")
                    
                    page = 0
                    consecutive_empty_pages = 0
                    
                    while page < max_pages and consecutive_empty_pages < 2:
                        # LinkedIn uses start parameter for pagination (0, 25, 50, 75...)
                        page_url = f"{search_url}&start={page * 25}"
                        logger.info(f"Scraping LinkedIn page {page + 1}: {page_url}")
                        
                        self.driver.get(page_url)
                        time.sleep(random.uniform(3, 5))  # LinkedIn is strict, wait longer
                        
                        # Wait for job cards
                        try:
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
                            from selenium.webdriver.common.by import By
                            
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.base-card"))
                            )
                        except:
                            logger.warning(f"No job listings found on LinkedIn page {page + 1}")
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                break
                            page += 1
                            continue
                        
                        # Parse job listings
                        page_source = self.driver.page_source
                        page_jobs = self._parse_job_listings(page_source)
                        
                        if page_jobs:
                            jobs.extend(page_jobs)
                            logger.info(f"Found {len(page_jobs)} jobs on LinkedIn page {page + 1}")
                            consecutive_empty_pages = 0
                        else:
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                logger.info("Reached end of LinkedIn results")
                                break
                        
                        time.sleep(random.uniform(3, 5))
                        page += 1
                    
                    logger.info(f"Finished scraping LinkedIn search. Total pages: {page}")
                    
                    # Only scrape first search URL for now to avoid too many requests
                    if jobs:
                        break
                        
                except Exception as e:
                    logger.warning(f"LinkedIn search failed: {e}")
                    continue
            
            # Remove duplicates
            unique_jobs = []
            seen_urls = set()
            for job in jobs:
                if job.get('url') and job['url'] not in seen_urls:
                    seen_urls.add(job['url'])
                    unique_jobs.append(job)
            
            logger.info(f"Total found {len(unique_jobs)} unique LinkedIn jobs")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"LinkedIn scraping failed: {e}")
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _parse_job_listings(self, page_source: str) -> List[Dict]:
        """Parse job listings from LinkedIn page HTML."""
        soup = BeautifulSoup(page_source, 'html.parser')
        jobs = []
        
        # LinkedIn uses different selectors for public job search
        job_cards = soup.select('div.base-card')
        
        if not job_cards:
            # Try alternative selector
            job_cards = soup.select('li.jobs-search-results__list-item')
        
        logger.info(f"Found {len(job_cards)} LinkedIn job cards")
        
        for card in job_cards[:25]:  # LinkedIn shows 25 per page
            job = self._extract_job_from_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job information from a LinkedIn job card."""
        try:
            # Title and URL
            title_link = card.select_one('h3.base-search-card__title, a.base-card__full-link')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Company
            company_elem = card.select_one('h4.base-search-card__subtitle, a.hidden-nested-link')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Location
            location_elem = card.select_one('span.job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Job type (if available)
            job_type_elem = card.select_one('span.job-search-card__listed-time')
            job_type = "Full-time"  # Default
            
            job = {
                'external_id': self._extract_job_id(url),
                'title': title,
                'company': company,
                'location': location,
                'salary_range': '',  # LinkedIn rarely shows salary publicly
                'job_type': job_type,
                'url': url,
                'source': 'linkedin'
            }
            
            return job
            
        except Exception as e:
            logger.warning(f"Failed to extract LinkedIn job: {e}")
            return None
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn URL."""
        # LinkedIn URLs typically: /jobs/view/1234567890
        match = re.search(r'/view/(\d+)', url)
        if match:
            return f"linkedin_{match.group(1)}"
        return f"linkedin_{hash(url)}"


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    scraper = LinkedInScraper()
    jobs = scraper.scrape_jobs(max_pages=2)
    print(f"\nScraped {len(jobs)} jobs from LinkedIn")
    for job in jobs[:5]:
        print(f"- {job['title']} at {job['company']}")

