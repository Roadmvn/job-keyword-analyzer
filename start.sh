#!/bin/bash

# Script de démarrage rapide pour Job Keywords Analyzer
# Utilisation: ./start.sh

echo "🚀 Job Keywords Analyzer - Démarrage"
echo "======================================"

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé"
    echo "⚠️  Modifiez les mots de passe dans .env avant la production!"
fi

echo ""
echo "Choisissez votre mode de démarrage:"
echo ""
echo "1) 🐳 Application complète (Docker)"
echo "2) 💻 Développement backend (Local Python + Docker DB)"
echo "3) 🎨 Développement frontend (Local React + Docker Backend)"
echo "4) 🔧 Services d'infrastructure uniquement (MySQL, Redis, Elasticsearch)"
echo "5) 📊 Monitoring et outils"
echo ""

read -p "Votre choix (1-5): " choice

case $choice in
    1)
        echo "🐳 Lancement de l'application complète..."
        docker-compose up -d
        echo ""
        echo "✅ Application lancée!"
        echo "📍 API: http://localhost:8000"
        echo "📍 Frontend: http://localhost:3000"
        echo "📍 Elasticsearch: http://localhost:9200"
        echo "📍 MySQL: localhost:3306"
        ;;
    2)
        echo "💻 Mode développement backend..."
        echo "Lancement des services d'infrastructure..."
        docker-compose up -d mysql redis elasticsearch
        echo "✅ Infrastructure prête!"
        echo "👨‍💻 Maintenant, dans un autre terminal:"
        echo "  cd backend"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        echo "  uvicorn api.main:app --reload"
        ;;
    3)
        echo "🎨 Mode développement frontend..."
        echo "Lancement du backend complet..."
        docker-compose up -d mysql redis elasticsearch api worker
        echo "✅ Backend prêt!"
        echo "👨‍💻 Maintenant, dans un autre terminal:"
        echo "  cd frontend"
        echo "  npm install"
        echo "  npm run dev"
        ;;
    4)
        echo "🔧 Services d'infrastructure uniquement..."
        docker-compose up -d mysql redis elasticsearch
        echo "✅ Infrastructure lancée!"
        ;;
    5)
        echo "📊 Monitoring et outils..."
        docker-compose up -d mysql redis elasticsearch
        echo "✅ Services de monitoring prêts!"
        echo "📍 Elasticsearch: http://localhost:9200"
        echo "📍 MySQL: localhost:3306 (utilisez DBeaver ou similaire)"
        ;;
    *)
        echo "❌ Choix invalide. Relancez le script."
        exit 1
        ;;
esac

echo ""
echo "📚 Commandes utiles:"
echo "  docker-compose logs -f     # Voir les logs"
echo "  docker-compose ps          # État des services"
echo "  docker-compose down        # Arrêter tout"
echo ""
echo "📖 Documentation complète: README.md" 