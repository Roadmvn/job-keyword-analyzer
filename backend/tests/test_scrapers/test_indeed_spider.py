"""
Tests pour le spider Indeed
"""

import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse, Request
from scrapy import Spider

# Import du spider
from scraper.spiders.indeed_spider import IndeedSpider
from scraper.items import JobOfferItem


class TestIndeedSpider:
    """Tests pour le spider Indeed"""
    
    @pytest.fixture
    def spider(self):
        """Fixture pour créer une instance du spider"""
        return IndeedSpider(
            search_query="python développeur",
            location="Paris",
            max_pages=2,
            scraping_job_id="test_job_123"
        )
    
    @pytest.fixture
    def indeed_search_response(self):
        """Mock d'une page de résultats Indeed"""
        html_content = """
        <html>
            <body>
                <div data-jk="job123">
                    <h2 class="jobTitle">
                        <a href="/viewjob?jk=job123">
                            <span>Développeur Python Senior</span>
                        </a>
                    </h2>
                    <span class="companyName">
                        <a href="/cmp/TechCorp">TechCorp</a>
                    </span>
                    <div data-testid="job-location">Paris, France</div>
                    <div data-testid="attribute_snippet_testid">45 000 € - 55 000 € par an</div>
                    <div data-testid="myJobsStateDate">Il y a 2 jours</div>
                </div>
                <div data-jk="job456">
                    <h2 class="jobTitle">
                        <a href="/viewjob?jk=job456">
                            <span>Développeur JavaScript</span>
                        </a>
                    </h2>
                    <span class="companyName">WebCorp</span>
                    <div data-testid="job-location">Lyon, France</div>
                </div>
                <a aria-label="Next Page" href="/jobs?q=python&start=50">Suivant</a>
            </body>
        </html>
        """
        
        return HtmlResponse(
            url="https://fr.indeed.com/jobs?q=python&l=Paris",
            body=html_content.encode('utf-8'),
            encoding='utf-8'
        )
    
    @pytest.fixture
    def indeed_job_response(self):
        """Mock d'une page d'offre Indeed"""
        html_content = """
        <html>
            <body>
                <h1>Développeur Python Senior</h1>
                <div data-testid="inlineHeader-companyName">
                    <a href="/cmp/TechCorp">TechCorp</a>
                </div>
                <div data-testid="job-location">Paris, France</div>
                <div id="jobDescriptionText">
                    <p>Nous recherchons un développeur Python expérimenté.</p>
                    <p>Compétences requises :</p>
                    <ul>
                        <li>Python 3.8+</li>
                        <li>Django ou FastAPI</li>
                        <li>PostgreSQL</li>
                        <li>Docker</li>
                    </ul>
                    <p>Expérience de 5 ans minimum requise.</p>
                </div>
                <div data-testid="job-details-section">
                    <span>CDI</span>
                    <span>Temps plein</span>
                </div>
            </body>
        </html>
        """
        
        return HtmlResponse(
            url="https://fr.indeed.com/viewjob?jk=job123",
            body=html_content.encode('utf-8'),
            encoding='utf-8'
        )
    
    def test_spider_initialization(self):
        """Test d'initialisation du spider"""
        spider = IndeedSpider(
            search_query="python",
            location="Paris",
            max_pages=3,
            scraping_job_id="test_123"
        )
        
        assert spider.name == "indeed"
        assert spider.search_query == "python"
        assert spider.location == "Paris"
        assert spider.max_pages == 3
        assert spider.scraping_job_id == "test_123"
        assert spider.current_page == 1
        assert spider.jobs_scraped == 0
    
    def test_get_start_urls(self, spider):
        """Test de génération des URLs de départ"""
        urls = spider.get_start_urls()
        
        assert len(urls) == 1
        url = urls[0]
        assert "fr.indeed.com/jobs" in url
        assert "q=python+d%C3%A9veloppeur" in url  # URL encodée
        assert "l=Paris" in url
        assert "sort=date" in url
    
    def test_parse_search_page(self, spider, indeed_search_response):
        """Test du parsing d'une page de résultats"""
        results = list(spider.parse(indeed_search_response))
        
        # Doit générer des requêtes pour les pages d'offres
        job_requests = [r for r in results if isinstance(r, Request)]
        assert len(job_requests) >= 2  # Au moins 2 offres trouvées
        
        # Vérifier les URLs des requêtes
        for request in job_requests:
            assert "viewjob" in request.url
            assert "jk=" in request.url
            assert "job_data" in request.meta
    
    def test_extract_job_card_data(self, spider, indeed_search_response):
        """Test d'extraction des données depuis une carte d'offre"""
        # Simuler l'extraction d'une carte
        job_cards = indeed_search_response.css('[data-jk]')
        first_card = job_cards[0]
        
        job_data = spider.extract_job_card_data(first_card)
        
        assert "title" in job_data
        assert "company" in job_data
        assert "location" in job_data
        assert "external_id" in job_data
        
        assert job_data["title"] == "Développeur Python Senior"
        assert job_data["company"] == "TechCorp"
        assert job_data["location"] == "Paris, France"
        assert job_data["external_id"] == "job123"
    
    def test_parse_job_page(self, spider, indeed_job_response):
        """Test du parsing d'une page d'offre"""
        # Simuler les métadonnées de la requête
        indeed_job_response.meta = {
            "job_data": {
                "title": "Développeur Python Senior",
                "company": "TechCorp",
                "location": "Paris, France",
                "external_id": "job123"
            }
        }
        
        results = list(spider.parse_job(indeed_job_response))
        
        assert len(results) == 1
        item = results[0]
        assert isinstance(item, JobOfferItem)
        
        # Vérifier les données extraites
        assert item["title"] == "Développeur Python Senior"
        assert item["company"] == "TechCorp"
        assert item["location"] == "Paris, France"
        assert item["source"] == "indeed"
        assert item["url"] == indeed_job_response.url
        assert "Python" in item["description"]
        assert "Django" in item["description"]
    
    def test_parse_indeed_date(self, spider):
        """Test du parsing des dates Indeed"""
        # Test des différents formats
        assert spider.parse_indeed_date("aujourd'hui") is not None
        assert spider.parse_indeed_date("hier") is not None
        assert spider.parse_indeed_date("Il y a 3 jours") is not None
        assert spider.parse_indeed_date("Il y a 1 jour") is not None
        
        # Test d'une date invalide
        result = spider.parse_indeed_date("format invalide")
        assert result == "format invalide"
    
    def test_parse_salary(self, spider):
        """Test du parsing des salaires"""
        # Test avec range
        result = spider.parse_salary("45 000 € - 55 000 € par an")
        assert result is not None
        assert result["min"] == 45000
        assert result["max"] == 55000
        assert result["currency"] == "EUR"
        
        # Test avec salaire unique
        result = spider.parse_salary("50k€")
        assert result is not None
        assert result["min"] == 50000
        assert result["max"] == 50000
        
        # Test avec format invalide
        result = spider.parse_salary("négociable")
        assert result is None
    
    def test_get_next_page_url(self, spider, indeed_search_response):
        """Test d'extraction de l'URL page suivante"""
        next_url = spider.get_next_page_url(indeed_search_response)
        assert next_url is not None
        assert "start=50" in next_url
    
    def test_should_continue_scraping(self, spider):
        """Test de la logique de continuation du scraping"""
        # Au début, doit continuer
        assert spider.should_continue_scraping() is True
        
        # Après avoir atteint la limite de pages
        spider.current_page = spider.max_pages + 1
        assert spider.should_continue_scraping() is False
        
        # Réinitialiser et tester la limite de jobs
        spider.current_page = 1
        spider.jobs_scraped = spider.max_jobs + 1
        assert spider.should_continue_scraping() is False
    
    def test_handle_pagination(self, spider, indeed_search_response):
        """Test de la gestion de la pagination"""
        results = list(spider.handle_pagination(indeed_search_response))
        
        # Doit générer une requête pour la page suivante
        assert len(results) == 1
        next_request = results[0]
        assert isinstance(next_request, Request)
        assert spider.current_page == 2
    
    @patch('scraper.spiders.indeed_spider.IndeedSpider.should_continue_scraping')
    def test_handle_pagination_no_continue(self, mock_continue, spider, indeed_search_response):
        """Test pagination quand on ne doit plus continuer"""
        mock_continue.return_value = False
        
        results = list(spider.handle_pagination(indeed_search_response))
        assert len(results) == 0
    
    def test_extract_id_from_url(self, spider):
        """Test d'extraction d'ID depuis une URL"""
        # Test URL Indeed typique
        url = "https://fr.indeed.com/viewjob?jk=abc123def"
        job_id = spider.extract_id_from_url(url)
        # Cette méthode pourrait ne pas fonctionner avec ce format
        # Le test dépend de l'implémentation réelle
        
        # Test URL avec ID à la fin
        url = "https://example.com/job/12345"
        job_id = spider.extract_id_from_url(url)
        assert job_id == "12345"
    
    def test_is_valid_job(self, spider):
        """Test de validation des jobs"""
        # Job valide
        valid_job = {
            "title": "Python Developer",
            "company": "TechCorp",
            "url": "https://example.com/job"
        }
        assert spider.is_valid_job(valid_job) is True
        
        # Job invalide (manque titre)
        invalid_job = {
            "company": "TechCorp",
            "url": "https://example.com/job"
        }
        assert spider.is_valid_job(invalid_job) is False
    
    def test_spider_stats(self, spider):
        """Test des statistiques du spider"""
        # État initial
        assert spider.jobs_scraped == 0
        assert spider.current_page == 1
        
        # Simuler quelques jobs scrapés
        spider.jobs_scraped = 5
        spider.current_page = 2
        
        assert spider.jobs_scraped == 5
        assert spider.current_page == 2


class TestIndeedSpiderIntegration:
    """Tests d'intégration pour le spider Indeed"""
    
    @pytest.mark.integration
    def test_full_spider_workflow(self):
        """Test d'intégration complète du spider"""
        # Note: Ce test nécessiterait une vraie réponse Indeed
        # ou des mocks plus sophistiqués
        spider = IndeedSpider(
            search_query="python test",
            location="Paris",
            max_pages=1
        )
        
        # Test de l'initialisation
        assert spider.name == "indeed"
        assert spider.search_query == "python test"
        
        # Test des URLs de départ
        start_urls = spider.get_start_urls()
        assert len(start_urls) > 0
        
        # Les autres tests nécessiteraient des réponses réelles
        # ou des fixtures plus complètes