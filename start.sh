#!/bin/bash

# 🚀 Script de démarrage amélioré pour Job Keywords Analyzer
# Utilisation: ./start.sh
# Compatible: bash, zsh, fish

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonctions utilitaires
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}🚀 Job Keywords Analyzer - Démarrage${NC}"
    echo -e "${BLUE}============================================${NC}"
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

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Fonction pour détecter le shell
detect_shell() {
    if [ -n "$FISH_VERSION" ]; then
        echo "fish"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    else
        echo "bash"  # Par défaut
    fi
}

# Vérifications préalables
check_prerequisites() {
    echo -e "\n${BLUE}🔍 Vérification des prérequis...${NC}"
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        echo "Installation sur CachyOS/Arch :"
        echo "  sudo pacman -S docker docker-compose"
        exit 1
    fi
    print_success "Docker installé"
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        echo "Installation sur CachyOS/Arch :"
        echo "  sudo pacman -S docker-compose"
        exit 1
    fi
    print_success "Docker Compose installé"
    
    # Vérifier si Docker daemon est démarré
    if ! docker info &> /dev/null; then
        print_warning "Docker daemon n'est pas démarré"
        echo "Tentative de démarrage..."
        if sudo systemctl start docker 2>/dev/null; then
            print_success "Docker daemon démarré"
        else
            print_error "Impossible de démarrer Docker. Exécutez :"
            echo "  sudo systemctl start docker"
            echo "  sudo systemctl enable docker"
            exit 1
        fi
    fi
    print_success "Docker daemon actif"
    
    # Vérifier les permissions Docker
    if ! docker ps &> /dev/null; then
        print_warning "Permissions Docker insuffisantes"
        echo "Solutions possibles :"
        echo "  1. Redémarrer votre session après avoir ajouté votre utilisateur au groupe docker"
        echo "  2. Exécuter: newgrp docker"
        echo "  3. Utiliser sudo temporairement"
        echo ""
        read -p "Voulez-vous continuer avec sudo ? (y/N): " use_sudo
        if [[ $use_sudo =~ ^[Yy]$ ]]; then
            DOCKER_CMD="sudo docker-compose"
            print_warning "Utilisation de sudo pour Docker"
        else
            print_error "Permissions Docker requises. Redémarrez votre session."
            exit 1
        fi
    else
        DOCKER_CMD="docker-compose"
        print_success "Permissions Docker OK"
    fi
}

# Vérifier les ports
check_ports() {
    echo -e "\n${BLUE}🔍 Vérification des ports...${NC}"
    
    ports=(3000 8000 3306 6379 9200)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if ss -tlnp 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=($port)
            print_warning "Port $port occupé"
            
            # Identifier le conteneur Docker s'il y en a un
            container=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null || echo "")
            if [ ! -z "$container" ]; then
                echo "  └─ Utilisé par: $container (Docker)"
            fi
        else
            print_success "Port $port libre"
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo ""
        print_warning "Ports occupés détectés: ${occupied_ports[*]}"
        read -p "Voulez-vous arrêter les conteneurs Docker conflictuels ? (y/N): " stop_containers
        if [[ $stop_containers =~ ^[Yy]$ ]]; then
            for port in "${occupied_ports[@]}"; do
                container=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null || echo "")
                if [ ! -z "$container" ]; then
                    echo "Arrêt du conteneur: $container"
                    docker stop "$container" &> /dev/null || true
                fi
            done
            print_success "Conteneurs conflictuels arrêtés"
        fi
    fi
}

# Créer/vérifier le fichier .env
setup_env() {
    echo -e "\n${BLUE}📝 Configuration environnement...${NC}"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Fichier .env créé depuis .env.example"
            print_warning "Modifiez les mots de passe dans .env avant la production!"
        else
            print_error "Fichier .env.example manquant"
            exit 1
        fi
    else
        print_success "Fichier .env existant"
    fi
}

# Lancer les services avec health check
launch_services() {
    local services="$1"
    local description="$2"
    
    echo -e "\n${BLUE}🐳 $description${NC}"
    
    # Construire la commande Docker
    if [ -z "$services" ]; then
        cmd="$DOCKER_CMD up -d"
    else
        cmd="$DOCKER_CMD up -d $services"
    fi
    
    print_info "Exécution: $cmd"
    
    # Lancer les services
    if eval $cmd; then
        print_success "Services lancés"
        
        # Attendre que les services soient prêts
        echo "Attente de la disponibilité des services..."
        sleep 5
        
        # Vérifier la santé des services
        if command -v docker-compose &> /dev/null; then
            echo ""
            eval "$DOCKER_CMD ps"
        fi
        
        return 0
    else
        print_error "Échec du lancement des services"
        echo "Consultez les logs avec: $DOCKER_CMD logs"
        return 1
    fi
}

