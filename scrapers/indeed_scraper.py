"""
Indeed NZ IT Jobs Scraper
"""

import logging
import time
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class IndeedScraper:
    """Scraper for Indeed New Zealand IT jobs."""
    
    def __init__(self):
        self.base_url = "https://nz.indeed.com"
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
            user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_indeed_{os.getpid()}')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            logger.info("Indeed scraper driver initialized")
            return True
            
        except ImportError:
            logger.error("Selenium not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False
    
    def scrape_jobs(self, max_pages: int = 20) -> List[Dict]:
        """Scrape IT jobs from Indeed NZ."""
        if not self._setup_driver():
            return []
        
        try:
            jobs = []
            
            # Indeed NZ IT jobs search URLs
            search_keywords = [
                "software+developer",
                "data+analyst",
                "IT+support",
                "devops"
            ]
            
            for keyword in search_keywords:
                try:
                    # Indeed uses q for query and l for location
                    # fromage=1 means last 24 hours
                    search_url = f"{self.base_url}/jobs?q={keyword}&l=New+Zealand&fromage=7"
                    logger.info(f"Searching Indeed: {keyword}")
                    
                    page = 0
                    consecutive_empty_pages = 0
                    
                    while page < max_pages and consecutive_empty_pages < 2:
                        # Indeed uses start parameter (0, 10, 20, 30...)
                        page_url = f"{search_url}&start={page * 10}"
                        logger.info(f"Scraping Indeed page {page + 1}: {page_url}")
                        
                        self.driver.get(page_url)
                        time.sleep(random.uniform(2, 4))
                        
                        # Wait for job cards
                        try:
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
                            from selenium.webdriver.common.by import By
                            
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job_seen_beacon, div.slider_item"))
                            )
                        except:
                            logger.warning(f"No job listings found on Indeed page {page + 1}")
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                break
                            page += 1
                            continue
                        
                        page_source = self.driver.page_source
                        page_jobs = self._parse_job_listings(page_source)
                        
                        if page_jobs:
                            jobs.extend(page_jobs)
                            logger.info(f"Found {len(page_jobs)} jobs on Indeed page {page + 1}")
                            consecutive_empty_pages = 0
                        else:
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                logger.info("Reached end of Indeed results")
                                break
                        
                        time.sleep(random.uniform(2, 4))
                        page += 1
                    
                    logger.info(f"Finished scraping Indeed for '{keyword}'")
                    
                    # Limit to avoid rate limiting
                    if len(jobs) > 100:
                        break
                        
                except Exception as e:
                    logger.warning(f"Indeed search failed for {keyword}: {e}")
                    continue
            
            # Remove duplicates
            unique_jobs = []
            seen_urls = set()
            for job in jobs:
                if job.get('url') and job['url'] not in seen_urls:
                    seen_urls.add(job['url'])
                    unique_jobs.append(job)
            
            logger.info(f"Total found {len(unique_jobs)} unique Indeed jobs")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"Indeed scraping failed: {e}")
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _parse_job_listings(self, page_source: str) -> List[Dict]:
        """Parse job listings from Indeed page HTML."""
        soup = BeautifulSoup(page_source, 'html.parser')
        jobs = []
        
        # Indeed job cards
        job_cards = soup.select('div.job_seen_beacon, div.slider_item, td.resultContent')
        
        logger.info(f"Found {len(job_cards)} Indeed job cards")
        
        for card in job_cards[:15]:  # Indeed shows ~15 per page
            job = self._extract_job_from_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job information from an Indeed job card."""
        try:
            # Title and URL
            title_link = card.select_one('h2.jobTitle a, a[data-jk]')
            if not title_link:
                return None
            
            title_span = title_link.select_one('span[title]')
            title = title_span.get('title', '') if title_span else title_link.get_text(strip=True)
            
            job_key = title_link.get('data-jk', '') or title_link.get('id', '').replace('job_', '')
            url = f"{self.base_url}/viewjob?jk={job_key}" if job_key else title_link.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Company
            company_elem = card.select_one('span[data-testid="company-name"], span.companyName')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Location
            location_elem = card.select_one('div[data-testid="text-location"], div.companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Salary
            salary_elem = card.select_one('div.salary-snippet, span.salary-snippet')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            job = {
                'external_id': f"indeed_{job_key}" if job_key else f"indeed_{hash(url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary_range': salary,
                'job_type': 'Full-time',
                'url': url,
                'source': 'indeed'
            }
            
            return job
            
        except Exception as e:
            logger.warning(f"Failed to extract Indeed job: {e}")
            return None


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    scraper = IndeedScraper()
    jobs = scraper.scrape_jobs(max_pages=2)
    print(f"\nScraped {len(jobs)} jobs from Indeed")
    for job in jobs[:5]:
        print(f"- {job['title']} at {job['company']}")

