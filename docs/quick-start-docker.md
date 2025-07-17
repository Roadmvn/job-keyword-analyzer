# 🚀 Guide de Démarrage Rapide - Docker

Ce guide vous aide à résoudre rapidement les problèmes courants de Docker.

## ⚡ **Solution Rapide aux Conflits de Ports**

### **Problème** : "Port 3000 is already in use"

```bash
# 🎯 Solution en 3 étapes

# 1. Identifier qui utilise le port
docker ps --filter "publish=3000"

# 2. Arrêter le conteneur coupable
docker stop CONTAINER_NAME

# 3. Relancer votre projet
docker-compose up -d
```

## 🛠️ **Script d'Aide Automatique**

Le plus simple est d'utiliser notre script interactif :

```bash
# Lancer le menu d'aide
./docker-helper
```

Le script vous guide automatiquement pour :
- ✅ Lister tous les conteneurs
- ✅ Identifier les conflits de ports  
- ✅ Arrêter des conteneurs spécifiques
- ✅ Nettoyer les conteneurs inutiles
- ✅ Redémarrer le projet proprement

## 🔧 **Commandes d'Urgence**

### **Arrêter TOUS les conteneurs**
```bash
docker stop $(docker ps -q)
```

### **Supprimer TOUS les conteneurs arrêtés**
```bash
docker container prune -f
```

### **Libérer un port spécifique (exemple: 3000)**
```bash
# Méthode Docker
docker stop $(docker ps -q --filter "publish=3000")

# Méthode système (si pas Docker)
fuser -k 3000/tcp
```

### **Redémarrer Docker complètement**
```bash
sudo systemctl restart docker
```

## 📋 **Diagnostic Rapide**

### **Vérifier l'état des services**
```bash
# Conteneurs actifs avec ports
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Vérifier les ports système
ss -tlnp | grep -E ":(3000|8000|3306|6379|9200)"

# Vérifier la santé des conteneurs
docker ps --filter "health=healthy"
```

### **Logs en cas de problème**
```bash
# Logs de tous les services
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f frontend

# Logs des dernières 50 lignes
docker-compose logs --tail=50 api
```

## 🎯 **Workflow de Résolution de Problème**

1. **🔍 Diagnostic** : `./docker-helper` → Option 2 (Vérifier les ports)
2. **🛑 Arrêt** : `./docker-helper` → Option 3 (Arrêter conteneur)
3. **🧹 Nettoyage** : `./docker-helper` → Option 6 (Nettoyer Docker)
4. **🔄 Redémarrage** : `./docker-helper` → Option 7 (Redémarrer projet)

## ⚠️ **Erreurs Courantes et Solutions**

### **"Cannot connect to the Docker daemon"**
```bash
# Démarrer Docker
sudo systemctl start docker

# Vérifier le statut
sudo systemctl status docker
```

### **"Permission denied" lors de l'exécution de docker**
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Puis se reconnecter ou faire
newgrp docker
```

### **"No space left on device"**
```bash
# Nettoyer complètement Docker
docker system prune -a --volumes -f

# Vérifier l'espace disque
df -h
```

### **Conteneur qui redémarre en boucle**
```bash
# Voir les logs pour identifier le problème
docker logs CONTAINER_NAME

# Vérifier la configuration
docker inspect CONTAINER_NAME
```

## 💡 **Astuces Pro**

### **Aliases utiles pour ~/.zshrc**
```bash
# Ajouter à votre ~/.zshrc
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dstop='docker stop $(docker ps -q)'
alias dclean='docker container prune -f'
alias dlogs='docker-compose logs -f'

# Recharger
source ~/.zshrc
```

### **Surveillance en temps réel**
```bash
# Voir l'utilisation des ressources
docker stats

# Surveiller les logs en temps réel
docker-compose logs -f | grep -E "(ERROR|WARN|FATAL)"
```

---

🎯 **Pour aller plus loin** : Consultez le [Guide complet](docker-management.md) pour des techniques avancées ! 