# Scrapy settings for job scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html

BOT_NAME = 'job_scraper'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Respect robots.txt (can be disabled for certain sites if needed)
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy
CONCURRENT_REQUESTS = 16

# Configure delays for requests for the same website
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5 * DOWNLOAD_DELAY

# Configure concurrent requests per domain
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scraper.middlewares.JobScraperSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scraper.middlewares.JobScraperDownloaderMiddleware': 543,
    'scraper.middlewares.UserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'scraper.pipelines.ValidationPipeline': 300,
    'scraper.pipelines.CleaningPipeline': 400,
    'scraper.pipelines.DatabasePipeline': 500,
    'scraper.pipelines.ElasticsearchPipeline': 600,
}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 505, 500, 400, 403, 404]

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

# Custom settings
FEEDS = {
    'jobs.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 4,
    }
}

# Database configuration (loaded from environment)
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_URL = os.getenv('REDIS_URL')
ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL')

# Job scraping limits
MAX_JOBS_PER_SEARCH = 500
MAX_PAGES_PER_SEARCH = 20