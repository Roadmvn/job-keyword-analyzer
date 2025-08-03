"""
Service d'analyse NLP simplifié pour les tests
"""

import spacy
from typing import List, Dict, Any
from loguru import logger

class KeywordExtractor:
    """Extracteur de mots-clés simplifié"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("fr_core_news_md")
        except OSError:
            logger.warning("Modèle spaCy fr_core_news_md non trouvé, utilisation du modèle par défaut")
            self.nlp = None
    
    def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extraire les mots-clés d'un texte"""
        if not text or not self.nlp:
            return []
        
        doc = self.nlp(text)
        keywords = []
        
        # Technologies communes
        tech_keywords = ["python", "javascript", "java", "react", "django", "fastapi", 
                        "mysql", "postgresql", "docker", "kubernetes", "aws", "git"]
        
        for token in doc:
            if token.text.lower() in tech_keywords:
                keywords.append({
                    "keyword": token.text.title(),
                    "category": "technologie",
                    "confidence": 0.9,
                    "frequency": 1
                })
        
        return keywords

class NLPAnalyzer:
    """Analyseur NLP principal"""
    
    def __init__(self):
        self.keyword_extractor = KeywordExtractor()
    
    def analyze_job_offer(self, job_offer) -> Dict[str, Any]:
        """Analyser une offre d'emploi"""
        text = f"{job_offer.title} {job_offer.description or ''}"
        keywords = self.keyword_extractor.extract_keywords(text)
        
        return {
            "job_id": job_offer.id,
            "keywords": keywords,
            "analysis_summary": {
                "total_keywords": len(keywords),
                "technologies_found": [kw["keyword"] for kw in keywords]
            }
        }

# Instance globale
nlp_analyzer = NLPAnalyzer()