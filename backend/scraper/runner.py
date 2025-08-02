"""
Runner pour exécuter les spiders Scrapy dans un contexte asynchrone
Intégration avec RQ pour les tâches de scraping
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
import multiprocessing as mp
from datetime import datetime


class ScrapyRunner:
    """Runner pour exécuter les spiders Scrapy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configuration Scrapy
        os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'backend.scraper.settings')
        self.settings = get_project_settings()
        
        # Configuration du logging
        configure_logging(self.settings)
        
        self.runner = CrawlerRunner(self.settings)
        
        # Spiders disponibles
        self.available_spiders = {
            'indeed': 'backend.scraper.spiders.indeed_spider.IndeedSpider',
            'linkedin': 'backend.scraper.spiders.linkedin_spider.LinkedinSpider'
        }
    
    def run_spider(self, 
                   spider_name: str, 
                   search_query: str = "développeur",
                   location: str = "France", 
                   max_pages: int = 5,
                   scraping_job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Lance un spider de scraping
        
        Args:
            spider_name: Nom du spider ('indeed', 'linkedin')
            search_query: Requête de recherche
            location: Localisation
            max_pages: Nombre maximum de pages à scraper
            scraping_job_id: ID du job de scraping pour tracking
        
        Returns:
            Dict avec les résultats du scraping
        """
        
        if spider_name not in self.available_spiders:
            raise ValueError(f"Spider '{spider_name}' non disponible. Spiders disponibles: {list(self.available_spiders.keys())}")
        
        self.logger.info(f"Démarrage du spider {spider_name}")
        self.logger.info(f"Paramètres: query='{search_query}', location='{location}', pages={max_pages}")
        
        try:
            # Paramètres du spider
            spider_kwargs = {
                'search_query': search_query,
                'location': location,
                'max_pages': max_pages,
                'scraping_job_id': scraping_job_id
            }
            
            # Lancer le spider dans un processus séparé pour éviter les conflits Twisted
            result = self._run_spider_in_process(spider_name, spider_kwargs)
            
            return {
                'success': True,
                'spider': spider_name,
                'jobs_scraped': result.get('jobs_scraped', 0),
                'pages_scraped': result.get('pages_scraped', 0),
                'duration': result.get('duration', 0),
                'message': f"Scraping {spider_name} terminé avec succès"
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping {spider_name}: {e}")
            return {
                'success': False,
                'spider': spider_name,
                'error': str(e),
                'message': f"Erreur lors du scraping {spider_name}"
            }
    
    def _run_spider_in_process(self, spider_name: str, spider_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute le spider dans un processus séparé"""
        
        def run_spider_process(spider_name, spider_kwargs, result_queue):
            """Fonction exécutée dans le processus séparé"""
            try:
                from scrapy.crawler import CrawlerProcess
                from scrapy.utils.project import get_project_settings
                
                # Configuration du processus
                settings = get_project_settings()
                process = CrawlerProcess(settings)
                
                # Stats du spider
                stats = {
                    'jobs_scraped': 0,
                    'pages_scraped': 0,
                    'start_time': datetime.now()
                }
                
                # Import dynamique du spider
                if spider_name == 'indeed':
                    from backend.scraper.spiders.indeed_spider import IndeedSpider
                    spider_class = IndeedSpider
                elif spider_name == 'linkedin':
                    from backend.scraper.spiders.linkedin_spider import LinkedinSpider
                    spider_class = LinkedinSpider
                else:
                    raise ValueError(f"Spider inconnu: {spider_name}")
                
                # Démarrer le crawling
                process.crawl(spider_class, **spider_kwargs)
                process.start()
                
                # Calculer la durée
                end_time = datetime.now()
                duration = (end_time - stats['start_time']).total_seconds()
                
                result = {
                    'jobs_scraped': getattr(process.crawlers[0].spider, 'jobs_scraped', 0),
                    'pages_scraped': getattr(process.crawlers[0].spider, 'current_page', 0),
                    'duration': duration
                }
                
                result_queue.put(result)
                
            except Exception as e:
                result_queue.put({'error': str(e)})
        
        # Créer et lancer le processus
        result_queue = mp.Queue()
        process = mp.Process(
            target=run_spider_process, 
            args=(spider_name, spider_kwargs, result_queue)
        )
        
        process.start()
        process.join(timeout=300)  # Timeout de 5 minutes
        
        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutError("Le spider a dépassé le timeout de 5 minutes")
        
        # Récupérer le résultat
        if not result_queue.empty():
            result = result_queue.get()
            if 'error' in result:
                raise Exception(result['error'])
            return result
        else:
            raise Exception("Aucun résultat retourné par le spider")
    
    def get_available_spiders(self) -> list:
        """Retourne la liste des spiders disponibles"""
        return list(self.available_spiders.keys())
    
    def validate_spider_params(self, spider_name: str, params: Dict[str, Any]) -> bool:
        """Valide les paramètres d'un spider"""
        if spider_name not in self.available_spiders:
            return False
        
        required_params = ['search_query']
        for param in required_params:
            if param not in params or not params[param]:
                return False
        
        return True


# Fonction utilitaire pour RQ
def run_scraping_job(spider_name: str, 
                    search_query: str,
                    location: str = "France",
                    max_pages: int = 5,
                    scraping_job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fonction wrapper pour RQ
    Exécute un job de scraping en arrière-plan
    """
    runner = ScrapyRunner()
    return runner.run_spider(
        spider_name=spider_name,
        search_query=search_query,
        location=location,
        max_pages=max_pages,
        scraping_job_id=scraping_job_id
    )


if __name__ == "__main__":
    # Test du runner
    runner = ScrapyRunner()
    
    print("Spiders disponibles:", runner.get_available_spiders())
    
    # Test Indeed
    result = runner.run_spider(
        spider_name="indeed",
        search_query="python développeur",
        location="Paris",
        max_pages=2
    )
    
    print("Résultat Indeed:", result)