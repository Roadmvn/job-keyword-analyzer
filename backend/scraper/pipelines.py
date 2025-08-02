# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import logging
import hashlib
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ElasticsearchException
import os


class ValidationPipeline:
    """Pipeline de validation des données scrapées"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        """Valide les éléments avant traitement"""
        
        # Vérifications obligatoires
        required_fields = ['title', 'company', 'url', 'source']
        
        for field in required_fields:
            if not item.get(field):
                self.logger.warning(f"Champ requis manquant '{field}' dans {item.get('url', 'URL inconnue')}")
                raise DropItem(f"Champ requis manquant: {field}")
        
        # Validation de l'URL
        url = item.get('url', '')
        if not url.startswith(('http://', 'https://')):
            self.logger.warning(f"URL invalide: {url}")
            raise DropItem(f"URL invalide: {url}")
        
        # Validation de la longueur des champs
        if len(item.get('title', '')) > 255:
            item['title'] = item['title'][:255]
            self.logger.warning(f"Titre tronqué pour {item['url']}")
        
        if len(item.get('company', '')) > 255:
            item['company'] = item['company'][:255]
            self.logger.warning(f"Nom d'entreprise tronqué pour {item['url']}")
        
        self.logger.debug(f"Item validé: {item.get('title', 'N/A')}")
        return item


class CleaningPipeline:
    """Pipeline de nettoyage et normalisation des données"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        """Nettoie et normalise les données"""
        
        # Nettoyage du titre
        if item.get('title'):
            title = item['title'].strip()
            # Supprimer les doublons d'espaces
            title = ' '.join(title.split())
            item['title'] = title
        
        # Nettoyage de l'entreprise
        if item.get('company'):
            company = item['company'].strip()
            # Supprimer les suffixes courants
            company = company.replace(' - Jobs', '').replace(' - Careers', '')
            item['company'] = company
        
        # Nettoyage de la localisation
        if item.get('location'):
            location = item['location'].strip()
            # Normaliser les formats de localisation
            location = location.replace('  ', ' ')
            item['location'] = location
        
        # Nettoyage de la description
        if item.get('description'):
            description = item['description'].strip()
            # Limiter la taille de la description
            if len(description) > 10000:
                description = description[:10000] + "..."
            item['description'] = description
        
        # Génération d'un hash unique
        unique_string = f"{item.get('title', '')}{item.get('company', '')}{item.get('url', '')}"
        item['content_hash'] = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Timestamps
        item['processed_at'] = datetime.now().isoformat()
        
        self.logger.debug(f"Item nettoyé: {item.get('title', 'N/A')}")
        return item


class DatabasePipeline:
    """Pipeline de sauvegarde en base de données"""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        database_url = crawler.settings.get('DATABASE_URL')
        if not database_url:
            database_url = os.getenv('DATABASE_URL')
        
        return cls(database_url=database_url)
    
    def open_spider(self, spider):
        """Initialise la connexion à la base de données"""
        try:
            self.engine = create_engine(self.database_url)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self.logger.info("Connexion à la base de données établie")
        except Exception as e:
            self.logger.error(f"Erreur de connexion à la base de données: {e}")
            raise
    
    def close_spider(self, spider):
        """Ferme la connexion à la base de données"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        self.logger.info("Connexion à la base de données fermée")
    
    def process_item(self, item, spider):
        """Sauvegarde l'item en base de données"""
        try:
            # Import ici pour éviter les dépendances circulaires
            from models.job_offer import JobOffer
            from models.keyword import Keyword
            from sqlalchemy.exc import IntegrityError
            
            # Vérifier si l'offre existe déjà
            existing_job = self.session.query(JobOffer).filter_by(
                external_id=item.get('external_id'),
                source=item.get('source')
            ).first()
            
            if existing_job:
                self.logger.debug(f"Job déjà existant: {item.get('external_id')}")
                return item
            
            # Créer le nouvel job
            job_offer = JobOffer(
                external_id=item.get('external_id'),
                title=item.get('title'),
                company=item.get('company'),
                location=item.get('location'),
                description=item.get('description'),
                requirements=item.get('requirements'),
                salary_min=item.get('salary_min'),
                salary_max=item.get('salary_max'),
                salary_currency=item.get('salary_currency'),
                job_type=item.get('job_type'),
                contract_type=item.get('contract_type'),
                experience_level=item.get('experience_level'),
                remote_work=item.get('remote_work') == 'Oui',
                url=item.get('url'),
                apply_url=item.get('apply_url'),
                source=item.get('source'),
                posted_date=item.get('posted_date'),
                scraped_at=item.get('scraped_at'),
                content_hash=item.get('content_hash'),
                scraping_job_id=item.get('scraping_job_id')
            )
            
            self.session.add(job_offer)
            self.session.commit()
            
            self.logger.info(f"Job sauvegardé: {item.get('title')} - {item.get('company')}")
            
        except IntegrityError as e:
            self.session.rollback()
            self.logger.warning(f"Job déjà existant (contrainte): {item.get('external_id')}")
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Erreur de sauvegarde: {e}")
            raise
        
        return item


