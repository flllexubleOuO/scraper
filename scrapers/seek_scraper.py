"""
Lightweight Selenium scraper for Seek NZ optimized for cheap AWS instances.
"""

import time
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class SeekScraper:
    """Lightweight Selenium scraper for Seek NZ."""
    
    def __init__(self):
        self.base_url = 'https://www.seek.co.nz'
        self.driver = None
    
    def _setup_driver(self):
        """Setup lightweight Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            
            # Headless mode for production
            chrome_options.add_argument('--headless')
            
            # Essential arguments for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # Resource optimization (but keep JS enabled for Seek)
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-css')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Memory optimization (极限省内存模式)
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=256')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--password-store=basic')
            chrome_options.add_argument('--use-mock-keychain')
            # 限制缓存大小
            chrome_options.add_argument('--disk-cache-size=1')
            chrome_options.add_argument('--media-cache-size=1')
            
            # Anti-detection
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Window size optimization
            chrome_options.add_argument('--window-size=800,600')
            
            # Use a unique user data directory to avoid conflicts
            import tempfile
            import os
            user_data_dir = os.path.join(tempfile.gettempdir(), f'selenium_chrome_{os.getpid()}')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            return True
            
        except ImportError:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return False
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False
    
    def scrape_jobs(self, max_pages: int = 999, keep_driver=False) -> List[Dict]:
        """Scrape IT jobs using lightweight Selenium with pagination support.
        
        Args:
            max_pages: Maximum pages to scrape (default 999 means scrape until no more pages)
            keep_driver: If True, keep the driver open for fetching job descriptions
        """
        if not self._setup_driver():
            return []
        
        try:
            jobs = []
            
            # Use classification search for comprehensive coverage
            # classification=6281 is "Information & Communication Technology" in Seek NZ
            search_urls = [
                f"{self.base_url}/jobs?classification=6281"
            ]
            
            for search_url in search_urls:
                try:
                    logger.info(f"Searching: {search_url}")
                    
                    # Scrape until no more pages
                    page = 1
                    consecutive_empty_pages = 0
                    
                    while page <= max_pages and consecutive_empty_pages < 2:
                        page_url = f"{search_url}&page={page}"
                        logger.info(f"Scraping page {page}: {page_url}")
                        
                        self.driver.get(page_url)
                        time.sleep(random.uniform(2, 4))  # Random delay to avoid detection
                        
                        # Quick check for job listings
                        try:
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
                            from selenium.webdriver.common.by import By
                            
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-automation='normalJob']"))
                            )
                        except:
                            logger.warning(f"No job listings found on page {page}, stopping pagination...")
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                break
                            continue
                        
                        # Parse job listings
                        page_source = self.driver.page_source
                        page_jobs = self._parse_job_listings(page_source)
                        
                        if page_jobs:
                            jobs.extend(page_jobs)
                            logger.info(f"Found {len(page_jobs)} jobs on page {page}")
                            consecutive_empty_pages = 0
                        else:
                            logger.info(f"No jobs found on page {page}")
                            consecutive_empty_pages += 1
                            if consecutive_empty_pages >= 2:
                                logger.info("Reached end of results, stopping pagination")
                                break
                        
                        # Random delay between pages
                        time.sleep(random.uniform(2, 3))
                        page += 1
                    
                    logger.info(f"Finished scraping. Total pages: {page - 1}")
                    
                    # If we got jobs, don't try other search URLs
                    if jobs:
                        break
                        
                except Exception as e:
                    logger.warning(f"Search failed: {e}")
                    continue
            
            # Remove duplicates by URL
            unique_jobs = []
            seen_urls = set()
            for job in jobs:
                if job.get('url') and job['url'] not in seen_urls:
                    seen_urls.add(job['url'])
                    unique_jobs.append(job)
            
            logger.info(f"Total found {len(unique_jobs)} unique jobs (from {len(jobs)} total)")
            return unique_jobs
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []
        finally:
            # Only quit driver if not keeping it for description fetching
            if not keep_driver and self.driver:
                self.driver.quit()
    
    def _parse_job_listings(self, html: str) -> List[Dict]:
        """Parse job listings from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        # Look for job cards
        job_cards = soup.find_all('article', {'data-automation': 'normalJob'})
        
        if not job_cards:
            logger.warning("No job cards found")
            return []
        
        logger.info(f"Found {len(job_cards)} job cards")
        
        for card in job_cards[:20]:  # Extract up to 20 jobs per page
            job = self._extract_job_from_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job information from a job card."""
        try:
            # Try multiple selectors for title and URL
            title_selectors = [
                'a[data-automation="jobTitle"]',
                'h3 a',
                'h2 a',
                'a[href*="/job/"]',
                'a'
            ]
            
            title_link = None
            for selector in title_selectors:
                title_link = card.select_one(selector)
                if title_link:
                    break
            
            if not title_link:
                logger.debug("No title link found in card")
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Try multiple selectors for company - improved extraction
            company_selectors = [
                'a[data-automation="jobCompany"]',  # Company link
                'span[data-automation="jobCompany"]',
                'div[data-automation="jobCompany"]',
                'a[data-automation="job-card-company"]',
                'span.company',
                'div.company',
                '[data-automation*="company"]',
                '[data-automation*="advertiser"]'
            ]
            
            company = ""
            for selector in company_selectors:
                company_elem = card.select_one(selector)
                if company_elem:
                    # Try to get text from link or span
                    company_text = company_elem.get_text(strip=True)
                    if company_text and company_text.lower() != 'private advertiser':
                        company = company_text
                        break
            
            # If still no company, try to extract from nearby elements
            if not company:
                # Sometimes company is in a specific structure
                company_container = card.select_one('[class*="advertiser"]')
                if company_container:
                    company = company_container.get_text(strip=True)
            
            # Try multiple selectors for location
            location_selectors = [
                'span[data-automation="jobLocation"]',
                'div[data-automation="jobLocation"]',
                'span.location',
                'div.location',
                '[data-automation*="location"]'
            ]
            
            location = ""
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Try multiple selectors for salary
            salary_selectors = [
                'span[data-automation="jobSalary"]',
                'div[data-automation="jobSalary"]',
                'span.salary',
                'div.salary',
                '[data-automation*="salary"]'
            ]
            
            salary = ""
            for selector in salary_selectors:
                salary_elem = card.select_one(selector)
                if salary_elem:
                    salary = salary_elem.get_text(strip=True)
                    break
            
            # Only return job if we have essential info
            if not title:
                logger.debug(f"No title found in card: {card.get_text()[:100]}...")
                return None
            
            if not company:
                company = "Unknown Company"  # Fallback
            
            job = {
                'external_id': self._extract_job_id(url),
                'title': title,
                'company': company,
                'location': location,
                'salary_range': salary,
                'job_type': 'Full-time',
                'url': url,
                'source': 'seek'
            }
            
            return job
            
        except Exception as e:
            logger.warning(f"Failed to extract job: {e}")
            return None
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from URL."""
        match = re.search(r'/job/(\d+)', url)
        return match.group(1) if match else url
    
    def fetch_job_description(self, job_url: str) -> str:
        """
        Fetch full job description from job detail page.
        
        Args:
            job_url: Full URL to the job posting
            
        Returns:
            Job description text or empty string if failed
        """
        try:
            logger.info(f"Fetching job description from: {job_url[:60]}...")
            
            self.driver.get(job_url)
            time.sleep(random.uniform(2, 3))
            
            # Wait for job description to load
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation='jobAdDetails'], div.job-description"))
                )
            except:
                logger.warning("Could not find job description element")
                return ""
            
            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try multiple selectors for job description
            description_selectors = [
                'div[data-automation="jobAdDetails"]',
                'div.job-description',
                'div[class*="jobdetails"]',
                'div[class*="job-detail"]',
                'article',
            ]
            
            description = ""
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    # Extract text and clean it
                    description = desc_elem.get_text(separator='\n', strip=True)
                    break
            
            if description:
                # Clean up the description
                description = '\n'.join(line.strip() for line in description.split('\n') if line.strip())
                logger.info(f"Successfully fetched description ({len(description)} chars)")
                return description
            else:
                logger.warning("No description found on page")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to fetch job description: {e}")
            return ""
    
    def enrich_jobs_with_descriptions(self, jobs: List[Dict], max_jobs: int = 50) -> List[Dict]:
        """
        Enrich job listings with full descriptions.
        Note: This method assumes the driver is still active from scrape_jobs(keep_driver=True).
        
        Args:
            jobs: List of job dictionaries
            max_jobs: Maximum number of jobs to fetch descriptions for (to avoid long runtime)
            
        Returns:
            Updated list of jobs with descriptions
        """
        if not self.driver:
            logger.warning("Driver not initialized, cannot fetch descriptions")
            return jobs
        
        logger.info(f"Enriching {min(len(jobs), max_jobs)} jobs with full descriptions...")
        
        enriched_count = 0
        for i, job in enumerate(jobs[:max_jobs]):
            try:
                description = self.fetch_job_description(job['url'])
                job['description'] = description
                
                if description:
                    enriched_count += 1
                
                # Add a delay to avoid overwhelming the server
                if i < len(jobs) - 1:  # Don't delay after last job
                    time.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                logger.error(f"Failed to enrich job {job.get('title', 'Unknown')}: {e}")
                job['description'] = ""
                continue
        
        logger.info(f"Successfully enriched {enriched_count}/{min(len(jobs), max_jobs)} jobs with descriptions")
        return jobs
    
    def close_driver(self):
        """Close the Selenium driver if it's open."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
