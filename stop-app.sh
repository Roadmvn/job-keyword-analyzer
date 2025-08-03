#!/bin/bash
# Script d'arrêt ultra-sécurisé pour Job Keywords Analyzer

echo "🛑 Arrêt sécurisé de Job Keywords Analyzer"
echo "==========================================="

# Variables pour vérifier que nous arrêtons bien nos processus
PROJECT_PATH="/home/roadmvn/projet1/job-keyword-analyzer"
STOPPED_COUNT=0

# Fonction pour vérifier si un processus appartient à notre projet
is_our_process() {
    local pid=$1
    local expected_path=$2
    
    if [ -z "$pid" ] || ! kill -0 $pid 2>/dev/null; then
        return 1  # Processus n'existe pas
    fi
    
    # Vérifier le répertoire de travail du processus
    local proc_cwd=$(pwdx $pid 2>/dev/null | cut -d' ' -f2- || echo "")
    if [[ "$proc_cwd" == *"$expected_path"* ]]; then
        return 0  # C'est notre processus
    fi
    
    return 1  # Pas notre processus
}

# Arrêter SEULEMENT nos processus sauvegardés
if [ -f .api-simple.pid ]; then
    API_PID=$(cat .api-simple.pid 2>/dev/null || echo "")
    if [ ! -z "$API_PID" ]; then
        if is_our_process $API_PID "$PROJECT_PATH"; then
            echo "  🔪 Arrêt API Job Keywords Analyzer (PID: $API_PID)"
            kill $API_PID 2>/dev/null || true
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo "  ⚠️  API PID $API_PID ne semble pas être notre processus, ignoré"
        fi
    fi
    rm -f .api-simple.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid 2>/dev/null || echo "")
    if [ ! -z "$FRONTEND_PID" ]; then
        if is_our_process $FRONTEND_PID "$PROJECT_PATH"; then
            echo "  🔪 Arrêt Frontend Job Keywords Analyzer (PID: $FRONTEND_PID)"
            kill $FRONTEND_PID 2>/dev/null || true
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo "  ⚠️  Frontend PID $FRONTEND_PID ne semble pas être notre processus, ignoré"
        fi
    fi
    rm -f .frontend.pid
fi

# Nettoyer les autres fichiers temporaires
rm -f .api.pid 2>/dev/null || true

if [ $STOPPED_COUNT -eq 0 ]; then
    echo "ℹ️  Aucun processus de Job Keywords Analyzer en cours d'exécution"
else
    echo "✅ $STOPPED_COUNT processus arrêté(s) avec succès"
fi

echo "🎉 Arrêt sécurisé terminé !"