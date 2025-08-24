#!/bin/bash

# Full restore test script
# This script simulates a disaster recovery scenario

set -e

echo "========================================"
echo "FULL SYSTEM RESTORE TEST"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    if [ "$1" = "success" ]; then
        echo -e "${GREEN}✓${NC} $2"
    elif [ "$1" = "error" ]; then
        echo -e "${RED}✗${NC} $2"
    elif [ "$1" = "warning" ]; then
        echo -e "${YELLOW}⚠${NC} $2"
    else
        echo "$2"
    fi
}

BACKUP_DIR="/backups"
RESTORE_DIR="/tmp/full_restore_$$"

# Find latest backup
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/healthstash_backup_*.tar.gz.enc 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    print_status "error" "No backups found"
    exit 1
fi

print_status "success" "Found backup: $(basename $LATEST_BACKUP)"
echo ""

# Step 1: Record current state
echo "Step 1: Recording current system state..."
echo "----------------------------------------"

# Count current records
CURRENT_USER_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
CURRENT_RECORD_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM health_records;" 2>/dev/null | xargs)
CURRENT_FILE_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM file_metadata;" 2>/dev/null | xargs)

print_status "" "Current database state:"
print_status "" "  - Users: ${CURRENT_USER_COUNT}"
print_status "" "  - Health Records: ${CURRENT_RECORD_COUNT}"
print_status "" "  - File Metadata: ${CURRENT_FILE_COUNT}"

# Count MinIO files
MINIO_FILE_COUNT=$(minio-mc ls minio/healthstash-files --recursive 2>/dev/null | wc -l || echo "0")
print_status "" "  - MinIO Files: ${MINIO_FILE_COUNT}"
echo ""

# Step 2: Decrypt and extract backup
echo "Step 2: Extracting backup..."
echo "-----------------------------"

mkdir -p ${RESTORE_DIR}

# Read encryption key
ENCRYPTION_KEY=$(cat ${BACKUP_DIR}/.encryption_key 2>/dev/null || echo "healthstash-backup-key-2025")

# Decrypt
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
    -in ${LATEST_BACKUP} \
    -out ${RESTORE_DIR}/backup.tar.gz \
    -pass pass:"${ENCRYPTION_KEY}"

if [ $? -eq 0 ]; then
    print_status "success" "Backup decrypted"
else
    print_status "error" "Failed to decrypt backup"
    exit 1
fi

# Extract
tar -xzf ${RESTORE_DIR}/backup.tar.gz -C ${RESTORE_DIR}
BACKUP_NAME=$(ls ${RESTORE_DIR} | grep healthstash_backup_ | head -1)
EXTRACTED_DIR="${RESTORE_DIR}/${BACKUP_NAME}"

print_status "success" "Backup extracted to ${EXTRACTED_DIR}"
echo ""

# Step 3: Simulate disaster - Clear test data
echo "Step 3: Simulating disaster (clearing test data)..."
echo "---------------------------------------------------"

# Create test database for restore
TEST_DB="healthstash_restore_test"
print_status "warning" "Creating test database: ${TEST_DB}"

PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -c "DROP DATABASE IF EXISTS ${TEST_DB};" 2>/dev/null
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -c "CREATE DATABASE ${TEST_DB};" 2>/dev/null

# Clear test MinIO bucket
print_status "warning" "Creating test MinIO bucket: healthstash-test"
minio-mc mb minio/healthstash-test --ignore-existing 2>/dev/null || true
minio-mc rm minio/healthstash-test --recursive --force 2>/dev/null || true

print_status "success" "Test environment prepared"
echo ""

# Step 4: Restore database
echo "Step 4: Restoring database..."
echo "-----------------------------"

PGPASSWORD=${POSTGRES_PASSWORD} psql \
    -h ${POSTGRES_HOST} \
    -U ${POSTGRES_USER} \
    -d ${TEST_DB} \
    -f ${EXTRACTED_DIR}/postgres_backup.sql > ${RESTORE_DIR}/restore.log 2>&1

if [ $? -eq 0 ]; then
    print_status "success" "PostgreSQL database restored"
else
    print_status "error" "Database restore failed"
    tail -10 ${RESTORE_DIR}/restore.log
    exit 1
fi

# Verify restored data
RESTORED_USER_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${TEST_DB} -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
RESTORED_RECORD_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${TEST_DB} -t -c "SELECT COUNT(*) FROM health_records;" 2>/dev/null | xargs)
RESTORED_FILE_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${TEST_DB} -t -c "SELECT COUNT(*) FROM file_metadata;" 2>/dev/null | xargs)

