# 🐳 Guide de Gestion des Conteneurs Docker

Ce guide vous aide à identifier, gérer et nettoyer les conteneurs Docker qui peuvent entrer en conflit avec votre projet.

## 📋 **Lister les Conteneurs**

### **Conteneurs actifs (en cours d'exécution)**
```bash
# Liste simple
docker ps

# Liste détaillée avec les ports
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Liste avec tailles
docker ps -s
```

### **Tous les conteneurs (actifs + arrêtés)**
```bash
# Tous les conteneurs
docker ps -a

# Format personnalisé
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"
```

### **Filtrer par critères**
```bash
# Par statut
docker ps -f status=running    # Conteneurs actifs
docker ps -f status=exited     # Conteneurs arrêtés

# Par nom
docker ps -f name=student      # Conteneurs contenant "student"

# Par port
docker ps --filter "publish=3000"  # Conteneurs utilisant le port 3000
```

## 🛑 **Arrêter les Conteneurs**

### **Arrêt simple (gracieux)**
```bash
# Un conteneur spécifique
docker stop CONTAINER_NAME_OR_ID

# Plusieurs conteneurs
docker stop container1 container2 container3

# Tous les conteneurs actifs
docker stop $(docker ps -q)
```

### **Arrêt forcé (si bloqué)**
```bash
# Forcer l'arrêt d'un conteneur
docker kill CONTAINER_NAME_OR_ID

# Forcer l'arrêt de tous les conteneurs
docker kill $(docker ps -q)
```

## 🗑️ **Supprimer les Conteneurs**

### **Suppression après arrêt**
```bash
# Supprimer un conteneur arrêté
docker rm CONTAINER_NAME_OR_ID

# Supprimer plusieurs conteneurs
docker rm container1 container2

# Supprimer tous les conteneurs arrêtés
docker rm $(docker ps -aq -f status=exited)
```

### **Suppression forcée (conteneur actif)**
```bash
# Arrêter ET supprimer d'un coup
docker rm -f CONTAINER_NAME_OR_ID

# Forcer la suppression de tous les conteneurs
docker rm -f $(docker ps -aq)
```

## ⚡ **Commandes Pratiques Combinées**

### **Nettoyer par projet**
```bash
# Arrêter tous les conteneurs d'un projet spécifique
docker stop $(docker ps -q -f name=student)

# Supprimer tous les conteneurs d'un projet
docker rm -f $(docker ps -aq -f name=student)

# Nettoyer les conteneurs d'une image spécifique
docker rm -f $(docker ps -aq -f ancestor=nginx)
```

### **Nettoyage complet du système**
```bash
# Supprimer tous les conteneurs arrêtés
docker container prune

# Supprimer conteneurs, réseaux, images non utilisées
docker system prune

# Nettoyage complet (ATTENTION : supprime tout !)
docker system prune -a --volumes
```

## 🔍 **Diagnostic des Conflits de Ports**

### **Identifier qui utilise un port**
```bash
# Méthode 1 : ss (recommandée)
ss -tlnp | grep :3000

# Méthode 2 : lsof
lsof -i :3000

# Méthode 3 : fuser
fuser -v 3000/tcp

# Méthode 4 : Docker
docker ps --filter "publish=3000"
```

### **Libérer un port occupé**
```bash
# Si c'est un conteneur Docker
docker stop $(docker ps -q --filter "publish=3000")

# Si c'est un processus système
fuser -k 3000/tcp

# Ou identifier le PID et l'arrêter proprement
kill -15 PID
```

## 📊 **Monitoring et Informations**

### **Utilisation des ressources**
```bash
# Statistiques en temps réel
docker stats

# Informations détaillées d'un conteneur
docker inspect CONTAINER_NAME

# Logs d'un conteneur
docker logs CONTAINER_NAME
docker logs -f CONTAINER_NAME  # En temps réel
```

### **Informations sur les réseaux**
```bash
# Lister les réseaux Docker
docker network ls

# Voir les conteneurs d'un réseau
docker network inspect NETWORK_NAME
```

## 🚨 **Commandes d'Urgence**

### **En cas de problème majeur**
```bash
# Arrêter TOUS les conteneurs
docker stop $(docker ps -q)

# Supprimer TOUS les conteneurs
docker rm -f $(docker ps -aq)

# Nettoyer complètement Docker
docker system prune -a --volumes --force

# Redémarrer le service Docker (Linux)
sudo systemctl restart docker
```

## 🎯 **Cas Pratiques Fréquents**

### **Libérer le port 3000 pour notre projet**
```bash
# 1. Identifier le conteneur
docker ps --filter "publish=3000"

# 2. Arrêter le conteneur spécifique
docker stop student_backend

# 3. Le supprimer si plus nécessaire
docker rm student_backend

# 4. Vérifier que le port est libre
ss -tlnp | grep :3000
```

### **Nettoyer avant un nouveau déploiement**
```bash
# Arrêter les conteneurs du projet actuel
docker-compose down

# Supprimer les conteneurs orphelins
docker-compose down --remove-orphans

# Reconstruire proprement
docker-compose up --build -d
```

### **Dépannage rapide**
```bash
# Voir tous les conteneurs avec leurs ports
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"

# Arrêter les conteneurs problématiques
docker stop $(docker ps -q -f name=problematique)

# Redémarrer un service spécifique
docker-compose restart SERVICE_NAME
```

## ⚠️ **Bonnes Pratiques**

1. **Toujours identifier avant de supprimer** : Utilisez `docker ps` avant `docker rm`
2. **Arrêt gracieux d'abord** : Préférez `docker stop` à `docker kill`
3. **Sauvegardez vos données** : Vérifiez les volumes avant `docker system prune`
4. **Utilisez des noms explicites** : `--name mon-projet-frontend` 
5. **Docker Compose pour les projets** : Plus facile à gérer que les conteneurs individuels

## 📝 **Alias Utiles à Ajouter dans ~/.zshrc**

```bash
# Aliases Docker pratiques
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dpsa='docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"'
alias dstop='docker stop $(docker ps -q)'
alias dclean='docker rm $(docker ps -aq -f status=exited)'
alias dsys='docker system prune'

# Recharger les aliases
source ~/.zshrc
```

---

💡 **Astuce** : Bookmark cette page et gardez-la à portée de main pour résoudre rapidement les conflits de conteneurs Docker ! 