# Instructions post-lancement
show_instructions() {
    local mode="$1"
    local shell_type=$(detect_shell)
    
    echo -e "\n${GREEN}✅ Lancement réussi!${NC}"
    
    case $mode in
        1)
            echo -e "\n${CYAN}🌐 Services disponibles :${NC}"
            echo "📍 Frontend:          http://localhost:3000"
            echo "📍 API:               http://localhost:8000"
            echo "📍 Documentation API: http://localhost:8000/docs"
            echo "📍 Elasticsearch:     http://localhost:9200"
            echo "📍 MySQL:             localhost:3306"
            echo ""
            echo "🎯 Première étape recommandée :"
            echo "  1. Ouvrez http://localhost:3000"
            echo "  2. Cliquez sur '🧪 Ajouter données test'"
            ;;
        2)
            echo -e "\n${CYAN}👨‍💻 Instructions pour le développement backend :${NC}"
            echo "Dans un nouveau terminal, exécutez :"
            echo "  cd backend"
            echo "  python -m venv venv"
            if [ "$shell_type" = "fish" ]; then
                echo "  source venv/bin/activate.fish"
            else
                echo "  source venv/bin/activate"
            fi
            echo "  pip install -r requirements.txt"
            echo "  uvicorn api.main:app --reload"
            echo ""
            echo "📍 API sera disponible sur: http://localhost:8000"
            ;;
        3)
            echo -e "\n${CYAN}🎨 Instructions pour le développement frontend :${NC}"
            echo "Dans un nouveau terminal, exécutez :"
            echo "  cd frontend"
            echo "  npm install"
            echo "  npm run dev"
            echo ""
            echo "📍 Frontend sera disponible sur: http://localhost:3000"
            ;;
        4|5)
            echo -e "\n${CYAN}🔧 Services d'infrastructure lancés${NC}"
            echo "📍 Elasticsearch: http://localhost:9200"
            echo "📍 MySQL:         localhost:3306"
            echo "📍 Redis:         localhost:6379"
            ;;
    esac
    
    echo -e "\n${BLUE}📚 Commandes utiles :${NC}"
    echo "  $DOCKER_CMD ps              # État des services"
    echo "  $DOCKER_CMD logs -f         # Voir les logs en temps réel"
    echo "  $DOCKER_CMD logs [service]  # Logs d'un service spécifique"
    echo "  $DOCKER_CMD down            # Arrêter tous les services"
    echo "  ./docker-helper             # Script d'aide pour la gestion Docker"
    
    echo -e "\n${BLUE}📖 Documentation complète:${NC} README.md"
}

# Menu principal
show_menu() {
    echo -e "\n${BLUE}📋 Choisissez votre mode de démarrage :${NC}"
    echo ""
    echo "1) 🐳 Application complète (Docker)"
    echo "2) 💻 Développement backend (Local Python + Docker DB)"
    echo "3) 🎨 Développement frontend (Local React + Docker Backend)"
    echo "4) 🔧 Services d'infrastructure uniquement (MySQL, Redis, Elasticsearch)"
    echo "5) 📊 Monitoring et outils"
    echo "6) 🆘 Aide et diagnostic"
    echo "7) ❌ Quitter"
    echo ""
}

# Aide et diagnostic
show_help() {
    echo -e "\n${BLUE}🆘 Aide et diagnostic${NC}"
    echo ""
    echo "🔍 Diagnostic rapide :"
    echo "  docker ps                    # Conteneurs actifs"
    echo "  docker-compose ps           # État du projet"
    echo "  docker-compose logs api     # Logs de l'API"
    echo "  docker-compose logs frontend # Logs du frontend"
    echo ""
    echo "🛠️ Résolution de problèmes :"
    echo "  ./docker-helper             # Script d'aide interactif"
    echo "  docker-compose down && docker-compose up -d  # Redémarrage complet"
    echo "  docker system prune         # Nettoyer Docker"
    echo ""
    echo "📖 Documentation :"
    echo "  README.md                   # Guide complet"
    echo "  docs/quick-start-docker.md  # Guide de démarrage rapide"
    echo ""
    echo "🌐 URLs importantes :"
    echo "  http://localhost:3000       # Frontend"
    echo "  http://localhost:8000/docs  # Documentation API"
    echo ""
}

# Fonction principale
main() {
    print_header
    
    # Vérifications préalables
    check_prerequisites
    check_ports
    setup_env
    
    while true; do
        show_menu
        read -p "Votre choix (1-7): " choice
        
        case $choice in
            1)
                if launch_services "" "Lancement de l'application complète"; then
                    show_instructions 1
                    break
                fi
                ;;
            2)
                if launch_services "mysql redis elasticsearch" "Lancement de l'infrastructure pour développement backend"; then
                    show_instructions 2
                    break
                fi
                ;;
            3)
                if launch_services "mysql redis elasticsearch api worker" "Lancement du backend pour développement frontend"; then
                    show_instructions 3
                    break
                fi
                ;;
            4)
                if launch_services "mysql redis elasticsearch" "Lancement des services d'infrastructure"; then
                    show_instructions 4
                    break
                fi
                ;;
            5)
                if launch_services "mysql redis elasticsearch" "Lancement des services de monitoring"; then
                    show_instructions 5
                    break
                fi
                ;;
            6)
                show_help
                echo ""
                read -p "Appuyez sur Entrée pour revenir au menu..."
                ;;
            7)
                print_success "Au revoir !"
                exit 0
                ;;
            *)
                print_error "Choix invalide. Veuillez choisir entre 1 et 7."
                echo ""
                read -p "Appuyez sur Entrée pour continuer..."
                ;;
        esac
    done
}

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 