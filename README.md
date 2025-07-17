# 🚀 Job Keywords Analyzer

Une application de scraping et d'analyse d'offres d'emploi utilisant l'intelligence artificielle pour extraire et analyser les compétences les plus demandées sur le marché du travail.

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Technologies utilisées](#technologies-utilisées)
- [Installation rapide](#installation-rapide)
- [Guide de développement](#guide-de-développement)
- [Gestion Docker](#gestion-docker)
- [API Documentation](#api-documentation)
- [Contribution](#contribution)

## 🎯 Vue d'ensemble

### Objectif
Automatiser la collecte et l'analyse des offres d'emploi pour identifier :
- Les compétences techniques les plus demandées
- Les tendances du marché de l'emploi
- Les évolutions des technologies recherchées
- Les insights pour orienter la formation

### Fonctionnalités principales
- **Scraping automatisé** : Collecte d'offres depuis Indeed, LinkedIn, etc.
- **Analyse NLP** : Extraction de mots-clés avec spaCy
- **API REST** : Exposition des données via FastAPI
- **Dashboard** : Visualisation des données avec React
- **Recherche avancée** : Moteur de recherche full-text avec Elasticsearch

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │────│   FastAPI        │────│   MySQL         │
│   (Frontend)    │    │   (API Gateway)  │    │   (Database)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scrapy        │────│   Redis Queue    │────│   Elasticsearch │
│   (Scraper)     │    │   (Jobs)         │    │   (Search)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   spaCy NLP      │
                       │   (Analysis)     │
                       └──────────────────┘
```

## 🛠️ Technologies utilisées

### Backend
- **Python 3.11+** : Langage principal
- **FastAPI** : Framework web moderne et rapide
- **Scrapy** : Framework de scraping robuste
- **spaCy** : Traitement du langage naturel
- **SQLAlchemy** : ORM pour la base de données
- **Redis + RQ** : File de tâches asynchrones

### Base de données
- **MySQL 8.0** : Base de données relationnelle
- **Elasticsearch** : Moteur de recherche et analytics
- **Redis** : Cache et file de tâches

### Frontend
- **React 18** : Interface utilisateur
- **Vite** : Bundler rapide
- **Tailwind CSS** : Framework CSS utilitaire
- **Recharts** : Graphiques et visualisations

### Infrastructure
- **Docker & Docker Compose** : Conteneurisation
- **NGINX** : Reverse proxy (production)

## 🚀 Installation rapide

### Prérequis
- Docker et Docker Compose
- Python 3.11+ (pour le développement)
- Node.js 18+ (pour le frontend)

### 1. Cloner le projet
```bash
git clone <url-repo>
cd job-keywords-analyzer
```

### 2. Configuration
```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer les variables selon vos besoins
nano .env
```

### 3. Lancement avec Docker
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### 4. Accès aux services
- **API** : http://localhost:8000
- **Frontend** : http://localhost:3000
- **Elasticsearch** : http://localhost:9200
- **MySQL** : localhost:3306

## 🧑‍💻 Guide de développement

### Structure du projet
```
job-keywords-analyzer/
├── backend/
│   ├── api/              # FastAPI application
│   ├── scraper/          # Scrapy spiders
│   ├── nlp/              # Analyse NLP
│   └── models/           # Modèles de données
├── frontend/
│   ├── src/
│   │   ├── components/   # Composants React
│   │   ├── pages/        # Pages de l'application
│   │   └── utils/        # Utilitaires
├── docker/               # Configurations Docker
├── docs/                 # Documentation
└── tests/                # Tests automatisés
```

### Développement local

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Base de données
```bash
# Démarrer uniquement MySQL et Redis
docker-compose up -d mysql redis

# Créer les tables
cd backend
python -m alembic upgrade head
```

### Workflow de développement

1. **Développement backend** : Modifiez le code dans `backend/`
2. **Tests** : `pytest backend/tests/`
3. **Développement frontend** : Modifiez le code dans `frontend/`
4. **Build & Test** : `docker-compose build && docker-compose up -d`

## 📊 API Documentation

L'API est automatiquement documentée via FastAPI :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints principaux

#### Scraping
- `POST /api/scraper/start` : Démarrer un scraping
- `GET /api/scraper/status/{job_id}` : Statut d'un job
- `GET /api/scraper/jobs` : Liste des offres collectées

#### Analyse
- `POST /api/analyze/job/{job_id}` : Analyser une offre
- `GET /api/analyze/keywords` : Top des mots-clés
- `GET /api/analyze/trends` : Tendances temporelles

#### Recherche
- `GET /api/search/jobs` : Rechercher des offres
- `GET /api/search/suggestions` : Suggestions de recherche

## 🧪 Tests

```bash
# Tests backend
cd backend
pytest tests/ -v

# Tests frontend
cd frontend
npm test

# Tests d'intégration
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🐳 Gestion Docker

Pour gérer efficacement les conteneurs Docker et résoudre les conflits de ports, consultez notre documentation complète :

📖 **[Guide complet de gestion Docker](docs/docker-management.md)**

### Script d'aide interactif
```bash
# Lancer le script d'aide Docker (recommandé)
./docker-helper

# Ou directement
./scripts/docker-helper.sh
```

### Commandes essentielles
```bash
# Lister les conteneurs actifs
docker ps

# Identifier les conflits de ports
ss -tlnp | grep :3000

# Arrêter un conteneur spécifique
docker stop CONTAINER_NAME

# Nettoyer les conteneurs arrêtés
docker container prune
```

## 📈 Monitoring

### Logs
```bash
# Voir tous les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f api
```

### Métriques
- **Redis** : http://localhost:6379
- **MySQL** : Utilisez un client comme DBeaver
- **Elasticsearch** : http://localhost:9200/_cluster/health

## 🚀 Déploiement

### Production avec Docker
```bash
# Build des images de production
docker-compose -f docker-compose.prod.yml build

# Déploiement
docker-compose -f docker-compose.prod.yml up -d
```

### Variables d'environnement importantes
```env
# Base de données
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_DATABASE=job_analyzer
MYSQL_USER=app_user
MYSQL_PASSWORD=app_password

# Redis
REDIS_PASSWORD=redis_password

# API
API_SECRET_KEY=your_secret_key_here
DEBUG=false

# Scraping
SCRAPING_DELAY=2000
MAX_CONCURRENT_JOBS=5
```

## 🤝 Contribution

### Comment contribuer
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

### Standards de code
- **Python** : PEP 8, type hints, docstrings
- **JavaScript** : ESLint, Prettier
- **Commits** : Messages clairs en français
- **Tests** : Couverture minimale de 80%

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

- **Issues** : Utilisez GitHub Issues
- **Documentation** : Consultez le dossier `docs/`
- **FAQ** : Voir `docs/FAQ.md`

---

**Développé avec ❤️ pour analyser le marché de l'emploi tech** 