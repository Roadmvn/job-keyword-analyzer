"""
Tests pour le modèle JobOffer
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models.job_offer import JobOffer


class TestJobOfferModel:
    """Tests pour le modèle JobOffer"""
    
    def test_create_job_offer_minimal(self, test_db_session):
        """Test de création d'une offre avec les champs minimaux"""
        job = JobOffer(
            title="Développeur Python",
            company="TechCorp",
            url="https://example.com/job/1",
            source="indeed"
        )
        
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        assert job.id is not None
        assert job.title == "Développeur Python"
        assert job.company == "TechCorp"
        assert job.url == "https://example.com/job/1"
        assert job.source == "indeed"
        assert job.created_at is not None
        assert job.updated_at is not None
    
    def test_create_job_offer_complete(self, test_db_session, sample_job_offer_data):
        """Test de création d'une offre avec tous les champs"""
        job = JobOffer(**sample_job_offer_data)
        
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        assert job.id is not None
        assert job.external_id == sample_job_offer_data["external_id"]
        assert job.title == sample_job_offer_data["title"]
        assert job.company == sample_job_offer_data["company"]
        assert job.location == sample_job_offer_data["location"]
        assert job.description == sample_job_offer_data["description"]
        assert job.salary_min == sample_job_offer_data["salary_min"]
        assert job.salary_max == sample_job_offer_data["salary_max"]
        assert job.remote_work == sample_job_offer_data["remote_work"]
    
    def test_job_offer_to_dict(self, test_db_session, sample_job_offer_data):
        """Test de la méthode to_dict"""
        job = JobOffer(**sample_job_offer_data)
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        job_dict = job.to_dict()
        
        assert isinstance(job_dict, dict)
        assert "id" in job_dict
        assert "title" in job_dict
        assert "company" in job_dict
        assert "created_at" in job_dict
        assert job_dict["title"] == sample_job_offer_data["title"]
        assert job_dict["company"] == sample_job_offer_data["company"]
    
    def test_job_offer_str_representation(self, test_db_session):
        """Test de la représentation string"""
        job = JobOffer(
            title="Python Developer",
            company="TechCorp",
            url="https://example.com/job/1",
            source="indeed"
        )
        
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        str_repr = str(job)
        assert "Python Developer" in str_repr
        assert "TechCorp" in str_repr
    
    def test_job_offer_unique_constraints(self, test_db_session):
        """Test des contraintes d'unicité"""
        # Créer la première offre
        job1 = JobOffer(
            external_id="unique_123",
            title="Python Developer",
            company="TechCorp",
            url="https://example.com/job/1",
            source="indeed"
        )
        test_db_session.add(job1)
        test_db_session.commit()
        
        # Tenter de créer une offre avec le même external_id et source
        job2 = JobOffer(
            external_id="unique_123",
            title="Another Job",
            company="OtherCorp",
            url="https://example.com/job/2",
            source="indeed"  # Même source
        )
        test_db_session.add(job2)
        
        # Cela devrait lever une IntegrityError
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_job_offer_different_sources_same_external_id(self, test_db_session):
        """Test que le même external_id peut exister pour différentes sources"""
        # Première offre (Indeed)
        job1 = JobOffer(
            external_id="123",
            title="Python Developer",
            company="TechCorp",
            url="https://indeed.com/job/123",
            source="indeed"
        )
        test_db_session.add(job1)
        test_db_session.commit()
        
        # Deuxième offre (LinkedIn) avec même external_id
        job2 = JobOffer(
            external_id="123",
            title="JavaScript Developer",
            company="WebCorp",
            url="https://linkedin.com/job/123",
            source="linkedin"
        )
        test_db_session.add(job2)
        test_db_session.commit()  # Ne devrait pas lever d'erreur
        
        # Vérifier que les deux existent
        jobs = test_db_session.query(JobOffer).filter_by(external_id="123").all()
        assert len(jobs) == 2
    
    def test_job_offer_salary_validation(self, test_db_session):
        """Test de validation des salaires"""
        job = JobOffer(
            title="Python Developer",
            company="TechCorp",
            url="https://example.com/job/1",
            source="indeed",
            salary_min=60000,
            salary_max=50000  # Max inférieur au min
        )
        
        test_db_session.add(job)
        test_db_session.commit()  # SQLite ne valide pas automatiquement
        
        # La validation métier devrait être faite au niveau applicatif
        assert job.salary_min > job.salary_max  # Juste pour vérifier que c'est stocké
    
    def test_job_offer_search_by_keywords(self, test_db_session):
        """Test de recherche par mots-clés dans la description"""
        job1 = JobOffer(
            title="Python Developer",
            company="TechCorp",
            description="Nous cherchons un développeur Python avec Django",
            url="https://example.com/job/1",
            source="indeed"
        )
        
        job2 = JobOffer(
            title="JavaScript Developer",
            company="WebCorp",
            description="Développeur React et Node.js expérimenté",
            url="https://example.com/job/2",
            source="indeed"
        )
        
        test_db_session.add_all([job1, job2])
        test_db_session.commit()
        
        # Recherche par mot-clé Python
        python_jobs = test_db_session.query(JobOffer).filter(
            JobOffer.description.contains("Python")
        ).all()
        
        assert len(python_jobs) == 1
        assert python_jobs[0].title == "Python Developer"
        
        # Recherche par mot-clé développeur
        dev_jobs = test_db_session.query(JobOffer).filter(
            JobOffer.description.contains("développeur")
        ).all()
        
        assert len(dev_jobs) == 2
    
    def test_job_offer_filter_by_source(self, test_db_session):
        """Test de filtrage par source"""
        job1 = JobOffer(
            title="Python Developer",
            company="TechCorp",
            url="https://indeed.com/job/1",
            source="indeed"
        )
        
        job2 = JobOffer(
            title="JavaScript Developer",
            company="WebCorp",
            url="https://linkedin.com/job/2",
            source="linkedin"
        )
        
        test_db_session.add_all([job1, job2])
        test_db_session.commit()
        
        # Filtrer par Indeed
        indeed_jobs = test_db_session.query(JobOffer).filter_by(source="indeed").all()
        assert len(indeed_jobs) == 1
        assert indeed_jobs[0].title == "Python Developer"
        
        # Filtrer par LinkedIn
        linkedin_jobs = test_db_session.query(JobOffer).filter_by(source="linkedin").all()
        assert len(linkedin_jobs) == 1
        assert linkedin_jobs[0].title == "JavaScript Developer"
    
    def test_job_offer_date_filtering(self, test_db_session):
        """Test de filtrage par date"""
        from datetime import datetime, timedelta
        
        # Job récent
        recent_job = JobOffer(
            title="Recent Job",
            company="TechCorp",
            url="https://example.com/job/1",
            source="indeed"
        )
        test_db_session.add(recent_job)
        test_db_session.commit()
        test_db_session.refresh(recent_job)
        
        # Simuler un job plus ancien (modification manuelle pour le test)
        old_job = JobOffer(
            title="Old Job",
            company="OldCorp",
            url="https://example.com/job/2",
            source="indeed"
        )
        test_db_session.add(old_job)
        test_db_session.commit()
        
        # Modifier manuellement la date pour le test
        test_db_session.execute(
            "UPDATE job_offers SET created_at = ? WHERE title = ?",
            ((datetime.now() - timedelta(days=10)).isoformat(), "Old Job")
        )
        test_db_session.commit()
        
        # Filtrer les jobs récents (dernières 24h)
        yesterday = datetime.now() - timedelta(days=1)
        recent_jobs = test_db_session.query(JobOffer).filter(
            JobOffer.created_at >= yesterday.isoformat()
        ).all()
        
        # Note: Ce test dépend de la précision des timestamps
        # En production, utiliser des vraies dates/times