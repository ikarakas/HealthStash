#!/bin/bash

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="healthstash_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting backup at $(date)"

# Create backup directory
mkdir -p ${BACKUP_PATH}

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    --no-owner \
    --no-acl \
    -f ${BACKUP_PATH}/postgres_backup.sql

# Backup TimescaleDB
echo "Backing up TimescaleDB..."
PGPASSWORD=${POSTGRES_PASSWORD} pg_dump \
    -h ${TIMESCALE_HOST} \
    -U ${POSTGRES_USER} \
    -d ${TIMESCALE_DB} \
    --no-owner \
    --no-acl \
    -f ${BACKUP_PATH}/timescale_backup.sql

# Configure MinIO client
mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

# Backup MinIO data
echo "Backing up MinIO files..."
mc mirror minio/healthstash-files ${BACKUP_PATH}/minio_files/

# Create checksum
echo "Creating checksum..."
find ${BACKUP_PATH} -type f -exec sha256sum {} \; > ${BACKUP_PATH}/checksums.txt

# Create compressed archive
echo "Creating compressed archive..."
tar -czf ${BACKUP_PATH}.tar.gz -C ${BACKUP_DIR} ${BACKUP_NAME}

# Encrypt backup with OpenSSL
if [ ! -z "${BACKUP_ENCRYPTION_KEY}" ]; then
    echo "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -in ${BACKUP_PATH}.tar.gz -out ${BACKUP_PATH}.tar.gz.enc -k ${BACKUP_ENCRYPTION_KEY}
    rm ${BACKUP_PATH}.tar.gz
    FINAL_BACKUP="${BACKUP_PATH}.tar.gz.enc"
else
    FINAL_BACKUP="${BACKUP_PATH}.tar.gz"
fi

# Clean up uncompressed files
rm -rf ${BACKUP_PATH}

# Remove old backups based on retention policy
if [ ! -z "${BACKUP_RETENTION_DAYS}" ]; then
    echo "Removing backups older than ${BACKUP_RETENTION_DAYS} days..."
    find ${BACKUP_DIR} -name "healthstash_backup_*.tar.gz*" -mtime +${BACKUP_RETENTION_DAYS} -delete
fi

echo "Backup completed successfully: ${FINAL_BACKUP}"
echo "Backup size: $(du -h ${FINAL_BACKUP} | cut -f1)"

# Update backup status in database
PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    -c "INSERT INTO backup_history (id, backup_type, status, file_path, file_size, completed_at) 
        VALUES (gen_random_uuid(), 'full', 'completed', '${FINAL_BACKUP}', 
        (SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'))::text), NOW());"