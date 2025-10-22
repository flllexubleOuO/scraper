"""
TradeMe Jobs NZ IT Jobs Scraper
TradeMe is a major New Zealand job board
"""

import logging
import time
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TradeMeScraper:
    """Scraper for TradeMe Jobs New Zealand IT positions."""
    
    def __init__(self):
        self.base_url = "https://www.trademe.co.nz"
        self.driver = None
        
    def _setup_driver(self):
        """Setup Selenium driver with anti-detection measures."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            
            import tempfile
            import os
            user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_trademe_{os.getpid()}')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            logger.info("TradeMe scraper driver initialized")
            return True
            
        except ImportError:
            logger.error("Selenium not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False
    
    def scrape_jobs(self, max_pages: int = 15) -> List[Dict]:
        """Scrape IT jobs from TradeMe Jobs NZ."""
        if not self._setup_driver():
            return []
        
        try:
            jobs = []
            
            # TradeMe Jobs IT category
            # Category 5000 is IT jobs
            # Can also search by keywords
            search_urls = [
                f"{self.base_url}/a/jobs/it/search",  # IT category
            ]
            
            for search_url in search_urls:
                try:
                    logger.info(f"Searching TradeMe: {search_url}")
                    
                    page = 1
                    consecutive_empty_pages = 0
                    
                    while page <= max_pages and consecutive_empty_pages < 2:
                        page_url = f"{search_url}?page={page}"
                        logger.info(f"Scraping TradeMe page {page}: {page_url}")
                        
                        self.driver.get(page_url)
                        time.sleep(random.uniform(2, 4))
                        
                        # Wait for job cards
                        try:
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
                            from selenium.webdriver.common.by import By
                            
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "tm-search-card-browse, div.tm-search-results"))
                            )
                        except:
                            logger.warning(f"No job listings found on TradeMe page {page}")
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                break
                            page += 1
                            continue
                        
                        page_source = self.driver.page_source
                        page_jobs = self._parse_job_listings(page_source)
                        
                        if page_jobs:
                            jobs.extend(page_jobs)
                            logger.info(f"Found {len(page_jobs)} jobs on TradeMe page {page}")
                            consecutive_empty_pages = 0
                        else:
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                logger.info("Reached end of TradeMe results")
                                break
                        
                        time.sleep(random.uniform(2, 4))
                        page += 1
                    
                    logger.info(f"Finished scraping TradeMe. Total pages: {page - 1}")
                    
                except Exception as e:
                    logger.warning(f"TradeMe search failed: {e}")
                    continue
            
            # Remove duplicates
            unique_jobs = []
            seen_urls = set()
            for job in jobs:
                if job.get('url') and job['url'] not in seen_urls:
                    seen_urls.add(job['url'])
                    unique_jobs.append(job)
            
            logger.info(f"Total found {len(unique_jobs)} unique TradeMe jobs")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"TradeMe scraping failed: {e}")
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _parse_job_listings(self, page_source: str) -> List[Dict]:
        """Parse job listings from TradeMe page HTML."""
        soup = BeautifulSoup(page_source, 'html.parser')
        jobs = []
        
        # TradeMe job cards
        job_cards = soup.select('tm-search-card-browse, div.tm-jobs-search-card, div[class*="supergrid-listing"]')
        
        if not job_cards:
            # Try alternative structure
            job_cards = soup.select('div.o-card, article')
        
        logger.info(f"Found {len(job_cards)} TradeMe job cards")
        
        for card in job_cards[:30]:  # TradeMe shows 30 per page
            job = self._extract_job_from_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job information from a TradeMe job card."""
        try:
            # Title and URL
            title_link = card.select_one('a[tm-search-card-browse-title-link], a.tm-jobs-search-card__title, a[href*="/job/"]')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Company
            company_elem = card.select_one('div[tm-search-card-browse-subtitle], div.tm-jobs-search-card__subtitle, span[class*="subtitle"]')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Location
            location_elem = card.select_one('div[tm-search-card-browse-location], div.tm-jobs-search-card__location, span[class*="location"]')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Salary
            salary_elem = card.select_one('div[tm-search-card-browse-salary], div.tm-jobs-search-card__salary, span[class*="salary"]')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            job = {
                'external_id': self._extract_job_id(url),
                'title': title,
                'company': company,
                'location': location,
                'salary_range': salary,
                'job_type': 'Full-time',
                'url': url,
                'source': 'trademe'
            }
            
            return job
            
        except Exception as e:
            logger.warning(f"Failed to extract TradeMe job: {e}")
            return None
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from TradeMe URL."""
        # TradeMe URLs typically: /a/jobs/.../listing/1234567
        match = re.search(r'/listing/(\d+)', url)
        if match:
            return f"trademe_{match.group(1)}"
        return f"trademe_{hash(url)}"


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    scraper = TradeMeScraper()
    jobs = scraper.scrape_jobs(max_pages=2)
    print(f"\nScraped {len(jobs)} jobs from TradeMe")
    for job in jobs[:5]:
        print(f"- {job['title']} at {job['company']}")

