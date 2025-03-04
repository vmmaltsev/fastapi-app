#!/bin/bash
set -e

# Проверяем, существует ли уже база данных
DB_NAME=${DB_NAME:-fastapi_app}
DB_EXISTS=$(psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

# Создаем базу данных, если она не существует
if [ -z "$DB_EXISTS" ]; then
    echo "Creating database $DB_NAME..."
    psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
fi

# Предоставляем привилегии пользователю
psql -U "$POSTGRES_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $POSTGRES_USER;"

echo "Database $DB_NAME initialized" 