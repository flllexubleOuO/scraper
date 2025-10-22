import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the job scraper application."""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///job_scraper.db')
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Scraping Configuration
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', 2))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # Application Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Scheduling
    SCRAPE_TIME = os.getenv('SCRAPE_TIME', '09:00')
    TIMEZONE = os.getenv('TIMEZONE', 'Pacific/Auckland')
    
    # LLM Configuration
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 1000))
    
    # Seek NZ Configuration
    SEEK_BASE_URL = 'https://www.seek.co.nz'
    SEEK_IT_CATEGORY = 'information-technology'
    
    # Job Categories for Classification
    JOB_CATEGORIES = [
        'Software Developer (Frontend)',
        'Software Developer (Backend)', 
        'Software Developer (Full-stack)',
        'Data Analyst',
        'Data Scientist',
        'Data Engineer',
        'DevOps Engineer',
        'Cloud Engineer',
        'QA Engineer',
        'Test Engineer',
        'Security Engineer',
        'IT Support',
        'System Administrator',
        'Product Manager',
        'Project Manager',
        'Other IT roles'
    ]