print_status "" "Restored database state:"
print_status "" "  - Users: ${RESTORED_USER_COUNT}"
print_status "" "  - Health Records: ${RESTORED_RECORD_COUNT}"
print_status "" "  - File Metadata: ${RESTORED_FILE_COUNT}"
echo ""

# Step 5: Restore MinIO files
echo "Step 5: Restoring MinIO files..."
echo "--------------------------------"

if [ -d "${EXTRACTED_DIR}/minio_files" ]; then
    FILE_COUNT=$(ls -la ${EXTRACTED_DIR}/minio_files/*/ 2>/dev/null | wc -l)
    print_status "" "Found ${FILE_COUNT} files to restore"
    
    # Mirror files to test bucket
    minio-mc mirror ${EXTRACTED_DIR}/minio_files/ minio/healthstash-test/
    
    if [ $? -eq 0 ]; then
        print_status "success" "MinIO files restored"
        
        # Count restored files
        RESTORED_MINIO_COUNT=$(minio-mc ls minio/healthstash-test --recursive 2>/dev/null | wc -l)
        print_status "" "Restored ${RESTORED_MINIO_COUNT} files to MinIO"
    else
        print_status "error" "Failed to restore MinIO files"
    fi
else
    print_status "warning" "No MinIO files found in backup"
fi
echo ""

# Step 6: Verify file integrity
echo "Step 6: Verifying file integrity..."
echo "-----------------------------------"

# Sample verification - check a few files exist and match checksums
cd ${EXTRACTED_DIR}
SAMPLE_FILES=$(grep "minio_files" checksums.txt | head -5)
VERIFY_COUNT=0
VERIFY_SUCCESS=0

while IFS= read -r line; do
    if [ -z "$line" ]; then continue; fi
    
    HASH=$(echo "$line" | awk '{print $1}')
    FILE=$(echo "$line" | sed 's/^[^ ]* *//' | sed 's/^\.\///')
    
    if [ -f "$FILE" ]; then
        ACTUAL_HASH=$(sha256sum "$FILE" 2>/dev/null | cut -d' ' -f1)
        if [ "$HASH" = "$ACTUAL_HASH" ]; then
            VERIFY_SUCCESS=$((VERIFY_SUCCESS + 1))
        fi
    fi
    VERIFY_COUNT=$((VERIFY_COUNT + 1))
done <<< "$SAMPLE_FILES"

print_status "success" "Verified ${VERIFY_SUCCESS}/${VERIFY_COUNT} sample file checksums"
echo ""

# Step 7: Verification Summary
echo "========================================"
echo "RESTORE VERIFICATION SUMMARY"
echo "========================================"
echo ""

# Compare counts
if [ "$RESTORED_USER_COUNT" = "$CURRENT_USER_COUNT" ]; then
    print_status "success" "User count matches: ${RESTORED_USER_COUNT}"
else
    print_status "warning" "User count: Original=${CURRENT_USER_COUNT}, Restored=${RESTORED_USER_COUNT}"
fi

if [ "$RESTORED_RECORD_COUNT" = "$CURRENT_RECORD_COUNT" ]; then
    print_status "success" "Health record count matches: ${RESTORED_RECORD_COUNT}"
else
    print_status "warning" "Health records: Original=${CURRENT_RECORD_COUNT}, Restored=${RESTORED_RECORD_COUNT}"
fi

if [ "$RESTORED_FILE_COUNT" = "$CURRENT_FILE_COUNT" ]; then
    print_status "success" "File metadata count matches: ${RESTORED_FILE_COUNT}"
else
    print_status "warning" "File metadata: Original=${CURRENT_FILE_COUNT}, Restored=${RESTORED_FILE_COUNT}"
fi

echo ""

# List sample restored files
echo "Sample restored files:"
echo "----------------------"
minio-mc ls minio/healthstash-test --recursive 2>/dev/null | head -10

echo ""
echo "========================================"
echo "RESTORE TEST COMPLETED"
echo "========================================"
echo ""
echo "Test database: ${TEST_DB}"
echo "Test MinIO bucket: healthstash-test"
echo ""
echo "To check restored data:"
echo "  Database: PGPASSWORD=\${POSTGRES_PASSWORD} psql -h \${POSTGRES_HOST} -U \${POSTGRES_USER} -d ${TEST_DB}"
echo "  Files: minio-mc ls minio/healthstash-test --recursive"
echo ""
echo "To clean up test data:"
echo "  PGPASSWORD=\${POSTGRES_PASSWORD} psql -h \${POSTGRES_HOST} -U \${POSTGRES_USER} -c 'DROP DATABASE ${TEST_DB};'"
echo "  minio-mc rm minio/healthstash-test --recursive --force"
echo "  rm -rf ${RESTORE_DIR}"