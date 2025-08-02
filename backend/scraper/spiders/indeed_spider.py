"""
Spider Indeed pour le scraping d'offres d'emploi
Utilise l'API de recherche Indeed pour collecter les offres
"""

import scrapy
import json
import re
from urllib.parse import urlencode, urljoin
from itemloaders import ItemLoader
from datetime import datetime, timedelta
from scraper.spiders.base_spider import BaseJobSpider
from scraper.items import JobOfferItem


class IndeedSpider(BaseJobSpider):
    """Spider pour scraper les offres d'emploi sur Indeed France"""
    
    name = 'indeed'
    allowed_domains = ['indeed.fr', 'indeed.com']
    
    # URL de base pour Indeed France
    base_url = 'https://fr.indeed.com'
    search_url = 'https://fr.indeed.com/jobs'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.5,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    def get_start_urls(self):
        """Génère les URLs de départ pour Indeed"""
        params = {
            'q': self.search_query,
            'l': self.location,
            'sort': 'date',  # Trier par date
            'limit': 50,     # Limite par page
            'start': 0       # Début de pagination
        }
        
        search_url = f"{self.search_url}?{urlencode(params)}"
        return [search_url]
    
    def parse(self, response):
        """Parse la page de résultats de recherche Indeed"""
        self.logger.info(f"Parsing page {response.meta.get('page', 1)}: {response.url}")
        
        # Sélecteurs pour les offres d'emploi
        job_cards = response.css('[data-jk]')
        
        if not job_cards:
            self.logger.warning(f"Aucune offre trouvée sur {response.url}")
            return
        
        self.logger.info(f"Trouvé {len(job_cards)} offres sur cette page")
        
        # Parser chaque offre
        for job_card in job_cards:
            job_url = self.extract_job_url(job_card, response)
            
            if job_url:
                # Extraire les informations de base depuis la carte
                job_data = self.extract_job_card_data(job_card)
                
                yield scrapy.Request(
                    url=job_url,
                    callback=self.parse_job,
                    meta={
                        'job_data': job_data,
                        'page': response.meta.get('page', 1)
                    }
                )
        
        # Gérer la pagination
        yield from self.handle_pagination(response)
    
    def extract_job_url(self, job_card, response):
        """Extrait l'URL d'une offre depuis sa carte"""
        # Indeed utilise des liens relatifs
        relative_url = job_card.css('h2.jobTitle a::attr(href)').get()
        
        if relative_url:
            return urljoin(response.url, relative_url)
        
        return None
    
    def extract_job_card_data(self, job_card):
        """Extrait les données basiques depuis la carte d'offre"""
        data = {}
        
        # Titre du poste
        title = job_card.css('h2.jobTitle a span::text').get()
        if title:
            data['title'] = title.strip()
        
        # Entreprise
        company = job_card.css('span.companyName a::text').get()
        if not company:
            company = job_card.css('span.companyName::text').get()
        if company:
            data['company'] = company.strip()
        
        # Localisation
        location = job_card.css('[data-testid="job-location"]::text').get()
        if location:
            data['location'] = location.strip()
        
        # Salaire (si présent)
        salary = job_card.css('[data-testid="attribute_snippet_testid"]::text').get()
        if salary:
            data['salary_raw'] = salary.strip()
        
        # Date de publication
        date_posted = job_card.css('[data-testid="myJobsStateDate"]::text').get()
        if date_posted:
            data['posted_date'] = self.parse_indeed_date(date_posted)
        
        # ID du job (data-jk)
        job_id = job_card.css('::attr(data-jk)').get()
        if job_id:
            data['external_id'] = job_id
        
        return data
    
    def parse_job(self, response):
        """Parse une page d'offre individuelle"""
        self.logger.debug(f"Parsing job: {response.url}")
        
        loader = ItemLoader(item=JobOfferItem(), response=response)
        
        # Données de base
        loader.add_value('url', response.url)
        loader.add_value('source', 'indeed')
        loader.add_value('scraped_at', datetime.now().isoformat())
        
        if self.scraping_job_id:
            loader.add_value('scraping_job_id', self.scraping_job_id)
        
        # Récupérer les données de la carte
        job_data = response.meta.get('job_data', {})
        
        # Informations principales
        if 'title' in job_data:
            loader.add_value('title', job_data['title'])
        else:
            loader.add_css('title', 'h1::text')
        
        if 'company' in job_data:
            loader.add_value('company', job_data['company'])
        else:
            loader.add_css('company', '[data-testid="inlineHeader-companyName"] a::text')
        
        if 'location' in job_data:
            loader.add_value('location', job_data['location'])
        else:
            loader.add_css('location', '[data-testid="job-location"]::text')
        
        if 'external_id' in job_data:
            loader.add_value('external_id', job_data['external_id'])
        else:
            # Extraire l'ID depuis l'URL
            job_id = self.extract_id_from_url(response.url)
            if job_id:
                loader.add_value('external_id', job_id)
        
        # Description du poste
        description_elements = response.css('#jobDescriptionText *::text').getall()
        if description_elements:
            description = ' '.join(description_elements)
            loader.add_value('description', description)
        
        # Informations de salaire
        if 'salary_raw' in job_data:
            salary_info = self.parse_salary(job_data['salary_raw'])
            if salary_info:
                loader.add_value('salary_min', salary_info.get('min'))
                loader.add_value('salary_max', salary_info.get('max'))
                loader.add_value('salary_currency', salary_info.get('currency', 'EUR'))
        
        # Type de contrat et autres infos
        job_details = response.css('[data-testid="job-details-section"] span::text').getall()
        for detail in job_details:
            detail = detail.strip().lower()
            if 'cdi' in detail or 'permanent' in detail:
                loader.add_value('contract_type', 'CDI')
            elif 'cdd' in detail or 'temporary' in detail:
                loader.add_value('contract_type', 'CDD')
            elif 'stage' in detail or 'internship' in detail:
                loader.add_value('contract_type', 'Stage')
            elif 'freelance' in detail or 'indépendant' in detail:
                loader.add_value('contract_type', 'Freelance')
        
        # Télétravail
        if response.css('*:contains("télétravail"):contains("remote")'):
            loader.add_value('remote_work', 'Oui')
        
        # Date de publication
        if 'posted_date' in job_data:
            loader.add_value('posted_date', job_data['posted_date'])
        
        # URL de candidature
        apply_button = response.css('[data-testid="apply-button-container"] a::attr(href)').get()
        if apply_button:
            loader.add_value('apply_url', urljoin(response.url, apply_button))
        
        item = loader.load_item()
        
        if self.is_valid_job(item):
            self.jobs_scraped += 1
            self.logger.info(f"Job Indeed {self.jobs_scraped}: {item.get('title', 'N/A')} - {item.get('company', 'N/A')}")
            yield item
        else:
            self.logger.warning(f"Job Indeed invalide: {response.url}")
    
    def get_next_page_url(self, response):
        """Extrait l'URL de la page suivante"""
        # Indeed utilise une pagination par offset
        next_page = response.css('a[aria-label="Next Page"]::attr(href)').get()
        
        if next_page:
            return urljoin(response.url, next_page)
        
        return None
    
    def parse_indeed_date(self, date_str):
        """Parse les dates au format Indeed"""
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        if 'aujourd\'hui' in date_str or 'today' in date_str:
            return now.strftime('%Y-%m-%d')
        elif 'hier' in date_str or 'yesterday' in date_str:
            return (now - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'jour' in date_str or 'day' in date_str:
            # Extrait le nombre de jours
            days_match = re.search(r'(\d+)', date_str)
            if days_match:
                days = int(days_match.group(1))
                return (now - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return date_str
    
    def parse_salary(self, salary_str):
        """Parse les informations de salaire Indeed"""
        if not salary_str:
            return None
        
        salary_str = salary_str.replace(' ', '').replace(',', '')
        
        # Pattern pour capturer les salaires
        patterns = [
            r'(\d+)(?:€|euros?)?\s*-\s*(\d+)(?:€|euros?)?',  # Range: 30000 - 40000€
            r'(\d+)(?:k|K)?\s*€',  # Single: 35k€ ou 35000€
            r'(\d+)\s*(?:€|euros?)',  # Single: 35000 euros
        ]
        
        result = {}
        
        for pattern in patterns:
            match = re.search(pattern, salary_str)
            if match:
                if len(match.groups()) == 2:
                    # Range de salaire
                    result['min'] = int(match.group(1))
                    result['max'] = int(match.group(2))
                else:
                    # Salaire unique
                    salary = int(match.group(1))
                    # Si contient 'k' ou 'K', multiplier par 1000
                    if 'k' in salary_str.lower():
                        salary *= 1000
                    result['min'] = salary
                    result['max'] = salary
                
                result['currency'] = 'EUR'
                break
        
        return result if result else None