#!/bin/bash

# Simple restore script for backend container
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

echo "Starting restore from: $BACKUP_FILE"

# Check if file is gzipped
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing and restoring backup..."
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"
else
    echo "Restoring backup..."
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "Restore completed successfully"
    exit 0
else
    echo "Restore failed"
    exit 1
fi