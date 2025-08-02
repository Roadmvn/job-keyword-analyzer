#!/bin/bash
# Script de configuration de l'environnement de développement
# Job Keywords Analyzer

set -e  # Arrêter en cas d'erreur

echo "🚀 Configuration de l'environnement de développement Job Keywords Analyzer"
echo "========================================================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier les prérequis
check_prerequisites() {
    info "Vérification des prérequis..."
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 n'est pas installé"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
        error "Python 3.11+ requis (version actuelle: $PYTHON_VERSION)"
        exit 1
    fi
    success "Python $PYTHON_VERSION ✓"
    
    # Vérifier Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js n'est pas installé"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [[ $NODE_VERSION -lt 18 ]]; then
        error "Node.js 18+ requis (version actuelle: v$NODE_VERSION)"
        exit 1
    fi
    success "Node.js v$NODE_VERSION ✓"
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        warning "Docker n'est pas installé (optionnel pour le développement)"
    else
        success "Docker ✓"
    fi
    
    # Vérifier Git
    if ! command -v git &> /dev/null; then
        error "Git n'est pas installé"
        exit 1
    fi
    success "Git ✓"
}

# Configuration Backend Python
setup_backend() {
    info "Configuration du backend Python..."
    
    cd backend
    
    # Créer l'environnement virtuel
    if [[ ! -d "venv" ]]; then
        info "Création de l'environnement virtuel Python..."
        python3 -m venv venv
    fi
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Mettre à jour pip
    pip install --upgrade pip
    
    # Installer les dépendances
    info "Installation des dépendances Python..."
    pip install -r requirements.txt
    
    # Installer les dépendances de développement
    if [[ -f "requirements-dev.txt" ]]; then
        pip install -r requirements-dev.txt
    fi
    
    # Télécharger le modèle spaCy français
    info "Téléchargement du modèle spaCy français..."
    python -m spacy download fr_core_news_md
    
    success "Backend configuré ✓"
    cd ..
}

# Configuration Frontend React
setup_frontend() {
    info "Configuration du frontend React..."
    
    cd frontend
    
    # Installer les dépendances npm
    info "Installation des dépendances npm..."
    npm ci
    
    success "Frontend configuré ✓"
    cd ..
}

# Configuration Pre-commit
setup_precommit() {
    info "Configuration de pre-commit..."
    
    # Installer pre-commit dans l'environnement virtuel
    source backend/venv/bin/activate
    pip install pre-commit
    
    # Installer les hooks
    pre-commit install
    pre-commit install --hook-type commit-msg
    
    # Tester les hooks
    info "Test des hooks pre-commit..."
    pre-commit run --all-files || warning "Certains hooks pre-commit ont échoué (normal lors de la première exécution)"
    
    success "Pre-commit configuré ✓"
}

# Configuration de la base de données
setup_database() {
    info "Configuration de la base de données..."
    
    # Copier le fichier d'environnement
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            info "Fichier .env créé depuis .env.example"
            warning "Veuillez modifier .env avec vos paramètres"
        else
            warning "Aucun fichier .env.example trouvé"
        fi
    fi
    
    # Démarrer les services Docker si disponible
    if command -v docker-compose &> /dev/null; then
        info "Démarrage des services Docker..."
        docker-compose up -d mysql redis elasticsearch
        
        # Attendre que les services soient prêts
        info "Attente du démarrage des services..."
        sleep 30
        
        # Créer les migrations
        source backend/venv/bin/activate
        cd backend
        
        if [[ -f "alembic.ini" ]]; then
            info "Application des migrations de base de données..."
            alembic upgrade head
        fi
        
        cd ..
    else
        warning "Docker Compose non disponible - configuration manuelle de la BDD requise"
    fi
    
    success "Base de données configurée ✓"
}

# Configuration de l'IDE
setup_ide() {
    info "Configuration de l'IDE..."
    
    # Créer le dossier .vscode s'il n'existe pas
    mkdir -p .vscode
    
    # Configuration VS Code
    cat > .vscode/settings.json << EOF
{
    "python.defaultInterpreterPath": "./backend/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.associations": {
        "*.env": "dotenv"
    },
    "eslint.workingDirectories": ["frontend"],
    "typescript.preferences.importModuleSpecifier": "relative"
}
EOF
    
    # Extensions recommandées
    cat > .vscode/extensions.json << EOF
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.pylint",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode",
        "dbaeumer.vscode-eslint",
        "ms-vscode.vscode-typescript-next",
        "formulahendry.auto-rename-tag",
        "christian-kohler.path-intellisense",
        "ms-vscode.vscode-json",
        "redhat.vscode-yaml",
        "ms-vscode-remote.remote-containers"
    ]
}
EOF
    
    success "Configuration IDE créée ✓"
}

# Créer des scripts utilitaires
create_scripts() {
    info "Création des scripts utilitaires..."
    
    # Script de démarrage rapide
    cat > start-dev.sh << 'EOF'
#!/bin/bash
# Script de démarrage rapide pour le développement

echo "🚀 Démarrage de l'environnement de développement..."

# Démarrer les services Docker
if command -v docker-compose &> /dev/null; then
    echo "Démarrage des services Docker..."
    docker-compose up -d mysql redis elasticsearch
fi

# Démarrer le backend
echo "Démarrage du backend..."
cd backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Démarrer le frontend
echo "Démarrage du frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Services démarrés:"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"

# Fonction de nettoyage
cleanup() {
    echo "Arrêt des services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Attendre les signaux
wait
EOF
    
    chmod +x start-dev.sh
    
    # Script de tests
    cat > run-tests.sh << 'EOF'
#!/bin/bash
# Script pour exécuter tous les tests

echo "🧪 Exécution des tests..."

# Tests backend
echo "Tests backend..."
cd backend
source venv/bin/activate
pytest tests/ --verbose --cov=.
cd ..

# Tests frontend
echo "Tests frontend..."
cd frontend
npm test -- --watchAll=false --coverage
cd ..

echo "✅ Tests terminés"
EOF
    
    chmod +x run-tests.sh
    
    success "Scripts utilitaires créés ✓"
}

# Afficher les informations finales
show_final_info() {
    echo ""
    echo "========================================================================"
    success "Configuration terminée ! 🎉"
    echo ""
    echo "📝 Prochaines étapes :"
    echo "   1. Modifier le fichier .env avec vos paramètres"
    echo "   2. Démarrer l'environnement: ./start-dev.sh"
    echo "   3. Ouvrir http://localhost:3000 dans votre navigateur"
    echo ""
    echo "🛠️  Commandes utiles :"
    echo "   - Démarrer le dev: ./start-dev.sh"
    echo "   - Exécuter les tests: ./run-tests.sh"
    echo "   - Format du code: pre-commit run --all-files"
    echo "   - Migrations: cd backend && alembic revision --autogenerate -m 'message'"
    echo ""
    echo "📚 Documentation :"
    echo "   - API: http://localhost:8000/docs"
    echo "   - README: ./README.md"
    echo "   - Docs: ./docs/"
    echo ""
}

# Exécution principale
main() {
    check_prerequisites
    setup_backend
    setup_frontend
    setup_precommit
    setup_database
    setup_ide
    create_scripts
    show_final_info
}

# Gestion des erreurs
handle_error() {
    error "Une erreur s'est produite lors de la configuration"
    echo "Vérifiez les logs ci-dessus pour plus de détails"
    exit 1
}

trap handle_error ERR

# Lancer la configuration
main "$@"