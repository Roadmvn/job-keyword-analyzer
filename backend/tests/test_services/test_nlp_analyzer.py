"""
Tests pour le service d'analyse NLP
"""

import pytest
from unittest.mock import MagicMock, patch
from services.nlp_analyzer import NLPAnalyzer, KeywordExtractor


class TestKeywordExtractor:
    """Tests pour l'extracteur de mots-clés"""
    
    @pytest.fixture
    def extractor(self):
        """Fixture pour l'extracteur de mots-clés"""
        return KeywordExtractor()
    
    def test_extract_keywords_basic(self, extractor, sample_job_description):
        """Test d'extraction basique de mots-clés"""
        keywords = extractor.extract_keywords(sample_job_description)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        
        # Vérifier que certains mots-clés techniques sont extraits
        keyword_names = [kw["keyword"] for kw in keywords]
        assert "Python" in keyword_names
        assert "Docker" in keyword_names
        assert "PostgreSQL" in keyword_names or "MySQL" in keyword_names
    
    def test_extract_keywords_empty_text(self, extractor):
        """Test avec texte vide"""
        keywords = extractor.extract_keywords("")
        assert keywords == []
        
        keywords = extractor.extract_keywords(None)
        assert keywords == []
    
    def test_extract_keywords_structure(self, extractor, sample_job_description):
        """Test de la structure des mots-clés extraits"""
        keywords = extractor.extract_keywords(sample_job_description)
        
        for keyword in keywords:
            assert "keyword" in keyword
            assert "category" in keyword
            assert "confidence" in keyword
            assert "frequency" in keyword
            
            # Vérifier les types
            assert isinstance(keyword["keyword"], str)
            assert isinstance(keyword["confidence"], (int, float))
            assert isinstance(keyword["frequency"], int)
            assert keyword["frequency"] >= 1
    
    def test_categorize_keyword(self, extractor):
        """Test de catégorisation des mots-clés"""
        # Langages de programmation
        assert extractor.categorize_keyword("Python") == "langage"
        assert extractor.categorize_keyword("JavaScript") == "langage"
        assert extractor.categorize_keyword("Java") == "langage"
        
        # Frameworks
        assert extractor.categorize_keyword("Django") == "framework"
        assert extractor.categorize_keyword("React") == "framework"
        assert extractor.categorize_keyword("FastAPI") == "framework"
        
        # Bases de données
        assert extractor.categorize_keyword("PostgreSQL") == "base_donnees"
        assert extractor.categorize_keyword("MySQL") == "base_donnees"
        assert extractor.categorize_keyword("MongoDB") == "base_donnees"
        
        # Outils
        assert extractor.categorize_keyword("Docker") == "outil"
        assert extractor.categorize_keyword("Git") == "outil"
        assert extractor.categorize_keyword("Kubernetes") == "outil"
        
        # Méthodes
        assert extractor.categorize_keyword("Agile") == "methode"
        assert extractor.categorize_keyword("Scrum") == "methode"
        
        # Mot-clé inconnu
        assert extractor.categorize_keyword("MotCleInexistant") == "autre"
    
    def test_clean_text(self, extractor):
        """Test de nettoyage du texte"""
        # Texte avec HTML
        dirty_text = "<p>Développeur <strong>Python</strong> recherché</p>"
        clean = extractor.clean_text(dirty_text)
        assert "<p>" not in clean
        assert "<strong>" not in clean
        assert "Python" in clean
        
        # Texte avec espaces multiples
        dirty_text = "Python    Django     FastAPI"
        clean = extractor.clean_text(dirty_text)
        assert "Python Django FastAPI" == clean.strip()
    
    def test_filter_keywords(self, extractor):
        """Test de filtrage des mots-clés"""
        raw_keywords = [
            {"keyword": "Python", "confidence": 0.9, "frequency": 5},
            {"keyword": "et", "confidence": 0.3, "frequency": 10},  # Mot vide
            {"keyword": "AA", "confidence": 0.8, "frequency": 2},  # Trop court
            {"keyword": "Django", "confidence": 0.85, "frequency": 3},
            {"keyword": "mot_tres_long_qui_depasse_la_limite", "confidence": 0.7, "frequency": 1},  # Trop long
        ]
        
        filtered = extractor.filter_keywords(raw_keywords)
        
        # Seuls Python et Django devraient rester
        assert len(filtered) == 2
        keyword_names = [kw["keyword"] for kw in filtered]
        assert "Python" in keyword_names
        assert "Django" in keyword_names
        assert "et" not in keyword_names
        assert "AA" not in keyword_names


