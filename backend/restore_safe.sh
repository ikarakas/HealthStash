#!/bin/bash

# Safe restore script that properly handles database restoration
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: No backup file specified"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Database connection details
DB_HOST="postgres"
DB_NAME="healthstash"
DB_USER="healthstash"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme-strong-password}"

export PGPASSWORD="$DB_PASSWORD"

echo "Starting safe restore from: $BACKUP_FILE"

# First, create a temporary database name
TEMP_DB="${DB_NAME}_restore_$(date +%s)"

echo "Creating temporary database: $TEMP_DB"
psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "CREATE DATABASE $TEMP_DB;"

# Restore to temporary database
echo "Restoring to temporary database..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -U "$DB_USER" -d "$TEMP_DB" 2>/dev/null
else
    psql -h "$DB_HOST" -U "$DB_USER" -d "$TEMP_DB" -f "$BACKUP_FILE" 2>/dev/null
fi

if [ $? -eq 0 ]; then
    echo "Restore to temporary database successful"
    
    # Disconnect all users from the current database
    echo "Disconnecting users from current database..."
    psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" > /dev/null 2>&1
    
    # Drop the old database and rename the new one
    echo "Swapping databases..."
    psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME}_old;" > /dev/null 2>&1
    psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_old;" > /dev/null 2>&1
    psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "ALTER DATABASE $TEMP_DB RENAME TO $DB_NAME;"
    
    if [ $? -eq 0 ]; then
        echo "Database restored successfully!"
        # Clean up old database
        psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME}_old;" > /dev/null 2>&1
        exit 0
    else
        echo "Error swapping databases, rolling back..."
        psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEMP_DB;" > /dev/null 2>&1
        psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "ALTER DATABASE ${DB_NAME}_old RENAME TO $DB_NAME;" > /dev/null 2>&1
        exit 1
    fi
else
    echo "Restore failed, cleaning up temporary database..."
    psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $TEMP_DB;" > /dev/null 2>&1
    exit 1
fi