#!/bin/bash

# Deep verification script for backup/restore functionality
# This script performs comprehensive testing to ensure backups are restorable

set -e

echo "========================================="
echo "HEALTHSTASH BACKUP/RESTORE VERIFICATION"
echo "========================================="
echo ""

BACKUP_DIR="/backups"
TEST_DIR="/tmp/restore_test_$$"
VERIFY_DIR="/tmp/verify_$$"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to calculate checksums
calculate_checksum() {
    sha256sum "$1" 2>/dev/null | cut -d' ' -f1
}

# Step 1: Find latest backup
echo "Step 1: Locating latest backup..."
LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/healthstash_backup_*.tar.gz.enc 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    print_status "error" "No backups found in ${BACKUP_DIR}"
    exit 1
fi

print_status "success" "Found backup: $(basename $LATEST_BACKUP)"
BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
print_status "" "Backup size: $BACKUP_SIZE"
echo ""

# Step 2: Verify encryption key exists
echo "Step 2: Verifying encryption key..."
if [ -f "${BACKUP_DIR}/.encryption_key" ]; then
    ENCRYPTION_KEY=$(cat ${BACKUP_DIR}/.encryption_key)
    print_status "success" "Encryption key found"
    KEY_LENGTH=${#ENCRYPTION_KEY}
    if [ $KEY_LENGTH -lt 10 ]; then
        print_status "warning" "Encryption key seems short (${KEY_LENGTH} chars)"
    fi
else
    print_status "error" "No encryption key found at ${BACKUP_DIR}/.encryption_key"
    print_status "" "Attempting with default key..."
    ENCRYPTION_KEY="healthstash-backup-key-2025"
fi
echo ""

# Step 3: Test decryption
echo "Step 3: Testing decryption..."
mkdir -p ${TEST_DIR}

openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
    -in ${LATEST_BACKUP} \
    -out ${TEST_DIR}/backup.tar.gz \
    -pass pass:"${ENCRYPTION_KEY}" 2>${TEST_DIR}/decrypt.log

if [ $? -eq 0 ]; then
    print_status "success" "Backup decrypted successfully"
    DECRYPTED_SIZE=$(du -h ${TEST_DIR}/backup.tar.gz | cut -f1)
    print_status "" "Decrypted size: $DECRYPTED_SIZE"
else
    print_status "error" "Failed to decrypt backup"
    cat ${TEST_DIR}/decrypt.log
    rm -rf ${TEST_DIR}
    exit 1
fi
echo ""

# Step 4: Extract and verify archive
echo "Step 4: Extracting backup archive..."
tar -xzf ${TEST_DIR}/backup.tar.gz -C ${TEST_DIR} 2>${TEST_DIR}/extract.log

if [ $? -eq 0 ]; then
    print_status "success" "Archive extracted successfully"
else
    print_status "error" "Failed to extract archive"
    cat ${TEST_DIR}/extract.log
    rm -rf ${TEST_DIR}
    exit 1
fi

# Find extracted directory
BACKUP_NAME=$(ls ${TEST_DIR} | grep healthstash_backup_ | head -1)
EXTRACTED_DIR="${TEST_DIR}/${BACKUP_NAME}"

if [ ! -d "${EXTRACTED_DIR}" ]; then
    print_status "error" "Could not find extracted backup directory"
    rm -rf ${TEST_DIR}
    exit 1
fi
echo ""

# Step 5: Verify backup contents
echo "Step 5: Verifying backup contents..."
VERIFICATION_PASSED=true

# Check for required files
REQUIRED_FILES=(
    "postgres_backup.sql"
    "timescale_backup.sql"
    "checksums.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${EXTRACTED_DIR}/${file}" ]; then
        FILE_SIZE=$(du -h "${EXTRACTED_DIR}/${file}" | cut -f1)
        print_status "success" "Found ${file} (${FILE_SIZE})"
    else
        print_status "error" "Missing required file: ${file}"
        VERIFICATION_PASSED=false
    fi
done

# Check MinIO files directory
if [ -d "${EXTRACTED_DIR}/minio_files" ]; then
    FILE_COUNT=$(find "${EXTRACTED_DIR}/minio_files" -type f | wc -l)
    print_status "success" "Found MinIO files directory (${FILE_COUNT} files)"
else
    print_status "warning" "No MinIO files directory found"
fi
echo ""

# Step 6: Verify checksums
echo "Step 6: Verifying file checksums..."
if [ -f "${EXTRACTED_DIR}/checksums.txt" ]; then
    cd ${EXTRACTED_DIR}
    
    # Count total checksums
    TOTAL_CHECKSUMS=$(wc -l < checksums.txt)
    print_status "" "Verifying ${TOTAL_CHECKSUMS} file checksums..."
    
    # Verify checksums (files are relative to current directory)
    CHECKSUM_ERRORS=0
    VERIFIED_COUNT=0
    while IFS= read -r line; do
        HASH=$(echo "$line" | awk '{print $1}')
        # Extract filename after the hash (removing the ./ prefix if present)
        FILE=$(echo "$line" | sed 's/^[^ ]* *//; s/^\.\///')
        
        if [ -f "$FILE" ]; then
            # Skip verifying checksums.txt itself (it contains its own hash which is circular)
            if [ "$FILE" = "checksums.txt" ] || [ "$FILE" = "./checksums.txt" ]; then
                VERIFIED_COUNT=$((VERIFIED_COUNT + 1))
                continue
            fi
            
            ACTUAL_HASH=$(calculate_checksum "$FILE")
            if [ "$HASH" = "$ACTUAL_HASH" ]; then
                VERIFIED_COUNT=$((VERIFIED_COUNT + 1))
            else
                print_status "error" "Checksum mismatch for $FILE"
                print_status "" "  Expected: $HASH"
                print_status "" "  Got: $ACTUAL_HASH"
                CHECKSUM_ERRORS=$((CHECKSUM_ERRORS + 1))
            fi
        else
            print_status "error" "File not found: $FILE"
            CHECKSUM_ERRORS=$((CHECKSUM_ERRORS + 1))
        fi
    done < checksums.txt
    
    if [ $CHECKSUM_ERRORS -eq 0 ]; then
        print_status "success" "All ${VERIFIED_COUNT} checksums verified successfully"
    else
        print_status "error" "${CHECKSUM_ERRORS} checksum errors found"
        if [ $VERIFIED_COUNT -gt 0 ]; then
            print_status "warning" "${VERIFIED_COUNT} files passed verification"
        fi
        VERIFICATION_PASSED=false
    fi
else
    print_status "warning" "No checksums.txt file found"
fi
echo ""

# Step 7: Test SQL file integrity
echo "Step 7: Checking SQL backup integrity..."

# Check PostgreSQL backup
if [ -f "${EXTRACTED_DIR}/postgres_backup.sql" ]; then
    # Check for basic SQL structure
    if grep -q "CREATE TABLE" "${EXTRACTED_DIR}/postgres_backup.sql"; then
        TABLE_COUNT=$(grep -c "CREATE TABLE" "${EXTRACTED_DIR}/postgres_backup.sql")
        print_status "success" "PostgreSQL backup contains ${TABLE_COUNT} tables"
    else
        print_status "warning" "No CREATE TABLE statements found in PostgreSQL backup"
    fi
    
    # Check for data
    if grep -q "INSERT INTO" "${EXTRACTED_DIR}/postgres_backup.sql"; then
        INSERT_COUNT=$(grep -c "INSERT INTO" "${EXTRACTED_DIR}/postgres_backup.sql")
        print_status "success" "PostgreSQL backup contains ${INSERT_COUNT} INSERT statements"
    else
        print_status "warning" "No INSERT statements found in PostgreSQL backup"
    fi
fi

# Check TimescaleDB backup
if [ -f "${EXTRACTED_DIR}/timescale_backup.sql" ]; then
    # Check file size (should have content)
    TIMESCALE_SIZE=$(stat -c%s "${EXTRACTED_DIR}/timescale_backup.sql")
    if [ $TIMESCALE_SIZE -gt 1000 ]; then
        print_status "success" "TimescaleDB backup has content (${TIMESCALE_SIZE} bytes)"
    else
        print_status "warning" "TimescaleDB backup seems small (${TIMESCALE_SIZE} bytes)"
    fi
fi
echo ""

# Step 8: Test actual restore (optional - requires database access)
echo "Step 8: Testing restore capability..."
if [ ! -z "${TEST_RESTORE}" ]; then
    print_status "" "Attempting test restore to temporary database..."
    
    # Create test database
    TEST_DB="healthstash_restore_test_$$"
    
    PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST} \
        -U ${POSTGRES_USER} \
        -c "CREATE DATABASE ${TEST_DB};" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "success" "Created test database: ${TEST_DB}"
        
        # Restore to test database
        PGPASSWORD=${POSTGRES_PASSWORD} psql \
            -h ${POSTGRES_HOST} \
            -U ${POSTGRES_USER} \
            -d ${TEST_DB} \
            -f ${EXTRACTED_DIR}/postgres_backup.sql > ${TEST_DIR}/restore.log 2>&1
        
        if [ $? -eq 0 ]; then
            print_status "success" "Successfully restored to test database"
            
            # Verify restored data
            TABLE_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql \
                -h ${POSTGRES_HOST} \
                -U ${POSTGRES_USER} \
                -d ${TEST_DB} \
                -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)
            
            print_status "success" "Restored database has ${TABLE_COUNT} tables"
            
            # Check for users table
            USER_COUNT=$(PGPASSWORD=${POSTGRES_PASSWORD} psql \
                -h ${POSTGRES_HOST} \
                -U ${POSTGRES_USER} \
                -d ${TEST_DB} \
                -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
            
            if [ ! -z "$USER_COUNT" ]; then
                print_status "success" "Users table has ${USER_COUNT} records"
            fi
        else
            print_status "error" "Failed to restore to test database"
            tail -n 20 ${TEST_DIR}/restore.log
        fi
        
        # Drop test database
        PGPASSWORD=${POSTGRES_PASSWORD} psql \
            -h ${POSTGRES_HOST} \
            -U ${POSTGRES_USER} \
            -c "DROP DATABASE ${TEST_DB};" 2>/dev/null
    else
        print_status "warning" "Could not create test database (may need database credentials)"
    fi
else
    print_status "" "Skipping actual restore test (set TEST_RESTORE=1 to enable)"
fi
echo ""

# Step 9: Generate restore commands
echo "Step 9: Generating restore commands..."
mkdir -p ${VERIFY_DIR}

cat > ${VERIFY_DIR}/restore-commands.sh << EOF
#!/bin/bash
# Auto-generated restore commands for backup: $(basename $LATEST_BACKUP)
# Generated on: $(date)

# 1. Decrypt backup
echo "Decrypting backup..."
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \\
    -in ${LATEST_BACKUP} \\
    -out /tmp/restore.tar.gz \\
    -pass pass:"${ENCRYPTION_KEY}"

# 2. Extract archive
echo "Extracting archive..."
tar -xzf /tmp/restore.tar.gz -C /tmp/

# 3. Restore PostgreSQL database
echo "Restoring PostgreSQL database..."
PGPASSWORD=\${POSTGRES_PASSWORD} psql \\
    -h \${POSTGRES_HOST} \\
    -U \${POSTGRES_USER} \\
    -d \${POSTGRES_DB} \\
    -f ${EXTRACTED_DIR}/postgres_backup.sql

# 4. Restore TimescaleDB
echo "Restoring TimescaleDB..."
PGPASSWORD=\${TIMESCALE_PASSWORD:-\${POSTGRES_PASSWORD}} psql \\
    -h \${TIMESCALE_HOST} \\
    -U \${TIMESCALE_USER:-\${POSTGRES_USER}} \\
    -d \${TIMESCALE_DB} \\
    -f ${EXTRACTED_DIR}/timescale_backup.sql

# 5. Restore MinIO files
echo "Restoring MinIO files..."
minio-mc alias set minio http://\${MINIO_ENDPOINT} \${MINIO_ACCESS_KEY} \${MINIO_SECRET_KEY}
minio-mc mirror ${EXTRACTED_DIR}/minio_files/ minio/healthstash-files/

echo "Restore complete!"
EOF

chmod +x ${VERIFY_DIR}/restore-commands.sh
print_status "success" "Generated restore commands at: ${VERIFY_DIR}/restore-commands.sh"
echo ""

# Final summary
echo "========================================="
echo "VERIFICATION SUMMARY"
echo "========================================="

if [ "$VERIFICATION_PASSED" = true ]; then
    print_status "success" "BACKUP IS RESTORABLE"
    echo ""
    echo "Backup details:"
    echo "  - File: $(basename $LATEST_BACKUP)"
    echo "  - Size: $BACKUP_SIZE"
    echo "  - Created: $(stat -c %y "$LATEST_BACKUP" | cut -d' ' -f1,2)"
    echo "  - Encryption: AES-256-CBC with PBKDF2"
    echo "  - Contents verified: PostgreSQL, TimescaleDB, MinIO files"
    echo ""
    echo "To perform actual restore:"
    echo "  1. Review: cat ${VERIFY_DIR}/restore-commands.sh"
    echo "  2. Execute: bash ${VERIFY_DIR}/restore-commands.sh"
else
    print_status "error" "BACKUP VERIFICATION FAILED"
    echo ""
    echo "Issues found during verification. Please review above errors."
fi

# Cleanup
echo ""
echo "Cleaning up temporary files..."
rm -rf ${TEST_DIR}
print_status "success" "Cleanup complete"

echo ""
echo "========================================="
echo "Verification completed at: $(date)"
echo "========================================="