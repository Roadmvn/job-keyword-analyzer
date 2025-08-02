# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.http import HtmlResponse
from fake_useragent import UserAgent
import random
import logging


class JobScraperSpiderMiddleware:
    """Middleware pour les spiders de scraping d'emploi"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        """Traite les réponses avant qu'elles n'atteignent le spider"""
        return None

    def process_spider_output(self, response, result, spider):
        """Traite les éléments retournés par le spider"""
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        """Traite les exceptions levées par le spider"""
        spider.logger.error(f"Exception dans {spider.name}: {exception}")
        pass

    def process_start_requests(self, start_requests, spider):
        """Traite les requêtes de démarrage"""
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info(f'Spider ouvert: {spider.name}')


class JobScraperDownloaderMiddleware:
    """Middleware pour les téléchargements"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        """Traite les requêtes avant téléchargement"""
        return None

    def process_response(self, request, response, spider):
        """Traite les réponses après téléchargement"""
        
        # Log des réponses avec erreur
        if response.status >= 400:
            spider.logger.warning(f"Réponse {response.status} pour {request.url}")
        
        return response

    def process_exception(self, request, exception, spider):
        """Traite les exceptions de téléchargement"""
        spider.logger.error(f"Exception de téléchargement: {exception} pour {request.url}")
        pass

    def spider_opened(self, spider):
        spider.logger.info(f'Downloader middleware ouvert: {spider.name}')


class UserAgentMiddleware(UserAgentMiddleware):
    """Middleware pour rotation des User-Agents"""
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        self.ua = UserAgent()
        self.ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent=crawler.settings.get('USER_AGENT')
        )

    def process_request(self, request, spider):
        """Assigne un User-Agent aléatoire à chaque requête"""
        try:
            # Utiliser fake_useragent
            ua = self.ua.random
        except:
            # Fallback vers notre liste prédéfinie
            ua = random.choice(self.ua_list)
        
        request.headers['User-Agent'] = ua
        return None


class ProxyMiddleware:
    """Middleware pour rotation des proxies (optionnel)"""
    
    def __init__(self):
        self.proxies = []
        # TODO: Implémenter la gestion des proxies si nécessaire
        
    def process_request(self, request, spider):
        """Assigne un proxy aléatoire (si configuré)"""
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
        return None


class RetryMiddleware:
    """Middleware personnalisé pour les tentatives"""
    
    def __init__(self, max_retry_times=3):
        self.max_retry_times = max_retry_times
        self.retry_codes = [500, 502, 503, 504, 408, 429]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            max_retry_times=crawler.settings.getint('RETRY_TIMES', 3)
        )

    def process_response(self, request, response, spider):
        """Gère les tentatives en cas d'erreur"""
        if response.status in self.retry_codes:
            retry_times = request.meta.get('retry_times', 0) + 1
            
            if retry_times <= self.max_retry_times:
                spider.logger.warning(f"Tentative {retry_times} pour {request.url}")
                new_request = request.copy()
                new_request.meta['retry_times'] = retry_times
                new_request.dont_filter = True
                return new_request
            else:
                spider.logger.error(f"Max tentatives atteintes pour {request.url}")
        
        return response


class DelayMiddleware:
    """Middleware pour gérer les délais personnalisés"""
    
    def __init__(self):
        self.delays = {
            'linkedin.com': 5,  # Délai plus long pour LinkedIn
            'indeed.fr': 2,     # Délai standard pour Indeed
            'indeed.com': 2,
        }

    def process_request(self, request, spider):
        """Applique des délais spécifiques par domaine"""
        from urllib.parse import urlparse
        
        domain = urlparse(request.url).netloc
        
        # Chercher le délai approprié
        for site, delay in self.delays.items():
            if site in domain:
                request.meta['download_delay'] = delay
                break
        
        return None