#!/bin/bash

# 🐳 Script d'aide pour la gestion Docker
# Automatise les tâches courantes de gestion des conteneurs

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}🐳 Docker Helper - Gestion des Conteneurs${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour lister les conteneurs
list_containers() {
    echo -e "\n${BLUE}📋 Conteneurs actifs :${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" 2>/dev/null || {
        print_error "Impossible de lister les conteneurs. Docker est-il démarré ?"
        return 1
    }
    
    echo -e "\n${BLUE}📋 Tous les conteneurs :${NC}"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>/dev/null
}

# Fonction pour vérifier les ports
check_ports() {
    echo -e "\n${BLUE}🔍 Vérification des ports courants :${NC}"
    
    ports=(3000 3001 8000 6379 3306 9200)
    
    for port in "${ports[@]}"; do
        if ss -tlnp | grep -q ":$port "; then
            echo -e "${YELLOW}Port $port : OCCUPÉ${NC}"
            # Identifier quel conteneur utilise ce port
            container=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null || echo "")
            if [ ! -z "$container" ]; then
                echo -e "  └─ Utilisé par le conteneur Docker: ${GREEN}$container${NC}"
            else
                echo -e "  └─ Utilisé par un processus système"
            fi
        else
            echo -e "${GREEN}Port $port : LIBRE${NC}"
        fi
    done
}

# Fonction pour arrêter un conteneur spécifique
stop_container() {
    echo -e "\n${BLUE}🛑 Arrêt d'un conteneur${NC}"
    list_containers
    
    echo -e "\n${YELLOW}Entrez le nom ou ID du conteneur à arrêter :${NC}"
    read -r container_name
    
    if [ -z "$container_name" ]; then
        print_error "Nom de conteneur non fourni"
        return 1
    fi
    
    if docker stop "$container_name" 2>/dev/null; then
        print_success "Conteneur '$container_name' arrêté"
    else
        print_error "Impossible d'arrêter le conteneur '$container_name'"
    fi
}

# Fonction pour supprimer un conteneur
remove_container() {
    echo -e "\n${BLUE}🗑️  Suppression d'un conteneur${NC}"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    
    echo -e "\n${YELLOW}Entrez le nom ou ID du conteneur à supprimer :${NC}"
    read -r container_name
    
    if [ -z "$container_name" ]; then
        print_error "Nom de conteneur non fourni"
        return 1
    fi
    
    echo -e "${YELLOW}Voulez-vous forcer la suppression (y/N) ?${NC}"
    read -r force
    
    if [[ $force =~ ^[Yy]$ ]]; then
        if docker rm -f "$container_name" 2>/dev/null; then
            print_success "Conteneur '$container_name' supprimé (forcé)"
        else
            print_error "Impossible de supprimer le conteneur '$container_name'"
        fi
    else
        if docker rm "$container_name" 2>/dev/null; then
            print_success "Conteneur '$container_name' supprimé"
        else
            print_error "Impossible de supprimer le conteneur '$container_name'. Essayez de l'arrêter d'abord."
        fi
    fi
}

# Fonction pour libérer un port spécifique
free_port() {
    echo -e "\n${BLUE}🔓 Libération d'un port${NC}"
    echo -e "${YELLOW}Entrez le numéro de port à libérer :${NC}"
    read -r port
    
    if [ -z "$port" ]; then
        print_error "Numéro de port non fourni"
        return 1
    fi
    
    # Vérifier si le port est utilisé par Docker
    container=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null || echo "")
    
    if [ ! -z "$container" ]; then
        echo -e "${YELLOW}Le port $port est utilisé par le conteneur Docker: $container${NC}"
        echo -e "${YELLOW}Voulez-vous arrêter ce conteneur ? (y/N)${NC}"
        read -r confirm
        
        if [[ $confirm =~ ^[Yy]$ ]]; then
            if docker stop "$container" 2>/dev/null; then
                print_success "Conteneur '$container' arrêté, port $port libéré"
            else
                print_error "Impossible d'arrêter le conteneur '$container'"
            fi
        fi
    else
        # Vérifier si c'est un processus système
        if ss -tlnp | grep -q ":$port "; then
            print_warning "Le port $port est utilisé par un processus système"
            echo -e "${YELLOW}Voulez-vous essayer de libérer le port avec fuser ? (y/N)${NC}"
            read -r confirm
            
            if [[ $confirm =~ ^[Yy]$ ]]; then
                if fuser -k "$port/tcp" 2>/dev/null; then
                    print_success "Port $port libéré"
                else
                    print_error "Impossible de libérer le port $port"
                fi
            fi
        else
            print_success "Le port $port est déjà libre"
        fi
    fi
}

