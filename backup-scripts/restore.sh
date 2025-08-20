#!/bin/bash

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file_path>"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/tmp/restore_$$"

echo "Starting restore from ${BACKUP_FILE}"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Create temporary restore directory
mkdir -p ${RESTORE_DIR}

# Decrypt if encrypted
if [[ "${BACKUP_FILE}" == *.enc ]]; then
    echo "Decrypting backup..."
    if [ -z "${BACKUP_ENCRYPTION_KEY}" ]; then
        echo "BACKUP_ENCRYPTION_KEY not set for encrypted backup"
        exit 1
    fi
    openssl enc -aes-256-cbc -d -in ${BACKUP_FILE} -out ${RESTORE_DIR}/backup.tar.gz -k ${BACKUP_ENCRYPTION_KEY}
    BACKUP_FILE="${RESTORE_DIR}/backup.tar.gz"
fi

# Extract backup
echo "Extracting backup..."
tar -xzf ${BACKUP_FILE} -C ${RESTORE_DIR}

# Find extracted directory
BACKUP_DIR=$(find ${RESTORE_DIR} -maxdepth 1 -type d -name "healthstash_backup_*" | head -1)

if [ -z "${BACKUP_DIR}" ]; then
    echo "Failed to find backup directory in archive"
    exit 1
fi

# Verify checksums
echo "Verifying checksums..."
cd ${BACKUP_DIR}
sha256sum -c checksums.txt || {
    echo "Checksum verification failed!"
    exit 1
}

# Restore PostgreSQL database
echo "Restoring PostgreSQL database..."
PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d postgres \
    -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d postgres \
    -c "CREATE DATABASE ${POSTGRES_DB};"

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    < ${BACKUP_DIR}/postgres_backup.sql

# Restore TimescaleDB
echo "Restoring TimescaleDB..."
PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${POSTGRES_USER} \
    -d postgres \
    -c "DROP DATABASE IF EXISTS ${TIMESCALE_DB};"

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${POSTGRES_USER} \
    -d postgres \
    -c "CREATE DATABASE ${TIMESCALE_DB};"

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${POSTGRES_USER} \
    -d ${TIMESCALE_DB} \
    < ${BACKUP_DIR}/timescale_backup.sql

# Configure MinIO client
mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

# Clear existing MinIO data
echo "Clearing existing MinIO data..."
mc rm -r --force minio/healthstash-files/ || true

# Restore MinIO files
echo "Restoring MinIO files..."
mc mirror ${BACKUP_DIR}/minio_files/ minio/healthstash-files/

# Cleanup
echo "Cleaning up temporary files..."
rm -rf ${RESTORE_DIR}

echo "Restore completed successfully!"
echo "Please restart the application for changes to take effect."