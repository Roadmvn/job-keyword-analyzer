#!/bin/bash
# Script MINIMAL - API sans authentification

echo "🚀 Job Keywords Analyzer - Version MINIMALE"
echo "============================================"
echo "🎯 API simplifiée SANS authentification pour test rapide"
echo ""

# Nettoyer SEULEMENT nos processus de l'application
echo "🧹 Nettoyage sécurisé des processus de l'application..."

# Arrêter les processus sauvegardés (plus sûr)
if [ -f .api-simple.pid ]; then
    API_PID=$(cat .api-simple.pid 2>/dev/null || echo "")
    if [ ! -z "$API_PID" ] && kill -0 $API_PID 2>/dev/null; then
        echo "  🔪 Arrêt API (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi
    rm -f .api-simple.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid 2>/dev/null || echo "")
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "  🔪 Arrêt Frontend (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    rm -f .frontend.pid
fi

# Résoudre les chemins de façon robuste
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="/home/roadmvn/projet/job-keyword-analyzer"

PORT_3000_PID=$(lsof -ti :3000 2>/dev/null | head -1 || echo "")
if [ ! -z "$PORT_3000_PID" ]; then
    # Vérifier que c'est bien un processus node/npm ET dans notre projet
    PROCESS_CMD=$(ps -p $PORT_3000_PID -o comm= 2>/dev/null || echo "")
    PROCESS_CWD=$(pwdx $PORT_3000_PID 2>/dev/null | cut -d' ' -f2- || echo "")
    
    if ([[ "$PROCESS_CMD" == *"node"* ]] || [[ "$PROCESS_CMD" == *"npm"* ]]) && [[ "$PROCESS_CWD" == *"$PROJECT_PATH"* ]]; then
        echo "  🔪 Arrêt processus Node de notre projet sur port 3000 (PID: $PORT_3000_PID)"
        kill $PORT_3000_PID 2>/dev/null || true
    else
        echo "  ⚠️  Processus sur port 3000 (PID: $PORT_3000_PID) n'est pas de notre projet, ignoré"
    fi
fi

PORT_8000_PID=$(lsof -ti :8000 2>/dev/null | head -1 || echo "")
if [ ! -z "$PORT_8000_PID" ]; then
    # Vérifier que c'est bien un processus python ET dans notre projet
    PROCESS_CMD=$(ps -p $PORT_8000_PID -o comm= 2>/dev/null || echo "")
    PROCESS_CWD=$(pwdx $PORT_8000_PID 2>/dev/null | cut -d' ' -f2- || echo "")
    
    if [[ "$PROCESS_CMD" == *"python"* ]] && [[ "$PROCESS_CWD" == *"$PROJECT_PATH"* ]]; then
        echo "  🔪 Arrêt processus Python de notre projet sur port 8000 (PID: $PORT_8000_PID)"
        kill $PORT_8000_PID 2>/dev/null || true
    else
        echo "  ⚠️  Processus sur port 8000 (PID: $PORT_8000_PID) n'est pas de notre projet, ignoré"
    fi
fi

sleep 2
echo "✅ Nettoyage sécurisé terminé"

echo "🔧 Démarrage Backend Minimal..."
cd "$SCRIPT_DIR/backend" || exit 1
# Charger .env si présent (pour DATABASE_URL, etc.)
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    . "$SCRIPT_DIR/.env"
    set +a
fi
# Préparer l'environnement Python minimal
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "  ⚠️  Environnement Python 'venv' introuvable, création automatique..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Variables simples
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Lancer API simplifiée
nohup python api/main_simple.py > "$SCRIPT_DIR/api-simple.log" 2>&1 &
API_PID=$!
echo "✅ API Minimale démarrée (PID: $API_PID)"

# Démarrer Frontend
echo "🎨 Démarrage Frontend..."
cd "$SCRIPT_DIR/frontend"  
# Installer les dépendances si absentes
if [ ! -d node_modules ]; then
    echo "  📦 Installation des dépendances frontend (npm ci)..."
    npm ci --no-audit --no-fund
fi
nohup npm run dev -- --host 0.0.0.0 --port 3000 > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend démarré (PID: $FRONTEND_PID)"

# Attendre
echo "⏳ Vérification des services..."
sleep 3

# Tests
echo ""
echo "🧪 Tests de Connectivité:"
curl -s http://localhost:8000/health >/dev/null && echo "  ✅ Backend API Minimal: OK" || echo "  ❌ Backend: ERREUR"
curl -s http://localhost:3000 >/dev/null && echo "  ✅ Frontend React: OK" || echo "  ❌ Frontend: ERREUR"

echo ""
echo "🌐 Application Disponible:"
echo "  📍 API Minimal: http://localhost:8000"
echo "  📚 Documentation: http://localhost:8000/docs"
echo "  🎨 Frontend: http://localhost:3000"
echo ""
echo "📋 Logs:"
echo "  📄 API: tail -f $SCRIPT_DIR/api-simple.log"
echo "  📄 Frontend: tail -f $SCRIPT_DIR/frontend.log"
echo ""
echo "🛑 Pour arrêter: kill $API_PID $FRONTEND_PID"

# Sauvegarder PIDs
echo $API_PID > "$SCRIPT_DIR/.api-simple.pid"
echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"

echo ""
echo "🎉 Version minimale prête ! Testez dans votre navigateur."