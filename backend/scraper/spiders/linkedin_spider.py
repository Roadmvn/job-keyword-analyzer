"""
Spider LinkedIn pour le scraping d'offres d'emploi
ATTENTION: LinkedIn a des protections anti-bot strictes
Utiliser avec précaution et respecter les limites de débit
"""

import scrapy
import json
import re
from urllib.parse import urlencode, urljoin
from itemloaders import ItemLoader
from datetime import datetime, timedelta
from scraper.spiders.base_spider import BaseJobSpider
from scraper.items import JobOfferItem


class LinkedinSpider(BaseJobSpider):
    """Spider pour scraper les offres d'emploi sur LinkedIn"""
    
    name = 'linkedin'
    allowed_domains = ['linkedin.com']
    
    # URL de base pour LinkedIn
    base_url = 'https://www.linkedin.com'
    search_url = 'https://www.linkedin.com/jobs/search'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 5,  # Délai plus long pour LinkedIn
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Un seul à la fois
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False,  # LinkedIn robots.txt est restrictif
    }
    
    def get_start_urls(self):
        """Génère les URLs de départ pour LinkedIn"""
        params = {
            'keywords': self.search_query,
            'location': self.location,
            'sortBy': 'DD',  # Date desc
            'f_TPR': 'r86400',  # Dernières 24h
            'start': 0
        }
        
        search_url = f"{self.search_url}?{urlencode(params)}"
        return [search_url]
    
    def start_requests(self):
        """Requêtes de départ avec headers appropriés"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        for url in self.get_start_urls():
            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                meta={'page': 1}
            )
    
    def parse(self, response):
        """Parse la page de résultats de recherche LinkedIn"""
        self.logger.info(f"Parsing LinkedIn page {response.meta.get('page', 1)}: {response.url}")
        
        # Vérifier si on est bloqué
        if self.is_blocked(response):
            self.logger.error("LinkedIn a bloqué notre requête. Arrêt du spider.")
            return
        
        # Sélecteurs pour les offres d'emploi LinkedIn
        job_cards = response.css('[data-job-id]')
        
        if not job_cards:
            # Essayer un autre sélecteur
            job_cards = response.css('.job-search-card')
        
        if not job_cards:
            self.logger.warning(f"Aucune offre trouvée sur {response.url}")
            # Log du HTML pour debug
            self.logger.debug(f"HTML response: {response.text[:500]}")
            return
        
        self.logger.info(f"Trouvé {len(job_cards)} offres LinkedIn sur cette page")
        
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
                    },
                    headers={
                        'Referer': response.url,
                    }
                )
        
        # Gérer la pagination avec précaution
        yield from self.handle_pagination(response)
    
    def is_blocked(self, response):
        """Vérifie si LinkedIn nous a bloqué"""
        blocked_indicators = [
            'challenge' in response.url.lower(),
            'captcha' in response.text.lower(),
            'authwall' in response.text.lower(),
            response.status == 429,  # Too Many Requests
            response.status == 403,  # Forbidden
        ]
        
        return any(blocked_indicators)
    
    def extract_job_url(self, job_card, response):
        """Extrait l'URL d'une offre depuis sa carte"""
        # Plusieurs sélecteurs possibles pour LinkedIn
        selectors = [
            '.job-search-card__title-link::attr(href)',
            '[data-control-name="job_search_job_title"]::attr(href)',
            'h3 a::attr(href)',
            '.job-card-list__title::attr(href)'
        ]
        
        for selector in selectors:
            relative_url = job_card.css(selector).get()
            if relative_url:
                return urljoin(response.url, relative_url)
        
        return None
    
    def extract_job_card_data(self, job_card):
        """Extrait les données basiques depuis la carte d'offre LinkedIn"""
        data = {}
        
        # Titre du poste
        title_selectors = [
            '.job-search-card__title::text',
            'h3 a::text',
            '.job-card-list__title::text'
        ]
        
        for selector in title_selectors:
            title = job_card.css(selector).get()
            if title:
                data['title'] = title.strip()
                break
        
        # Entreprise
        company_selectors = [
            '.job-search-card__subtitle-link::text',
            '.job-card-container__company-name::text',
            '.job-card-list__company-name::text'
        ]
        
        for selector in company_selectors:
            company = job_card.css(selector).get()
            if company:
                data['company'] = company.strip()
                break
        
        # Localisation
        location_selectors = [
            '.job-search-card__location::text',
            '.job-card-container__metadata-item::text',
            '.job-card-list__metadata::text'
        ]
        
        for selector in location_selectors:
            location = job_card.css(selector).get()
            if location and not any(word in location.lower() for word in ['promoted', 'sponsorisé']):
                data['location'] = location.strip()
                break
        
        # Date de publication
        date_selectors = [
            '.job-search-card__listdate::text',
            'time::attr(datetime)',
            '.job-card-list__footer-wrapper time::text'
        ]
        
        for selector in date_selectors:
            date_posted = job_card.css(selector).get()
            if date_posted:
                data['posted_date'] = self.parse_linkedin_date(date_posted)
                break
        
        # ID du job
        job_id = job_card.css('::attr(data-job-id)').get()
        if job_id:
            data['external_id'] = job_id
        
        return data
    
    def parse_job(self, response):
        """Parse une page d'offre individuelle LinkedIn"""
        self.logger.debug(f"Parsing LinkedIn job: {response.url}")
        
        # Vérifier si on est bloqué
        if self.is_blocked(response):
            self.logger.error(f"Bloqué sur {response.url}")
            return
        
        loader = ItemLoader(item=JobOfferItem(), response=response)
        
        # Données de base
        loader.add_value('url', response.url)
        loader.add_value('source', 'linkedin')
        loader.add_value('scraped_at', datetime.now().isoformat())
        
        if self.scraping_job_id:
            loader.add_value('scraping_job_id', self.scraping_job_id)
        
        # Récupérer les données de la carte
        job_data = response.meta.get('job_data', {})
        
        # Informations principales
        if 'title' in job_data:
            loader.add_value('title', job_data['title'])
        else:
            title_selectors = [
                'h1::text',
                '.job-details-jobs-unified-top-card__job-title::text',
                '.t-24::text'
            ]
            for selector in title_selectors:
                title = response.css(selector).get()
                if title:
                    loader.add_value('title', title)
                    break
        
        if 'company' in job_data:
            loader.add_value('company', job_data['company'])
        else:
            company_selectors = [
                '.job-details-jobs-unified-top-card__company-name a::text',
                '.job-details-jobs-unified-top-card__company-name::text',
                '.jobs-unified-top-card__company-name::text'
            ]
            for selector in company_selectors:
                company = response.css(selector).get()
                if company:
                    loader.add_value('company', company)
                    break
        
        if 'location' in job_data:
            loader.add_value('location', job_data['location'])
        else:
            location_selectors = [
                '.job-details-jobs-unified-top-card__bullet::text',
                '.jobs-unified-top-card__bullet::text'
            ]
            for selector in location_selectors:
                location = response.css(selector).get()
                if location:
                    loader.add_value('location', location)
                    break
        
        if 'external_id' in job_data:
            loader.add_value('external_id', job_data['external_id'])
        else:
            # Extraire l'ID depuis l'URL
            job_id = self.extract_id_from_url(response.url)
            if job_id:
                loader.add_value('external_id', job_id)
        
        # Description du poste
        description_selectors = [
            '.jobs-box__html-content *::text',
            '.job-details-jobs-unified-top-card__job-description *::text',
            '.jobs-description-content__text *::text'
        ]
        
        for selector in description_selectors:
            description_elements = response.css(selector).getall()
            if description_elements:
                description = ' '.join(description_elements)
                loader.add_value('description', description)
                break
        
        # Informations sur l'emploi (type, niveau, etc.)
        job_insights = response.css('.job-details-jobs-unified-top-card__job-insight::text').getall()
        for insight in job_insights:
            insight = insight.strip().lower()
            if 'temps plein' in insight or 'full-time' in insight:
                loader.add_value('job_type', 'Temps plein')
            elif 'temps partiel' in insight or 'part-time' in insight:
                loader.add_value('job_type', 'Temps partiel')
            elif 'stage' in insight or 'internship' in insight:
                loader.add_value('job_type', 'Stage')
            elif 'contract' in insight or 'contrat' in insight:
                loader.add_value('contract_type', 'Contrat')
        
        # Niveau d'expérience
        experience_indicators = response.css('.job-details-jobs-unified-top-card__job-insight--highlight::text').getall()
        for exp in experience_indicators:
            exp = exp.strip().lower()
            if 'débutant' in exp or 'entry' in exp:
                loader.add_value('experience_level', 'Junior')
            elif 'senior' in exp:
                loader.add_value('experience_level', 'Senior')
            elif 'manager' in exp or 'lead' in exp:
                loader.add_value('experience_level', 'Lead')
        
        # Date de publication
        if 'posted_date' in job_data:
            loader.add_value('posted_date', job_data['posted_date'])
        
        # URL de candidature
        apply_selectors = [
            '.jobs-apply-button::attr(href)',
            '.jobs-s-apply button::attr(data-job-id)'
        ]
        
        for selector in apply_selectors:
            apply_info = response.css(selector).get()
            if apply_info:
                if apply_info.startswith('http'):
                    loader.add_value('apply_url', apply_info)
                else:
                    # Construire l'URL de candidature LinkedIn
                    apply_url = f"https://www.linkedin.com/jobs/view/{apply_info}/"
                    loader.add_value('apply_url', apply_url)
                break
        
        item = loader.load_item()
        
        if self.is_valid_job(item):
            self.jobs_scraped += 1
            self.logger.info(f"Job LinkedIn {self.jobs_scraped}: {item.get('title', 'N/A')} - {item.get('company', 'N/A')}")
            yield item
        else:
            self.logger.warning(f"Job LinkedIn invalide: {response.url}")
    
    def get_next_page_url(self, response):
        """Extrait l'URL de la page suivante pour LinkedIn"""
        # LinkedIn utilise une pagination par offset
        next_selectors = [
            'button[aria-label="Voir plus d\'offres d\'emploi"]::attr(data-page-num)',
            '.artdeco-pagination__button--next::attr(href)',
            '[data-test-pagination-page-btn="next"]::attr(href)'
        ]
        
        for selector in next_selectors:
            next_page = response.css(selector).get()
            if next_page:
                if next_page.startswith('http'):
                    return next_page
                else:
                    return urljoin(response.url, next_page)
        
        # Méthode alternative: construire manuellement l'URL suivante
        current_page = response.meta.get('page', 1)
        if current_page < self.max_pages:
            current_url = response.url
            # Remplacer ou ajouter le paramètre start
            if 'start=' in current_url:
                # Calculer le nouvel offset (25 jobs par page généralement)
                new_start = current_page * 25
                import re
                new_url = re.sub(r'start=\d+', f'start={new_start}', current_url)
                return new_url
        
        return None
    
    def parse_linkedin_date(self, date_str):
        """Parse les dates au format LinkedIn"""
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        if 'il y a' in date_str:
            if 'jour' in date_str:
                days_match = re.search(r'(\d+)', date_str)
                if days_match:
                    days = int(days_match.group(1))
                    return (now - timedelta(days=days)).strftime('%Y-%m-%d')
            elif 'semaine' in date_str:
                weeks_match = re.search(r'(\d+)', date_str)
                if weeks_match:
                    weeks = int(weeks_match.group(1))
                    return (now - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
            elif 'mois' in date_str:
                months_match = re.search(r'(\d+)', date_str)
                if months_match:
                    months = int(months_match.group(1))
                    return (now - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        return date_str
    
    def should_continue_scraping(self):
        """LinkedIn a des limites strictes, être plus conservateur"""
        if self.current_page > min(self.max_pages, 3):  # Max 3 pages pour LinkedIn
            self.logger.info(f"Limite LinkedIn atteinte: {min(self.max_pages, 3)} pages")
            return False
        
        if self.jobs_scraped >= min(self.max_jobs, 50):  # Max 50 jobs pour LinkedIn
            self.logger.info(f"Limite LinkedIn atteinte: {min(self.max_jobs, 50)} jobs")
            return False
        
        return True