class ElasticsearchPipeline:
    """Pipeline de sauvegarde dans Elasticsearch"""
    
    def __init__(self, elasticsearch_url):
        self.elasticsearch_url = elasticsearch_url
        self.es = None
        self.index_name = "job_offers"
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        elasticsearch_url = crawler.settings.get('ELASTICSEARCH_URL')
        if not elasticsearch_url:
            elasticsearch_url = os.getenv('ELASTICSEARCH_URL')
        
        return cls(elasticsearch_url=elasticsearch_url)
    
    def open_spider(self, spider):
        """Initialise la connexion à Elasticsearch"""
        try:
            self.es = Elasticsearch([self.elasticsearch_url])
            
            # Vérifier la connexion
            if self.es.ping():
                self.logger.info("Connexion à Elasticsearch établie")
                self.create_index_if_not_exists()
            else:
                self.logger.error("Impossible de se connecter à Elasticsearch")
                
        except Exception as e:
            self.logger.error(f"Erreur de connexion à Elasticsearch: {e}")
    
    def create_index_if_not_exists(self):
        """Crée l'index s'il n'existe pas"""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "analyzer": "french"},
                        "company": {"type": "keyword"},
                        "location": {"type": "keyword"},
                        "description": {"type": "text", "analyzer": "french"},
                        "requirements": {"type": "text", "analyzer": "french"},
                        "salary_min": {"type": "integer"},
                        "salary_max": {"type": "integer"},
                        "job_type": {"type": "keyword"},
                        "contract_type": {"type": "keyword"},
                        "experience_level": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "scraped_at": {"type": "date"},
                        "posted_date": {"type": "date"}
                    }
                }
            }
            
            try:
                self.es.indices.create(index=self.index_name, body=mapping)
                self.logger.info(f"Index {self.index_name} créé")
            except Exception as e:
                self.logger.error(f"Erreur création index: {e}")
    
    def process_item(self, item, spider):
        """Indexe l'item dans Elasticsearch"""
        if not self.es:
            return item
        
        try:
            # Préparer le document
            doc = dict(item)
            doc_id = item.get('content_hash')
            
            # Indexer le document
            self.es.index(
                index=self.index_name,
                id=doc_id,
                body=doc
            )
            
            self.logger.debug(f"Job indexé dans ES: {item.get('title')}")
            
        except ElasticsearchException as e:
            self.logger.error(f"Erreur indexation ES: {e}")
        except Exception as e:
            self.logger.error(f"Erreur inattendue ES: {e}")
        
        return item


class DuplicatesPipeline:
    """Pipeline de détection et suppression des doublons"""
    
    def __init__(self):
        self.ids_seen = set()
        self.logger = logging.getLogger(__name__)
    
    def process_item(self, item, spider):
        """Filtre les doublons basés sur le content_hash"""
        content_hash = item.get('content_hash')
        
        if content_hash in self.ids_seen:
            self.logger.debug(f"Doublon détecté: {item.get('title')}")
            raise DropItem(f"Doublon: {item.get('url')}")
        else:
            self.ids_seen.add(content_hash)
            return item


# Exception personnalisée
class DropItem(Exception):
    """Exception pour supprimer un item du pipeline"""
    pass