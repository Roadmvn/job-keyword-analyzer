"""
Spider de base pour le scraping d'offres d'emploi
Contient les fonctionnalités communes à tous les spiders
"""

import scrapy
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from itemloaders import ItemLoader
from scraper.items import JobOfferItem


class BaseJobSpider(scrapy.Spider):
    """Spider de base pour le scraping d'offres d'emploi"""
    
    name = 'base_job_spider'
    
    # Configuration par défaut
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    }
    
    def __init__(self, search_query=None, location=None, max_pages=5, scraping_job_id=None, *args, **kwargs):
        super(BaseJobSpider, self).__init__(*args, **kwargs)
        
        # Paramètres de recherche
        self.search_query = search_query or "développeur"
        self.location = location or "France"
        self.max_pages = int(max_pages) if max_pages else 5
        self.scraping_job_id = scraping_job_id
        
        # Compteurs
        self.current_page = 1
        self.jobs_scraped = 0
        self.max_jobs = 500  # Limite de sécurité
        
        # Configuration du logging
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        self.logger.info(f"Initialisation du spider {self.name}")
        self.logger.info(f"Recherche: '{self.search_query}' à '{self.location}'")
        self.logger.info(f"Max pages: {self.max_pages}")
    
    def start_requests(self):
        """Génère les requêtes initiales"""
        urls = self.get_start_urls()
        
        for url in urls:
            self.logger.info(f"Démarrage du scraping: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'page': 1}
            )
    
    def get_start_urls(self):
        """À surcharger dans les spiders enfants"""
        raise NotImplementedError("Les spiders enfants doivent implémenter get_start_urls()")
    
    def parse(self, response):
        """Parser principal - à surcharger dans les spiders enfants"""
        raise NotImplementedError("Les spiders enfants doivent implémenter parse()")
    
    def parse_job(self, response):
        """Parse une page d'offre individuelle"""
        self.logger.debug(f"Parsing job: {response.url}")
        
        loader = ItemLoader(item=JobOfferItem(), response=response)
        
        # URL de l'offre
        loader.add_value('url', response.url)
        loader.add_value('source', self.name)
        loader.add_value('scraped_at', datetime.now().isoformat())
        
        if self.scraping_job_id:
            loader.add_value('scraping_job_id', self.scraping_job_id)
        
        # Extraction des données - méthodes à surcharger
        self.extract_basic_info(loader, response)
        self.extract_job_details(loader, response)
        self.extract_company_info(loader, response)
        self.extract_salary_info(loader, response)
        
        item = loader.load_item()
        
        # Validation basique
        if self.is_valid_job(item):
            self.jobs_scraped += 1
            self.logger.info(f"Job {self.jobs_scraped} scrapé: {item.get('title', 'N/A')}")
            yield item
        else:
            self.logger.warning(f"Job invalide ignoré: {response.url}")
    
    def extract_basic_info(self, loader, response):
        """Extraction des informations de base - à surcharger"""
        pass
    
    def extract_job_details(self, loader, response):
        """Extraction des détails du poste - à surcharger"""
        pass
    
    def extract_company_info(self, loader, response):
        """Extraction des informations de l'entreprise - à surcharger"""
        pass
    
    def extract_salary_info(self, loader, response):
        """Extraction des informations de salaire - à surcharger"""
        pass
    
    def is_valid_job(self, item):
        """Valide qu'un job contient les informations minimales requises"""
        required_fields = ['title', 'company', 'url']
        
        for field in required_fields:
            if not item.get(field):
                return False
        
        return True
    
    def should_continue_scraping(self):
        """Détermine si le scraping doit continuer"""
        if self.current_page > self.max_pages:
            self.logger.info(f"Limite de pages atteinte: {self.max_pages}")
            return False
        
        if self.jobs_scraped >= self.max_jobs:
            self.logger.info(f"Limite de jobs atteinte: {self.max_jobs}")
            return False
        
        return True
    
    def get_next_page_url(self, response):
        """Extrait l'URL de la page suivante - à surcharger"""
        return None
    
    def handle_pagination(self, response):
        """Gère la pagination"""
        if not self.should_continue_scraping():
            return
        
        next_page_url = self.get_next_page_url(response)
        
        if next_page_url:
            self.current_page += 1
            full_url = urljoin(response.url, next_page_url)
            
            self.logger.info(f"Page suivante: {self.current_page} - {full_url}")
            
            yield scrapy.Request(
                url=full_url,
                callback=self.parse,
                meta={'page': self.current_page}
            )
    
    def clean_text(self, text):
        """Nettoie le texte extrait"""
        if not text:
            return ""
        
        # Supprimer les espaces multiples et les retours à la ligne
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def extract_id_from_url(self, url):
        """Extrait un ID depuis une URL"""
        # Pattern générique pour extraire des IDs numériques
        patterns = [
            r'/(\d+)/?$',  # ID à la fin de l'URL
            r'id=(\d+)',   # Paramètre ID
            r'job[_-]?(\d+)',  # job-123 ou job_123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def closed(self, reason):
        """Appelé quand le spider se ferme"""
        self.logger.info(f"Spider fermé. Raison: {reason}")
        self.logger.info(f"Total jobs scrapés: {self.jobs_scraped}")
        self.logger.info(f"Pages parcourues: {self.current_page}")