class TestNLPAnalyzer:
    """Tests pour l'analyseur NLP principal"""
    
    @pytest.fixture
    def analyzer(self):
        """Fixture pour l'analyseur NLP"""
        return NLPAnalyzer()
    
    @pytest.fixture
    def mock_job_offer(self, sample_job_offer_data):
        """Mock d'une offre d'emploi"""
        job = MagicMock()
        job.id = 1
        job.title = sample_job_offer_data["title"]
        job.description = sample_job_offer_data["description"]
        job.requirements = sample_job_offer_data["requirements"]
        return job
    
    def test_analyze_job_offer(self, analyzer, mock_job_offer):
        """Test d'analyse d'une offre d'emploi"""
        results = analyzer.analyze_job_offer(mock_job_offer)
        
        assert "job_id" in results
        assert "keywords" in results
        assert "analysis_summary" in results
        assert "categories" in results
        
        assert results["job_id"] == mock_job_offer.id
        assert isinstance(results["keywords"], list)
        assert len(results["keywords"]) > 0
    
    def test_analyze_multiple_jobs(self, analyzer, mock_job_offer):
        """Test d'analyse de plusieurs offres"""
        jobs = [mock_job_offer, mock_job_offer]  # Simuler 2 jobs identiques
        
        results = analyzer.analyze_multiple_jobs(jobs)
        
        assert "total_jobs" in results
        assert "total_keywords" in results
        assert "top_keywords" in results
        assert "categories_breakdown" in results
        
        assert results["total_jobs"] == 2
    
    def test_get_keyword_trends(self, analyzer):
        """Test de l'analyse des tendances"""
        # Simuler des données historiques
        mock_data = [
            {"date": "2024-01-01", "keyword": "Python", "frequency": 10},
            {"date": "2024-01-02", "keyword": "Python", "frequency": 15},
            {"date": "2024-01-01", "keyword": "JavaScript", "frequency": 8},
            {"date": "2024-01-02", "keyword": "JavaScript", "frequency": 12},
        ]
        
        with patch.object(analyzer, '_get_historical_data', return_value=mock_data):
            trends = analyzer.get_keyword_trends(days=30)
        
        assert "trends" in trends
        assert "period" in trends
        assert len(trends["trends"]) > 0
    
    def test_suggest_skills_for_cv(self, analyzer):
        """Test de suggestions pour CV"""
        user_skills = ["Python", "Django"]
        
        # Mock des données du marché
        mock_market_data = [
            {"keyword": "FastAPI", "frequency": 100, "category": "framework"},
            {"keyword": "Docker", "frequency": 80, "category": "outil"},
            {"keyword": "PostgreSQL", "frequency": 70, "category": "base_donnees"},
        ]
        
        with patch.object(analyzer, '_get_market_keywords', return_value=mock_market_data):
            suggestions = analyzer.suggest_skills_for_cv(user_skills)
        
        assert "missing_skills" in suggestions
        assert "skill_gaps" in suggestions
        assert "recommendations" in suggestions
        
        # Vérifier que les compétences suggérées ne sont pas déjà possédées
        suggested_skills = [skill["keyword"] for skill in suggestions["missing_skills"]]
        for skill in user_skills:
            assert skill not in suggested_skills
    
    @patch('services.nlp_analyzer.spacy.load')
    def test_load_nlp_model(self, mock_spacy_load, analyzer):
        """Test du chargement du modèle NLP"""
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp
        
        # Forcer le rechargement du modèle
        analyzer.nlp = None
        result = analyzer._ensure_nlp_model()
        
        assert result == mock_nlp
        mock_spacy_load.assert_called_once()
    
    def test_extract_entities(self, analyzer, sample_job_description):
        """Test d'extraction d'entités nommées"""
        entities = analyzer.extract_entities(sample_job_description)
        
        assert isinstance(entities, list)
        
        for entity in entities:
            assert "text" in entity
            assert "label" in entity
            assert "confidence" in entity
    
    def test_calculate_job_complexity(self, analyzer, mock_job_offer):
        """Test du calcul de complexité d'un job"""
        complexity = analyzer.calculate_job_complexity(mock_job_offer)
        
        assert "score" in complexity
        assert "factors" in complexity
        assert "level" in complexity
        
        assert 0 <= complexity["score"] <= 100
        assert complexity["level"] in ["Junior", "Médian", "Senior", "Expert"]
    
    def test_find_similar_jobs(self, analyzer, mock_job_offer):
        """Test de recherche de jobs similaires"""
        # Mock d'autres jobs en base
        mock_jobs = [MagicMock(), MagicMock(), MagicMock()]
        
        with patch.object(analyzer, '_get_all_jobs', return_value=mock_jobs):
            similar_jobs = analyzer.find_similar_jobs(mock_job_offer, limit=2)
        
        assert isinstance(similar_jobs, list)
        assert len(similar_jobs) <= 2
        
        for job in similar_jobs:
            assert "job" in job
            assert "similarity_score" in job
            assert 0 <= job["similarity_score"] <= 1
    
    def test_analyze_salary_correlation(self, analyzer):
        """Test d'analyse de corrélation salaires/compétences"""
        # Mock des données de salaires
        mock_data = [
            {"keyword": "Python", "avg_salary": 55000, "job_count": 100},
            {"keyword": "JavaScript", "avg_salary": 50000, "job_count": 80},
            {"keyword": "Docker", "avg_salary": 60000, "job_count": 60},
        ]
        
        with patch.object(analyzer, '_get_salary_data', return_value=mock_data):
            correlation = analyzer.analyze_salary_correlation()
        
        assert "top_paying_skills" in correlation
        assert "skill_value" in correlation
        assert len(correlation["top_paying_skills"]) > 0
    
    def test_performance_benchmark(self, analyzer, sample_job_description):
        """Test de performance de l'analyse"""
        import time
        
        start_time = time.time()
        keywords = analyzer.keyword_extractor.extract_keywords(sample_job_description)
        end_time = time.time()
        
        # L'extraction ne devrait pas prendre plus de 5 secondes
        assert (end_time - start_time) < 5.0
        assert len(keywords) > 0


class TestNLPAnalyzerIntegration:
    """Tests d'intégration pour l'analyseur NLP"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_analysis_workflow(self, test_db_session, sample_job_offer_data):
        """Test d'intégration complète"""
        from models.job_offer import JobOffer
        
        # Créer une vraie offre en base
        job = JobOffer(**sample_job_offer_data)
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        # Analyser avec le vrai service
        analyzer = NLPAnalyzer()
        results = analyzer.analyze_job_offer(job)
        
        # Vérifications
        assert results["job_id"] == job.id
        assert len(results["keywords"]) > 0
        
        # Vérifier que les mots-clés contiennent des technologies réelles
        keyword_names = [kw["keyword"] for kw in results["keywords"]]
        tech_keywords = ["Python", "FastAPI", "Django", "PostgreSQL", "MySQL", "Docker"]
        found_tech = [tech for tech in tech_keywords if tech in keyword_names]
        assert len(found_tech) > 0  # Au moins une technologie trouvée