#!/usr/bin/env bash
set -euo pipefail

# Initialisation automatique de MySQL pour Job Keywords Analyzer
# - Crée la base, l'utilisateur et les privilèges
# - Lit les variables depuis .env si présent, sinon utilise des valeurs par défaut

ROOT_CMD="sudo mysql"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Charger .env s'il existe
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  . "$PROJECT_DIR/.env"
  set +a
fi

DB_NAME=${MYSQL_DATABASE:-job_analyzer}
DB_USER=${MYSQL_USER:-app_user}
DB_PASS=${MYSQL_PASSWORD:-app_password}
DB_HOST_LOCAL=${DB_HOST_LOCAL:-127.0.0.1}

echo "🚀 Initialisation MySQL..."

SQL="
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
"

echo "🗄️  Création base/utilisateur/privilèges..."
echo "$SQL" | $ROOT_CMD

echo "🔍 Vérification:"
$ROOT_CMD -e "SHOW DATABASES LIKE '$DB_NAME';" | cat
$ROOT_CMD -e "SELECT User, Host FROM mysql.user WHERE User='$DB_USER';" | cat

echo "✅ Terminé. Exemple de configuration .env (si absent):"
cat <<EOF
DATABASE_URL=mysql://$DB_USER:$DB_PASS@127.0.0.1:3306/$DB_NAME
EOF

echo "ℹ️  Démarrage de l'application: ./start-minimal.sh"


