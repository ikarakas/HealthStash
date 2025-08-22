#!/bin/bash
# Create a proper backup of the database and files

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Dump PostgreSQL database
PGPASSWORD=${POSTGRES_PASSWORD:-changeme-strong-password} pg_dump \
    -h postgres \
    -U ${POSTGRES_USER:-healthstash} \
    -d ${POSTGRES_DB:-healthstash} \
    > ${BACKUP_DIR}/${BACKUP_NAME}.sql

# Create tar.gz archive with database dump
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}.sql

# Remove the uncompressed SQL file
rm ${BACKUP_NAME}.sql

echo "Backup created: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"