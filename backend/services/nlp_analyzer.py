"""
Service d'analyse NLP pour l'extraction de mots-clés
"""

import spacy
import re
from typing import List, Dict, Tuple, Set
from collections import Counter
from dataclasses import dataclass


@dataclass
class KeywordResult:
    """Résultat d'extraction de mots-clés"""
    keyword: str
    category: str
    confidence: float
    frequency: int


class NLPAnalyzer:
    """Analyseur NLP pour extraire les compétences techniques des offres d'emploi"""
    
    def __init__(self):
        """Initialiser l'analyseur NLP"""
        try:
            # Charger le modèle spaCy français
            self.nlp = spacy.load("fr_core_news_md")
        except OSError:
            print("⚠️ Modèle spaCy français non trouvé, utilisation du modèle anglais")
            try:
                self.nlp = spacy.load("en_core_web_md")
            except OSError:
                print("❌ Aucun modèle spaCy disponible")
                self.nlp = None
        
        # Dictionnaires de mots-clés techniques par catégorie
        self.tech_keywords = {
            'LANGUAGE': {
                'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
                'typescript', 'scala', 'kotlin', 'swift', 'r', 'matlab', 'sql', 'html',
                'css', 'bash', 'powershell', 'dart', 'lua', 'perl', 'haskell', 'julia'
            },
            'FRAMEWORK': {
                'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'laravel',
                'symfony', 'rails', 'express', 'nextjs', 'nuxt', 'gatsby', 'ember', 'backbone',
                'jquery', 'bootstrap', 'tailwind', 'material-ui', 'chakra-ui', 'ant-design',
                'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'keras'
            },
            'TOOL': {
                'docker', 'kubernetes', 'git', 'jenkins', 'gitlab', 'github', 'aws', 'azure',
                'gcp', 'terraform', 'ansible', 'vagrant', 'nginx', 'apache', 'redis', 'mongodb',
                'postgresql', 'mysql', 'elasticsearch', 'kafka', 'rabbitmq', 'grafana', 'prometheus',
                'jira', 'confluence', 'slack', 'teams', 'figma', 'sketch', 'photoshop', 'illustrator'
            },
            'SKILL': {
                'machine learning', 'deep learning', 'artificial intelligence', 'data science',
                'data analysis', 'big data', 'business intelligence', 'devops', 'cicd', 'agile',
                'scrum', 'kanban', 'tdd', 'bdd', 'microservices', 'api rest', 'graphql',
                'responsive design', 'ux/ui', 'design thinking', 'cybersecurity', 'blockchain',
                'cloud computing', 'serverless', 'mobile development', 'web development'
            },
            'DOMAIN': {
                'fintech', 'healthtech', 'edtech', 'e-commerce', 'saas', 'b2b', 'b2c',
                'startup', 'scale-up', 'enterprise', 'consulting', 'digital transformation',
                'innovation', 'research', 'marketing digital', 'growth hacking', 'seo', 'sem'
            }
        }
        
        # Motifs regex pour détecter certains patterns
        self.regex_patterns = {
            'VERSION': r'(\w+)\s+(\d+(?:\.\d+)*)',  # Ex: "Python 3.9", "React 18"
            'EXPERIENCE': r'(\d+)\s*(?:ans?|années?)\s*(?:d\'?expérience|experience)',
            'SALARY': r'(\d+)\s*(?:k€|k|000)\s*(?:€|euros?)?',
            'CERTIFICATION': r'certifi[éeè]\s+(\w+)',
        }
    
    def extract_keywords(self, text: str, min_confidence: float = 0.6) -> List[KeywordResult]:
        """
        Extraire les mots-clés techniques d'un texte
        
        Args:
            text: Texte à analyser (description d'offre d'emploi)
            min_confidence: Score de confiance minimum
            
        Returns:
            Liste des mots-clés extraits avec métadonnées
        """
        if not text or not self.nlp:
            return []
        
        # Nettoyer et normaliser le texte
        cleaned_text = self._clean_text(text)
        
        # Analyser avec spaCy
        doc = self.nlp(cleaned_text)
        
        # Extraire les mots-clés par différentes méthodes
        keywords = []
        
        # 1. Recherche par dictionnaire technique
        dict_keywords = self._extract_by_dictionary(cleaned_text)
        keywords.extend(dict_keywords)
        
        # 2. Extraction par entités nommées
        ner_keywords = self._extract_by_ner(doc)
        keywords.extend(ner_keywords)
        
        # 3. Extraction par patterns regex
        regex_keywords = self._extract_by_regex(cleaned_text)
        keywords.extend(regex_keywords)
        
        # 4. Extraction par analyse syntaxique
        syntax_keywords = self._extract_by_syntax(doc)
        keywords.extend(syntax_keywords)
        
        # Déduplication et scoring
        final_keywords = self._deduplicate_and_score(keywords, min_confidence)
        
        return final_keywords
    
    def _clean_text(self, text: str) -> str:
        """Nettoyer et normaliser le texte"""
        # Conversion en minuscules
        text = text.lower()
        
        # Supprimer HTML/XML
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer caractères spéciaux excessifs
        text = re.sub(r'[^\w\s\-\.\+\#]', ' ', text)
        
        return text.strip()
    
    def _extract_by_dictionary(self, text: str) -> List[KeywordResult]:
        """Extraction basée sur les dictionnaires techniques"""
        keywords = []
        
        for category, tech_set in self.tech_keywords.items():
            for tech in tech_set:
                # Recherche exacte et variations
                patterns = [
                    rf'\b{re.escape(tech)}\b',
                    rf'\b{re.escape(tech)}\.?js\b' if tech in ['react', 'vue', 'angular'] else None,
                    rf'\b{re.escape(tech)}\s*\d+\b',  # Avec version
                ]
                
                for pattern in patterns:
                    if pattern and re.search(pattern, text):
                        # Compter les occurrences
                        frequency = len(re.findall(pattern, text))
                        confidence = min(0.95, 0.7 + frequency * 0.1)
                        
                        keywords.append(KeywordResult(
                            keyword=tech,
                            category=category,
                            confidence=confidence,
                            frequency=frequency
                        ))
                        break
        
        return keywords
    
    def _extract_by_ner(self, doc) -> List[KeywordResult]:
        """Extraction par reconnaissance d'entités nommées"""
        keywords = []
        
        # Entités organisationnelles (peuvent être des technologies)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT'] and len(ent.text) > 2:
                # Vérifier si c'est une techno connue
                keyword_lower = ent.text.lower()
                category = self._classify_keyword(keyword_lower)
                
                if category != 'OTHER':
                    keywords.append(KeywordResult(
                        keyword=keyword_lower,
                        category=category,
                        confidence=0.7,
                        frequency=1
                    ))
        
        return keywords
    
    def _extract_by_regex(self, text: str) -> List[KeywordResult]:
        """Extraction par patterns regex"""
        keywords = []
        
        # Pattern pour les technologies avec versions
        version_matches = re.findall(self.regex_patterns['VERSION'], text)
        for tech, version in version_matches:
            category = self._classify_keyword(tech.lower())
            if category != 'OTHER':
                keywords.append(KeywordResult(
                    keyword=f"{tech.lower()}",
                    category=category,
                    confidence=0.8,
                    frequency=1
                ))
        
        return keywords
    
    def _extract_by_syntax(self, doc) -> List[KeywordResult]:
        """Extraction par analyse syntaxique"""
        keywords = []
        
        # Rechercher les noms composés techniques
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                len(token.text) > 2):
                
                # Vérifier si c'est technique
                category = self._classify_keyword(token.lemma_.lower())
                if category != 'OTHER':
                    keywords.append(KeywordResult(
                        keyword=token.lemma_.lower(),
                        category=category,
                        confidence=0.6,
                        frequency=1
                    ))
        
        return keywords
    
    def _classify_keyword(self, keyword: str) -> str:
        """Classifier un mot-clé dans une catégorie"""
        keyword_lower = keyword.lower()
        
        for category, tech_set in self.tech_keywords.items():
            if keyword_lower in tech_set:
                return category
        
        # Patterns pour classification automatique
        if any(pattern in keyword_lower for pattern in ['dev', 'develop', 'program']):
            return 'SKILL'
        elif any(pattern in keyword_lower for pattern in ['js', 'py', 'lang']):
            return 'LANGUAGE'
        elif any(pattern in keyword_lower for pattern in ['framework', 'library', 'lib']):
            return 'FRAMEWORK'
        
        return 'OTHER'
    
    def _deduplicate_and_score(self, keywords: List[KeywordResult], min_confidence: float) -> List[KeywordResult]:
        """Déduplication et scoring final"""
        # Grouper par mot-clé
        grouped = {}
        for kw in keywords:
            key = kw.keyword.lower()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(kw)
        
        # Fusionner et scorer
        final_keywords = []
        for keyword_variants in grouped.values():
            if not keyword_variants:
                continue
                
            # Prendre la meilleure variante
            best = max(keyword_variants, key=lambda x: x.confidence)
            
            # Ajuster le score selon la fréquence totale
            total_frequency = sum(kw.frequency for kw in keyword_variants)
            best.frequency = total_frequency
            best.confidence = min(0.95, best.confidence + total_frequency * 0.05)
            
            # Filtrer selon le seuil de confiance
            if best.confidence >= min_confidence:
                final_keywords.append(best)
        
        # Trier par confiance décroissante
        return sorted(final_keywords, key=lambda x: x.confidence, reverse=True)
    
    def analyze_job_requirements(self, description: str, requirements: str = "") -> Dict:
        """
        Analyser complètement une offre d'emploi
        
        Returns:
            Dictionnaire avec analyse complète
        """
        full_text = f"{description} {requirements}".strip()
        
        # Extraire les mots-clés
        keywords = self.extract_keywords(full_text)
        
        # Analyser les patterns spéciaux
        experience_matches = re.findall(self.regex_patterns['EXPERIENCE'], full_text.lower())
        salary_matches = re.findall(self.regex_patterns['SALARY'], full_text.lower())
        
        # Classifier le niveau du poste
        seniority_level = self._detect_seniority(full_text)
        
        # Résumé par catégorie
        categories_summary = {}
        for kw in keywords:
            if kw.category not in categories_summary:
                categories_summary[kw.category] = []
            categories_summary[kw.category].append(kw.keyword)
        
        return {
            'keywords': [
                {
                    'keyword': kw.keyword,
                    'category': kw.category,
                    'confidence': kw.confidence,
                    'frequency': kw.frequency
                }
                for kw in keywords
            ],
            'categories_summary': categories_summary,
            'experience_required': experience_matches[0] if experience_matches else None,
            'salary_indicators': salary_matches,
            'seniority_level': seniority_level,
            'total_tech_skills': len(keywords),
            'top_category': max(categories_summary.keys(), key=lambda k: len(categories_summary[k])) if categories_summary else None
        }
    
    def _detect_seniority(self, text: str) -> str:
        """Détecter le niveau de séniorité requis"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['senior', 'expert', 'lead', 'principal', 'architect']):
            return 'SENIOR'
        elif any(word in text_lower for word in ['junior', 'débutant', 'entry', 'graduate']):
            return 'JUNIOR'
        elif any(word in text_lower for word in ['stage', 'internship', 'stagiaire']):
            return 'INTERNSHIP'
        else:
            return 'INTERMEDIATE'
    
    def suggest_cv_improvements(self, user_skills: List[str], market_keywords: List[KeywordResult]) -> Dict:
        """
        Suggérer des améliorations de CV basées sur les tendances du marché
        
        Args:
            user_skills: Compétences actuelles de l'utilisateur
            market_keywords: Mots-clés populaires du marché
            
        Returns:
            Suggestions d'amélioration
        """
        user_skills_lower = [skill.lower() for skill in user_skills]
        
        # Compétences manquantes importantes
        missing_skills = []
        for kw in market_keywords[:20]:  # Top 20
            if kw.keyword.lower() not in user_skills_lower:
                missing_skills.append({
                    'skill': kw.keyword,
                    'category': kw.category,
                    'market_demand': kw.frequency,
                    'priority': 'HIGH' if kw.confidence > 0.8 else 'MEDIUM'
                })
        
        # Compétences à approfondir
        to_improve = []
        for skill in user_skills_lower:
            market_kw = next((kw for kw in market_keywords if kw.keyword.lower() == skill), None)
            if market_kw and market_kw.frequency > 5:
                to_improve.append({
                    'skill': skill,
                    'market_frequency': market_kw.frequency,
                    'suggestion': f"Approfondir {skill} - très demandé ({market_kw.frequency} occurrences)"
                })
        
        return {
            'missing_skills': missing_skills[:10],  # Top 10 manquantes
            'skills_to_improve': to_improve[:5],    # Top 5 à améliorer
            'total_coverage': len(user_skills_lower) / len(market_keywords) * 100 if market_keywords else 0,
            'recommendations': self._generate_recommendations(missing_skills, to_improve)
        }
    
    def _generate_recommendations(self, missing_skills: List, to_improve: List) -> List[str]:
        """Générer des recommandations textuelles"""
        recommendations = []
        
        if missing_skills:
            # Recommandations par catégorie
            categories = {}
            for skill in missing_skills[:5]:
                cat = skill['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(skill['skill'])
            
            for category, skills in categories.items():
                if category == 'LANGUAGE':
                    recommendations.append(f"🔤 Apprendre les langages : {', '.join(skills)}")
                elif category == 'FRAMEWORK':
                    recommendations.append(f"🛠️ Maîtriser les frameworks : {', '.join(skills)}")
                elif category == 'TOOL':
                    recommendations.append(f"⚙️ Se former aux outils : {', '.join(skills)}")
        
        if to_improve:
            recommendations.append(f"📈 Approfondir vos compétences existantes en {', '.join([s['skill'] for s in to_improve[:3]])}")
        
        return recommendations


# Instance globale
nlp_analyzer = NLPAnalyzer() 