#!/bin/bash

set -e

BACKUP_DIR="/backups"
RESTORE_DIR="/tmp/restore_$$"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.tar.gz.enc>"
    echo ""
    echo "Available backups:"
    ls -lh ${BACKUP_DIR}/healthstash_backup_*.tar.gz.enc 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file ${BACKUP_FILE} not found"
    exit 1
fi

echo "Starting restore from ${BACKUP_FILE}"

# Read encryption key
if [ -f "${BACKUP_DIR}/.encryption_key" ]; then
    BACKUP_ENCRYPTION_KEY=$(cat ${BACKUP_DIR}/.encryption_key)
    echo "Using saved encryption key"
else
    echo "Warning: No saved encryption key found, using default"
    BACKUP_ENCRYPTION_KEY="healthstash-backup-key-2025"
fi

# Create restore directory
mkdir -p ${RESTORE_DIR}

# Decrypt backup
echo "Decrypting backup..."
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
    -in ${BACKUP_FILE} \
    -out ${RESTORE_DIR}/backup.tar.gz \
    -pass pass:"${BACKUP_ENCRYPTION_KEY}"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to decrypt backup"
    rm -rf ${RESTORE_DIR}
    exit 1
fi

# Extract backup
echo "Extracting backup..."
tar -xzf ${RESTORE_DIR}/backup.tar.gz -C ${RESTORE_DIR}

# Find the extracted backup directory
BACKUP_NAME=$(ls ${RESTORE_DIR} | grep healthstash_backup_ | head -1)
EXTRACTED_DIR="${RESTORE_DIR}/${BACKUP_NAME}"

if [ ! -d "${EXTRACTED_DIR}" ]; then
    echo "ERROR: Could not find extracted backup directory"
    rm -rf ${RESTORE_DIR}
    exit 1
fi

# Verify checksums
echo "Verifying checksums..."
cd ${EXTRACTED_DIR}
sha256sum -c checksums.txt > /dev/null 2>&1 || echo "Warning: Some checksums don't match"

echo ""
echo "Backup extracted successfully to: ${EXTRACTED_DIR}"
echo ""
echo "Contents:"
ls -la ${EXTRACTED_DIR}

echo ""
echo "To restore databases, run:"
echo "  PostgreSQL: PGPASSWORD=\${POSTGRES_PASSWORD} psql -h \${POSTGRES_HOST} -U \${POSTGRES_USER} -d \${POSTGRES_DB} < ${EXTRACTED_DIR}/postgres_backup.sql"
echo "  TimescaleDB: PGPASSWORD=\${TIMESCALE_PASSWORD} psql -h \${TIMESCALE_HOST} -U \${TIMESCALE_USER} -d \${TIMESCALE_DB} < ${EXTRACTED_DIR}/timescale_backup.sql"
echo ""
echo "To restore MinIO files:"
echo "  minio-mc alias set minio http://\${MINIO_ENDPOINT} \${MINIO_ACCESS_KEY} \${MINIO_SECRET_KEY}"
echo "  minio-mc mirror ${EXTRACTED_DIR}/minio_files/ minio/healthstash-files/"
echo ""
echo "Note: Clean up temporary files after restore: rm -rf ${RESTORE_DIR}"
