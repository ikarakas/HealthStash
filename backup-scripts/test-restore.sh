#!/bin/bash

# Test restore script - restore to a staging environment for validation

set -e

BACKUP_FILE="${1}"
STAGING_PREFIX="${2:-staging}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file> [staging_prefix]"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "Starting test restore of ${BACKUP_FILE} to ${STAGING_PREFIX} environment..."

# Create temporary directory for extraction
TEMP_DIR="/tmp/restore_test_${STAGING_PREFIX}_$(date +%s)"
mkdir -p ${TEMP_DIR}

# Decrypt backup
if [[ "${BACKUP_FILE}" == *.enc ]]; then
    echo "Decrypting backup..."
    if [ -z "${BACKUP_ENCRYPTION_KEY}" ]; then
        echo "Error: BACKUP_ENCRYPTION_KEY not set for encrypted backup"
        exit 1
    fi
    
    openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -d \
        -in ${BACKUP_FILE} \
        -out ${TEMP_DIR}/backup.tar.gz \
        -pass pass:"${BACKUP_ENCRYPTION_KEY}"
    
    DECRYPTED_FILE="${TEMP_DIR}/backup.tar.gz"
elif [[ "${BACKUP_FILE}" == *.age ]]; then
    echo "Decrypting age-encrypted backup..."
    echo "${BACKUP_ENCRYPTION_KEY}" | age -d -o ${TEMP_DIR}/backup.tar.gz ${BACKUP_FILE}
    DECRYPTED_FILE="${TEMP_DIR}/backup.tar.gz"
else
    DECRYPTED_FILE="${BACKUP_FILE}"
fi

# Extract backup
echo "Extracting backup..."
tar -xzf ${DECRYPTED_FILE} -C ${TEMP_DIR}

# Find the backup directory
BACKUP_DIR=$(find ${TEMP_DIR} -maxdepth 1 -type d -name "healthstash_backup_*" | head -1)

if [ -z "${BACKUP_DIR}" ]; then
    echo "Error: Could not find backup directory in archive"
    exit 1
fi

# Verify checksums
echo "Verifying checksums..."
cd ${BACKUP_DIR}
sha256sum -c checksums.txt || {
    echo "Error: Checksum verification failed!"
    exit 1
}

# Test PostgreSQL restore
echo "Testing PostgreSQL restore to ${STAGING_PREFIX}_healthstash database..."
PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -c "CREATE DATABASE ${STAGING_PREFIX}_healthstash;" 2>/dev/null || true

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${STAGING_PREFIX}_healthstash \
    -f ${BACKUP_DIR}/postgres_backup.sql

# Test TimescaleDB restore
echo "Testing TimescaleDB restore to ${STAGING_PREFIX}_vitals database..."
PGPASSWORD=${TIMESCALE_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${TIMESCALE_USER} \
    -c "CREATE DATABASE ${STAGING_PREFIX}_vitals;" 2>/dev/null || true

PGPASSWORD=${TIMESCALE_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${TIMESCALE_USER} \
    -d ${STAGING_PREFIX}_vitals \
    -f ${BACKUP_DIR}/timescale_backup.sql

# Test MinIO restore
echo "Testing MinIO file restore to ${STAGING_PREFIX}-files bucket..."
minio-mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
minio-mc mb minio/${STAGING_PREFIX}-files 2>/dev/null || true
minio-mc mirror ${BACKUP_DIR}/minio_files/ minio/${STAGING_PREFIX}-files/

# Validate restored data
echo "Validating restored data..."

# Check PostgreSQL tables
PG_TABLES=$(PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${STAGING_PREFIX}_healthstash \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

echo "PostgreSQL tables restored: ${PG_TABLES}"

# Check TimescaleDB hypertables
TS_TABLES=$(PGPASSWORD=${TIMESCALE_PASSWORD} psql \
    -h ${TIMESCALE_HOST} \
    -U ${TIMESCALE_USER} \
    -d ${STAGING_PREFIX}_vitals \
    -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables;" 2>/dev/null || echo "0")

echo "TimescaleDB hypertables restored: ${TS_TABLES}"

# Check MinIO files
FILE_COUNT=$(minio-mc ls minio/${STAGING_PREFIX}-files/ --recursive | wc -l)
echo "MinIO files restored: ${FILE_COUNT}"

# Cleanup
echo "Cleaning up test restore..."
rm -rf ${TEMP_DIR}

# Optional: Drop staging databases (comment out to keep for inspection)
# PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -c "DROP DATABASE ${STAGING_PREFIX}_healthstash;"
# PGPASSWORD=${TIMESCALE_PASSWORD} psql -h ${TIMESCALE_HOST} -U ${TIMESCALE_USER} -c "DROP DATABASE ${STAGING_PREFIX}_vitals;"
# minio-mc rm -r --force minio/${STAGING_PREFIX}-files/

echo "Test restore completed successfully!"
echo "Staging databases created:"
echo "  - PostgreSQL: ${STAGING_PREFIX}_healthstash"
echo "  - TimescaleDB: ${STAGING_PREFIX}_vitals"
echo "  - MinIO bucket: ${STAGING_PREFIX}-files"