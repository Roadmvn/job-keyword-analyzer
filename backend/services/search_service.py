"""
Service de recherche intelligente avec Elasticsearch
"""

from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher
from dataclasses import dataclass
import os


@dataclass
class SearchResult:
    """Résultat de recherche"""
    job_id: int
    title: str
    company: str
    location: str
    description: str
    keywords: List[str]
    score: float
    highlighted_text: str = ""


class SearchService:
    """Service de recherche intelligente pour les offres d'emploi"""
    
    def __init__(self):
        """Initialiser le service de recherche"""
        try:
            # Connexion à Elasticsearch
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
            self.es = Elasticsearch([es_url])
            
            # Vérifier la connexion
            if self.es.ping():
                print("✅ Connexion Elasticsearch établie")
                self._setup_indices()
            else:
                print("❌ Connexion Elasticsearch échouée")
                self.es = None
        except Exception as e:
            print(f"❌ Erreur Elasticsearch: {e}")
            self.es = None
        
        # Index des offres d'emploi
        self.jobs_index = "job_offers"
        
        # Dictionnaire de correction d'erreurs communes
        self.corrections = {
            'pythom': 'python',
            'pytho': 'python',
            'phyton': 'python',
            'javascrip': 'javascript',
            'javasript': 'javascript',
            'react.js': 'react',
            'reactjs': 'react',
            'vue.js': 'vue',
            'vuejs': 'vue',
            'angula': 'angular',
            'djano': 'django',
            'djanga': 'django',
            'fastap': 'fastapi',
            'fastapy': 'fastapi',
            'docke': 'docker',
            'doker': 'docker',
            'kubernets': 'kubernetes',
            'kubernet': 'kubernetes',
            'postgre': 'postgresql',
            'postgres': 'postgresql',
            'mysql': 'mysql',
            'mango': 'mongodb',
            'mongdb': 'mongodb',
            'elasticsearh': 'elasticsearch',
            'elasticseach': 'elasticsearch',
        }
    
    def _setup_indices(self):
        """Configurer les indices Elasticsearch"""
        if not self.es:
            return
        
        # Configuration de l'index des offres d'emploi
        job_mapping = {
            "mappings": {
                "properties": {
                    "job_id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "french",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {
                                "type": "completion",
                                "analyzer": "simple"
                            }
                        }
                    },
                    "company": {
                        "type": "text",
                        "analyzer": "french",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "location": {
                        "type": "text",
                        "analyzer": "french",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "french"
                    },
                    "requirements": {
                        "type": "text",
                        "analyzer": "french"
                    },
                    "keywords": {
                        "type": "text",
                        "analyzer": "keyword",
                        "fields": {
                            "suggest": {
                                "type": "completion",
                                "analyzer": "simple"
                            }
                        }
                    },
                    "contract_type": {"type": "keyword"},
                    "experience_level": {"type": "keyword"},
                    "salary_min": {"type": "float"},
                    "salary_max": {"type": "float"},
                    "remote_work": {"type": "boolean"},
                    "scraped_at": {"type": "date"},
                    "created_at": {"type": "date"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "french": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "french_elision", "french_stop", "french_stemmer"]
                        }
                    },
                    "filter": {
                        "french_elision": {
                            "type": "elision",
                            "articles_case": True,
                            "articles": ["l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"]
                        },
                        "french_stop": {
                            "type": "stop",
                            "stopwords": "_french_"
                        },
                        "french_stemmer": {
                            "type": "stemmer",
                            "language": "light_french"
                        }
                    }
                }
            }
        }
        
        try:
            # Créer l'index s'il n'existe pas
            if not self.es.indices.exists(index=self.jobs_index):
                self.es.indices.create(index=self.jobs_index, body=job_mapping)
                print(f"✅ Index {self.jobs_index} créé")
        except Exception as e:
            print(f"⚠️ Erreur création index: {e}")
    
    def index_job(self, job_data: Dict) -> bool:
        """
        Indexer une offre d'emploi dans Elasticsearch
        
        Args:
            job_data: Données de l'offre d'emploi
            
        Returns:
            Succès de l'indexation
        """
        if not self.es:
            return False
        
        try:
            # Préparer le document pour Elasticsearch
            doc = {
                "job_id": job_data.get("id"),
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "description": job_data.get("description", ""),
                "requirements": job_data.get("requirements", ""),
                "keywords": job_data.get("keywords", []),
                "contract_type": job_data.get("contract_type"),
                "experience_level": job_data.get("experience_level"),
                "salary_min": job_data.get("salary_min"),
                "salary_max": job_data.get("salary_max"),
                "remote_work": job_data.get("remote_work", False),
                "scraped_at": job_data.get("scraped_at"),
                "created_at": job_data.get("created_at")
            }
            
            # Indexer le document
            self.es.index(
                index=self.jobs_index,
                id=job_data.get("id"),
                body=doc
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur indexation: {e}")
            return False
    
    def correct_query(self, query: str) -> str:
        """
        Corriger les erreurs de frappe dans la requête
        
        Args:
            query: Requête de recherche
            
        Returns:
            Requête corrigée
        """
        if not query:
            return query
        
        words = query.lower().split()
        corrected_words = []
        
        for word in words:
            # Vérifier les corrections manuelles
            if word in self.corrections:
                corrected_words.append(self.corrections[word])
                continue
            
            # Recherche de correspondance floue
            best_match = None
            best_score = 0.6  # Seuil minimum de similarité
            
            for correct_word in self.corrections.values():
                score = SequenceMatcher(None, word, correct_word).ratio()
                if score > best_score:
                    best_match = correct_word
                    best_score = score
            
            corrected_words.append(best_match if best_match else word)
        
        corrected_query = " ".join(corrected_words)
        
        # Log si correction appliquée
        if corrected_query != query.lower():
            print(f"🔧 Correction: '{query}' → '{corrected_query}'")
        
        return corrected_query
    
    def smart_search(
        self,
        query: str,
        filters: Dict = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Recherche intelligente avec correction d'erreurs et filtres
        
        Args:
            query: Terme de recherche
            filters: Filtres optionnels (location, company, etc.)
            limit: Nombre max de résultats
            offset: Décalage pour pagination
            
        Returns:
            Résultats de recherche avec métadonnées
        """
        if not self.es:
            return {
                "results": [],
                "total": 0,
                "corrected_query": query,
                "suggestions": []
            }
        
        # Corriger la requête
        corrected_query = self.correct_query(query) if query else ""
        
        # Construire la requête Elasticsearch
        es_query = self._build_search_query(corrected_query, filters)
        
        try:
            # Exécuter la recherche
            response = self.es.search(
                index=self.jobs_index,
                body=es_query,
                size=limit,
                from_=offset
            )
            
            # Traiter les résultats
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                
                # Extraire le texte surligné s'il existe
                highlighted = ""
                if 'highlight' in hit:
                    highlighted = " ".join([
                        " ".join(highlights) 
                        for highlights in hit['highlight'].values()
                    ])
                
                results.append(SearchResult(
                    job_id=source['job_id'],
                    title=source['title'],
                    company=source['company'],
                    location=source['location'],
                    description=source['description'][:300] + "..." if len(source['description']) > 300 else source['description'],
                    keywords=source.get('keywords', []),
                    score=hit['_score'],
                    highlighted_text=highlighted
                ))
            
            # Générer des suggestions si peu de résultats
            suggestions = []
            if len(results) < 3 and query:
                suggestions = self._get_suggestions(query)
            
            return {
                "results": [
                    {
                        "job_id": r.job_id,
                        "title": r.title,
                        "company": r.company,
                        "location": r.location,
                        "description": r.description,
                        "keywords": r.keywords,
                        "score": r.score,
                        "highlighted": r.highlighted_text
                    }
                    for r in results
                ],
                "total": response['hits']['total']['value'],
                "corrected_query": corrected_query,
                "original_query": query,
                "suggestions": suggestions,
                "filters_applied": filters or {},
                "search_time": response['took']
            }
            
        except Exception as e:
            print(f"❌ Erreur recherche: {e}")
            return {
                "results": [],
                "total": 0,
                "corrected_query": corrected_query,
                "suggestions": [],
                "error": str(e)
            }
    
    def _build_search_query(self, query: str, filters: Dict = None) -> Dict:
        """Construire la requête Elasticsearch"""
        # Requête de base
        if query:
            main_query = {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",        # Titre plus important
                        "description^2",  # Description importante
                        "requirements^2", # Prérequis importants
                        "keywords^4",     # Mots-clés très importants
                        "company",
                        "location"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",  # Correction automatique d'erreurs
                    "prefix_length": 1,   # Préfixe minimum avant fuzziness
                    "max_expansions": 50  # Limite d'expansion
                }
            }
        else:
            main_query = {"match_all": {}}
        
        # Construire les filtres
        filter_clauses = []
        if filters:
            if filters.get("location"):
                filter_clauses.append({
                    "match": {"location": filters["location"]}
                })
            
            if filters.get("company"):
                filter_clauses.append({
                    "match": {"company": filters["company"]}
                })
            
            if filters.get("contract_type"):
                filter_clauses.append({
                    "term": {"contract_type": filters["contract_type"]}
                })
            
            if filters.get("experience_level"):
                filter_clauses.append({
                    "term": {"experience_level": filters["experience_level"]}
                })
            
            if filters.get("remote_work") is not None:
                filter_clauses.append({
                    "term": {"remote_work": filters["remote_work"]}
                })
            
            # Filtres de salaire
            if filters.get("salary_min") or filters.get("salary_max"):
                salary_range = {}
                if filters.get("salary_min"):
                    salary_range["gte"] = filters["salary_min"]
                if filters.get("salary_max"):
                    salary_range["lte"] = filters["salary_max"]
                
                filter_clauses.append({
                    "range": {"salary_min": salary_range}
                })
        
        # Assemblage final de la requête
        if filter_clauses:
            final_query = {
                "bool": {
                    "must": main_query,
                    "filter": filter_clauses
                }
            }
        else:
            final_query = main_query
        
        # Configuration complète
        return {
            "query": final_query,
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {},
                    "requirements": {},
                    "keywords": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            },
            "sort": [
                "_score",
                {"created_at": {"order": "desc"}}
            ]
        }
    
    def _get_suggestions(self, query: str) -> List[str]:
        """Générer des suggestions de recherche"""
        if not self.es:
            return []
        
        try:
            # Recherche de suggestions basée sur les titres et mots-clés
            suggest_query = {
                "suggest": {
                    "title_suggest": {
                        "text": query,
                        "completion": {
                            "field": "title.suggest",
                            "size": 5,
                            "skip_duplicates": True
                        }
                    },
                    "keyword_suggest": {
                        "text": query,
                        "completion": {
                            "field": "keywords.suggest",
                            "size": 5,
                            "skip_duplicates": True
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.jobs_index,
                body=suggest_query,
                size=0
            )
            
            suggestions = []
            
            # Extraire les suggestions de titres
            for suggestion in response.get('suggest', {}).get('title_suggest', []):
                for option in suggestion.get('options', []):
                    suggestions.append(option['text'])
            
            # Extraire les suggestions de mots-clés
            for suggestion in response.get('suggest', {}).get('keyword_suggest', []):
                for option in suggestion.get('options', []):
                    suggestions.append(option['text'])
            
            # Déduplication et limitation
            return list(set(suggestions))[:5]
            
        except Exception as e:
            print(f"❌ Erreur suggestions: {e}")
            return []
    
    def get_popular_searches(self) -> List[Dict]:
        """Obtenir les recherches populaires basées sur les mots-clés fréquents"""
        if not self.es:
            return []
        
        try:
            # Agrégation pour trouver les mots-clés les plus fréquents
            agg_query = {
                "size": 0,
                "aggs": {
                    "popular_keywords": {
                        "terms": {
                            "field": "keywords.keyword",
                            "size": 10
                        }
                    },
                    "popular_companies": {
                        "terms": {
                            "field": "company.keyword",
                            "size": 5
                        }
                    },
                    "popular_locations": {
                        "terms": {
                            "field": "location.keyword",
                            "size": 5
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.jobs_index,
                body=agg_query
            )
            
            return {
                "keywords": [
                    {"term": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response["aggregations"]["popular_keywords"]["buckets"]
                ],
                "companies": [
                    {"term": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response["aggregations"]["popular_companies"]["buckets"]
                ],
                "locations": [
                    {"term": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response["aggregations"]["popular_locations"]["buckets"]
                ]
            }
            
        except Exception as e:
            print(f"❌ Erreur recherches populaires: {e}")
            return {"keywords": [], "companies": [], "locations": []}
    
    def autocomplete(self, query: str, field: str = "title") -> List[str]:
        """Autocomplétion de recherche"""
        if not self.es or not query:
            return []
        
        try:
            suggest_query = {
                "suggest": {
                    "autocomplete": {
                        "text": query,
                        "completion": {
                            "field": f"{field}.suggest",
                            "size": 8,
                            "skip_duplicates": True
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.jobs_index,
                body=suggest_query,
                size=0
            )
            
            suggestions = []
            for suggestion in response.get('suggest', {}).get('autocomplete', []):
                for option in suggestion.get('options', []):
                    suggestions.append(option['text'])
            
            return suggestions
            
        except Exception as e:
            print(f"❌ Erreur autocomplétion: {e}")
            return []


# Instance globale
search_service = SearchService() 