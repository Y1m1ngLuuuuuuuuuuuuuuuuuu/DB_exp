#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

CONTAINER_NAME="${OPENGAUSS_CONTAINER:-course-opengauss}"
DB_NAME="${OPENGAUSS_DB:-course_system}"
DB_USER="${OPENGAUSS_USER:-gaussdb}"
DB_PASSWORD="${OPENGAUSS_PASSWORD:-Secretpassword@123}"
SQL_FILE="${1:-$PROJECT_DIR/opengauss_setup/sql/init.sql}"
INTEGRITY_SQL_FILE="$PROJECT_DIR/opengauss_setup/sql/migrate_triggers_constraints_20260608.sql"
GAUSS_ENV='export GAUSSHOME=/usr/local/opengauss; export PATH="$GAUSSHOME/bin:$PATH"; export LD_LIBRARY_PATH="$GAUSSHOME/lib:${LD_LIBRARY_PATH:-}";'

if [[ ! "$DB_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "Invalid database name: $DB_NAME" >&2
  exit 1
fi

if [[ ! "$DB_USER" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "Invalid database user: $DB_USER" >&2
  exit 1
fi

if [[ ! -f "$SQL_FILE" ]]; then
  echo "SQL file not found: $SQL_FILE" >&2
  exit 1
fi

echo "Waiting for openGauss container: $CONTAINER_NAME"
for _ in $(seq 1 120); do
  if docker exec "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -U '$DB_USER' --password '$DB_PASSWORD' -d postgres -p 5432 -c 'SELECT 1;'" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -U '$DB_USER' --password '$DB_PASSWORD' -d postgres -p 5432 -c 'SELECT 1;'" >/dev/null

echo "Recreating database: $DB_NAME"
docker exec "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -U '$DB_USER' --password '$DB_PASSWORD' -d postgres -p 5432 -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';\""
docker exec "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -U '$DB_USER' --password '$DB_PASSWORD' -d postgres -p 5432 -c 'DROP DATABASE IF EXISTS $DB_NAME;'"
docker exec "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -U '$DB_USER' --password '$DB_PASSWORD' -d postgres -p 5432 -c \"CREATE DATABASE $DB_NAME WITH ENCODING 'UTF8';\""

echo "Importing schema and seed data from: $SQL_FILE"
docker exec -i "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -v ON_ERROR_STOP=1 -U '$DB_USER' --password '$DB_PASSWORD' -d '$DB_NAME' -p 5432" < "$SQL_FILE"

if [[ -f "$INTEGRITY_SQL_FILE" ]]; then
  echo "Applying integrity triggers and views from: $INTEGRITY_SQL_FILE"
  docker exec -i "$CONTAINER_NAME" bash -lc "$GAUSS_ENV gsql -v ON_ERROR_STOP=1 -U '$DB_USER' --password '$DB_PASSWORD' -d '$DB_NAME' -p 5432" < "$INTEGRITY_SQL_FILE"
fi

echo "openGauss database is ready."
