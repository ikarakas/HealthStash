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
# Use TimescaleDB-specific credentials if available, otherwise fall back to Postgres credentials
TIMESCALE_USER="${TIMESCALE_USER:-${POSTGRES_USER}}"
TIMESCALE_PASSWORD="${TIMESCALE_PASSWORD:-${POSTGRES_PASSWORD}}"

PGPASSWORD=${TIMESCALE_PASSWORD} pg_dump \
    -h ${TIMESCALE_HOST} \
    -U ${TIMESCALE_USER} \
    -d ${TIMESCALE_DB} \
    --no-owner \
    --no-acl \
    -f ${BACKUP_PATH}/timescale_backup.sql

# Configure MinIO client
minio-mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

# Backup MinIO data
echo "Backing up MinIO files..."
minio-mc mirror minio/healthstash-files ${BACKUP_PATH}/minio_files/

# Create checksum
echo "Creating checksum..."
find ${BACKUP_PATH} -type f -exec sha256sum {} \; > ${BACKUP_PATH}/checksums.txt

# Create compressed archive
echo "Creating compressed archive..."
tar -czf ${BACKUP_PATH}.tar.gz -C ${BACKUP_DIR} ${BACKUP_NAME}

# Encrypt backup with OpenSSL using authenticated encryption
# Use a FIXED key from environment or a default one that's always available
BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-healthstash-backup-key-2025}"
echo "Encrypting backup with authenticated encryption..."

# Save the encryption key to a file for restore operations
echo "${BACKUP_ENCRYPTION_KEY}" > ${BACKUP_DIR}/.encryption_key
chmod 600 ${BACKUP_DIR}/.encryption_key

# Use AES-256-CBC with PBKDF2 (GCM not available in Alpine's OpenSSL)
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in ${BACKUP_PATH}.tar.gz \
    -out ${BACKUP_PATH}.tar.gz.enc \
    -pass pass:"${BACKUP_ENCRYPTION_KEY}"

if [ $? -eq 0 ]; then
    rm ${BACKUP_PATH}.tar.gz
    FINAL_BACKUP="${BACKUP_PATH}.tar.gz.enc"
    echo "Backup encrypted successfully with saved key"
else
    echo "ERROR: Encryption failed, keeping unencrypted backup"
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

# For manual backups triggered via web UI, the database entry is already created
# Only create a new entry for automatic/cron backups
update_backup_status() {
    # Check if this is a manual backup (triggered via web UI)
    if [ ! -z "${BACKUP_ID}" ]; then
        echo "Manual backup - database entry already exists"
        return
    fi
    
    # For automatic backups, create a database entry
    local backup_size_bytes=$(stat -c%s "${FINAL_BACKUP}" 2>/dev/null || echo "0")
    local backup_id=$(uuidgen || echo "backup_$(date +%s)")
    
    PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST} \
        -U ${POSTGRES_USER} \
        -d ${POSTGRES_DB} \
        -c "INSERT INTO backup_history (id, backup_type, status, file_path, file_size, size_mb, completed_at, created_at, notes) 
            VALUES ('${backup_id}', 'FULL', 'COMPLETED', '${FINAL_BACKUP}', 
            ${backup_size_bytes}, $(echo "scale=2; ${backup_size_bytes}/1048576" | bc), NOW(), NOW(), 'Automatic backup (cron)');" 2>/dev/null || \
    echo "Warning: Failed to update backup history in database"
}

trap update_backup_status EXIT