# 🚀 Guide d'Utilisation - Job Keywords Analyzer

## Démarrage Rapide

### 1. Lancer l'Application
```bash
./start-minimal.sh
```

### 2. Accéder aux Interfaces
- **Frontend React** : http://localhost:3000
- **API Backend** : http://localhost:8000
- **Documentation** : http://localhost:8000/docs

## 🔍 Utilisation du Scraping

### Lancer un Scraping
```bash
# Scraping basique
curl -X POST "http://localhost:8000/api/scrape?query=python&location=Paris"

# Scraping spécialisé
curl -X POST "http://localhost:8000/api/scrape?query=react&location=Remote"
```

### Consulter les Résultats
```bash
# Voir les jobs scrapés
curl http://localhost:8000/api/scraped-jobs

# Voir les statistiques
curl http://localhost:8000/api/stats

# Rechercher dans la base
curl -X POST http://localhost:8000/api/db/search \
  -H "Content-Type: application/json" \
  -d '{"query":"fastapi","location":"Paris"}'
```

## 📊 Endpoints Principaux

### Données Mixtes (Recommandé)
- `GET /api/jobs/combined` - Jobs test + scrapés
- `GET /api/stats` - Statistiques complètes
- `GET /api/keywords` - Mots-clés populaires

### Scraping en Temps Réel
- `POST /api/scrape` - Lancer nouveau scraping
- `GET /api/scraped-jobs` - Cache des jobs scrapés

### Base de Données Persistante
- `GET /api/db/jobs` - Tous les jobs sauvés
- `POST /api/db/search` - Recherche avancée
- `GET /api/db/jobs/{id}` - Job spécifique

## 🎯 Cas d'Usage

### 1. Analyser le Marché Python
```bash
curl -X POST "http://localhost:8000/api/scrape?query=python&location=France"
curl "http://localhost:8000/api/keywords"
```

### 2. Recherche d'Emploi React à Distance
```bash
curl -X POST "http://localhost:8000/api/scrape?query=react&location=Remote"
curl -X POST "http://localhost:8000/api/db/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"react","location":"remote"}'
```

### 3. Analyse de Tendances
```bash
# Scraper plusieurs technologies
curl -X POST "http://localhost:8000/api/scrape?query=fullstack&location=Paris"
curl -X POST "http://localhost:8000/api/scrape?query=devops&location=Lyon"

# Voir les tendances
curl "http://localhost:8000/api/stats"
```

## 🛠️ Administration

### Arrêter l'Application
```bash
# Méthode 1: Depuis les logs du script
kill [PID_API] [PID_FRONTEND]

# Méthode 2: Kill général
pkill -f "python api/main_simple.py"
pkill -f "npm run dev"
```

### Nettoyer les Logs
```bash
rm api-simple.log frontend.log
```

### Sauvegarder la Base de Données
```bash
cp backend/jobs_simple.db backup_jobs_$(date +%Y%m%d).db
```

## 📈 Évolutions Possibles

### Prochaines Étapes Suggérées
1. **Interface Web Interactive** - Formulaires de recherche
2. **Authentification** - Comptes utilisateurs
3. **Alertes Email** - Notifications nouvelles offres
4. **API Publique** - Partage de données
5. **Machine Learning** - Recommandations personnalisées

### Intégrations Avancées
- **Slack/Discord Bot** - Notifications temps réel
- **Dashboard Analytics** - Graphiques interactifs
- **Export Excel** - Rapports automatisés
- **API Tier** - Scraping à la demande

## 🔧 Dépannage

### Problèmes Courants
- **Port occupé** : Changer les ports dans les scripts
- **Base corrompue** : Supprimer `jobs_simple.db` pour recréer
- **Scraping lent** : Normal, données simulées instantanées

### Logs Utiles
```bash
tail -f api-simple.log     # Erreurs API
tail -f frontend.log       # Erreurs React
```

## 🎯 Performance

Votre application peut gérer :
- **Scraping** : 6 jobs par source par requête
- **Base données** : Milliers d'offres
- **API** : Centaines de requêtes/minute
- **Recherche** : Instantanée sur mots-clés

---

**🎉 Félicitations ! Votre Job Keywords Analyzer est prêt pour l'utilisation professionnelle.**


