# 📚 Documentation Job Keywords Analyzer

Bienvenue dans la documentation complète du projet Job Keywords Analyzer !

## 🚀 **Guides de Démarrage**

### Pour les Débutants
- 📖 [**README Principal**](../README.md) - Vue d'ensemble et installation
- ⚡ [**Guide de Démarrage Rapide Docker**](quick-start-docker.md) - Résoudre les problèmes courants

### Pour les Développeurs
- 🐳 [**Guide Complet de Gestion Docker**](docker-management.md) - Toutes les commandes Docker
- 🔧 [**Configuration Avancée**](../docker-compose.yml) - Fichier docker-compose détaillé

## 🛠️ **Outils Pratiques**

### Scripts d'Aide
- 🎯 [**Docker Helper Script**](../scripts/docker-helper.sh) - Script interactif pour gérer Docker
- ⚡ [**Raccourci Docker Helper**](../docker-helper) - Lancement rapide du script

### Utilisation des Scripts
```bash
# Depuis la racine du projet
./docker-helper                    # Script interactif complet
./scripts/docker-helper.sh         # Même script, chemin direct
```

## 📋 **Index des Problèmes Courants**

### 🔴 **Problèmes de Ports**
- **Port 3000 occupé** → [Guide Rapide](quick-start-docker.md#solution-rapide-aux-conflits-de-ports)
- **Conflit de conteneurs** → [Guide Complet](docker-management.md#diagnostic-des-conflits-de-ports)
- **Libérer un port** → [Script Helper](../docker-helper) → Option 5

### 🔴 **Problèmes de Conteneurs**
- **Conteneur qui ne démarre pas** → [Guide Complet](docker-management.md#commandes-durgence)
- **Conteneur en boucle** → [Guide Rapide](quick-start-docker.md#conteneur-qui-redémarre-en-boucle)
- **Nettoyer Docker** → [Script Helper](../docker-helper) → Option 6

### 🔴 **Problèmes de Performance**
- **Docker lent** → [Guide Complet](docker-management.md#nettoyage-complet-du-système)
- **Espace disque** → [Guide Rapide](quick-start-docker.md#no-space-left-on-device)
- **Monitoring** → [Guide Complet](docker-management.md#monitoring-et-informations)

## 🎯 **Workflows Recommandés**

### **Premier Démarrage**
1. Lire le [README Principal](../README.md)
2. Vérifier avec `./docker-helper` → Option 2
3. Démarrer avec `docker-compose up -d`

### **Résolution de Problème**
1. Lancer `./docker-helper`
2. Diagnostic → Option 2 (Ports)
3. Solution → Option 3, 5 ou 6 selon le problème
4. Redémarrage → Option 7

### **Développement au Quotidien**
1. `./docker-helper` → Option 1 (Lister conteneurs)
2. `docker-compose logs -f SERVICE` pour déboguer
3. `./docker-helper` → Option 7 pour redémarrer

## 📖 **Documentation Technique**

### Architecture
- **Frontend** : React + Vite (Port 3000)
- **Backend** : FastAPI + Python (Port 8000)
- **Base de données** : MySQL (Port 3306)
- **Cache** : Redis (Port 6379)
- **Recherche** : Elasticsearch (Ports 9200/9300)

### Configuration
- [**Variables d'environnement**](../README.md#variables-denvironnement-importantes)
- [**Docker Compose**](../docker-compose.yml)
- [**Structure du projet**](../README.md#architecture)

## 🆘 **Support et Aide**

### En cas de problème
1. **Consultez d'abord** : [Guide de Démarrage Rapide](quick-start-docker.md)
2. **Utilisez le script** : `./docker-helper`
3. **Documentation complète** : [Guide Docker](docker-management.md)

### Commandes d'Urgence
```bash
# Tout arrêter
docker stop $(docker ps -q)

# Tout nettoyer
docker system prune -f

# Redémarrer le projet
docker-compose up -d
```

### Contacts
- **Issues GitHub** : Pour signaler des bugs
- **Documentation** : Ce dossier `docs/`
- **Logs** : `docker-compose logs -f`

---

💡 **Astuce** : Marquez cette page en favoris et consultez-la chaque fois que vous avez une question !

## 🗂️ **Index des Fichiers**

```
docs/
├── README.md                 # ← Vous êtes ici
├── docker-management.md      # Guide complet Docker
├── quick-start-docker.md     # Guide de démarrage rapide
└── [autres guides à venir]

scripts/
├── docker-helper.sh          # Script principal d'aide
└── [autres scripts]

docker-helper                 # Raccourci vers le script
docker-compose.yml           # Configuration des services
README.md                    # Documentation principale
``` 