# Fonction de nettoyage
cleanup_docker() {
    echo -e "\n${BLUE}🧹 Nettoyage Docker${NC}"
    echo -e "${YELLOW}Choisissez le type de nettoyage :${NC}"
    echo "1. Conteneurs arrêtés seulement"
    echo "2. Conteneurs + images non utilisées"
    echo "3. Nettoyage complet (ATTENTION: supprime tout)"
    echo "4. Annuler"
    
    read -r choice
    
    case $choice in
        1)
            if docker container prune -f 2>/dev/null; then
                print_success "Conteneurs arrêtés supprimés"
            else
                print_error "Erreur lors du nettoyage des conteneurs"
            fi
            ;;
        2)
            if docker system prune -f 2>/dev/null; then
                print_success "Conteneurs et images non utilisées supprimés"
            else
                print_error "Erreur lors du nettoyage système"
            fi
            ;;
        3)
            print_warning "ATTENTION: Cette action supprimera TOUS les conteneurs, images et volumes non utilisés"
            echo -e "${YELLOW}Êtes-vous sûr ? Tapez 'SUPPRIMER' pour confirmer :${NC}"
            read -r confirm
            
            if [ "$confirm" = "SUPPRIMER" ]; then
                if docker system prune -a --volumes -f 2>/dev/null; then
                    print_success "Nettoyage complet effectué"
                else
                    print_error "Erreur lors du nettoyage complet"
                fi
            else
                print_warning "Nettoyage annulé"
            fi
            ;;
        4)
            print_warning "Nettoyage annulé"
            ;;
        *)
            print_error "Choix invalide"
            ;;
    esac
}

# Fonction pour redémarrer notre projet
restart_project() {
    echo -e "\n${BLUE}🔄 Redémarrage du projet Job Analyzer${NC}"
    
    if [ -f "docker-compose.yml" ]; then
        print_warning "Arrêt des services..."
        docker-compose down 2>/dev/null || true
        
        print_warning "Démarrage des services..."
        if docker-compose up -d 2>/dev/null; then
            print_success "Projet redémarré avec succès"
            echo -e "\n${GREEN}Services disponibles :${NC}"
            echo "- Frontend: http://localhost:3000"
            echo "- API: http://localhost:8000"
            echo "- Documentation API: http://localhost:8000/docs"
        else
            print_error "Erreur lors du redémarrage du projet"
        fi
    else
        print_error "Fichier docker-compose.yml non trouvé dans le répertoire courant"
    fi
}

# Menu principal
show_menu() {
    echo -e "\n${BLUE}📋 Que voulez-vous faire ?${NC}"
    echo "1. 📋 Lister les conteneurs"
    echo "2. 🔍 Vérifier les ports"
    echo "3. 🛑 Arrêter un conteneur"
    echo "4. 🗑️  Supprimer un conteneur"
    echo "5. 🔓 Libérer un port"
    echo "6. 🧹 Nettoyer Docker"
    echo "7. 🔄 Redémarrer le projet"
    echo "8. ❌ Quitter"
    
    echo -e "\n${YELLOW}Votre choix (1-8) :${NC}"
}

# Fonction principale
main() {
    print_header
    
    # Vérifier si Docker est disponible
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé ou n'est pas dans le PATH"
        exit 1
    fi
    
    # Vérifier si Docker daemon est démarré
    if ! docker info &> /dev/null; then
        print_error "Docker daemon n'est pas démarré"
        exit 1
    fi
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) list_containers ;;
            2) check_ports ;;
            3) stop_container ;;
            4) remove_container ;;
            5) free_port ;;
            6) cleanup_docker ;;
            7) restart_project ;;
            8) 
                print_success "Au revoir !"
                exit 0
                ;;
            *)
                print_error "Choix invalide. Veuillez choisir entre 1 et 8."
                ;;
        esac
        
        echo -e "\n${YELLOW}Appuyez sur Entrée pour continuer...${NC}"
        read -r
    done
}

# Exécution du script
main "$@" 