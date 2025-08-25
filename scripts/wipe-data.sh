#!/bin/bash

# HealthStash Data Wipe Script
# This script removes all data except user accounts
# WARNING: This action is irreversible!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}=========================================${NC}"
echo -e "${RED}      HEALTHSTASH DATA WIPE UTILITY     ${NC}"
echo -e "${RED}=========================================${NC}"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will permanently delete:${NC}"
echo "  • All health records"
echo "  • All payment records"
echo "  • All uploaded files (MinIO)"
echo "  • All vital signs data"
echo "  • All audit logs"
echo "  • All backup history"
echo ""
echo -e "${GREEN}✓ Will preserve:${NC}"
echo "  • User accounts and credentials"
echo ""
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you absolutely sure? Type 'YES DELETE ALL DATA' to confirm: " confirmation

if [ "$confirmation" != "YES DELETE ALL DATA" ]; then
    echo -e "${BLUE}Operation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting data wipe...${NC}"
echo ""

# Step 1: Clear PostgreSQL tables (except users)
echo -e "${BLUE}Step 1: Clearing database tables...${NC}"

docker exec healthstash-postgres psql -U healthstash -d healthstash << 'EOF'
-- Clear all tables except users
BEGIN;

-- Clear payment records first (they reference health_records)
DELETE FROM payment_files;
DELETE FROM payment_records;

-- Now clear health records and related data
DELETE FROM record_tags;
DELETE FROM tags;
DELETE FROM health_records;

-- Clear audit logs
DELETE FROM audit_logs;

-- Clear backup history
DELETE FROM backup_history;

-- Reset any sequences if needed
-- (User IDs are preserved so we don't reset user sequence)

COMMIT;

-- Show remaining data
SELECT 'Users remaining:' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Health records:', COUNT(*) FROM health_records
UNION ALL
SELECT 'Payment records:', COUNT(*) FROM payment_records
UNION ALL
SELECT 'Audit logs:', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'Backup history:', COUNT(*) FROM backup_history;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database tables cleared${NC}"
else
    echo -e "${RED}✗ Failed to clear database tables${NC}"
    exit 1
fi

echo ""

# Step 2: Clear TimescaleDB vital signs
echo -e "${BLUE}Step 2: Clearing vital signs data...${NC}"

docker exec healthstash-timescale psql -U healthstash -d healthstash << 'EOF' 2>/dev/null
-- Clear vital signs data (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vital_signs') THEN
        TRUNCATE TABLE vital_signs;
        RAISE NOTICE 'Vital signs table cleared';
    ELSE
        RAISE NOTICE 'Vital signs table does not exist';
    END IF;
END $$;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Vital signs handled${NC}"
else
    echo -e "${YELLOW}⚠ Vital signs table may not exist${NC}"
fi

echo ""

# Step 3: Clear MinIO storage
echo -e "${BLUE}Step 3: Clearing MinIO file storage...${NC}"

# Check if MinIO client is available in backup container
docker exec healthstash-backup sh -c '
    # Configure MinIO client
    minio-mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} > /dev/null 2>&1
    
    # Remove all files from healthstash-files bucket
    echo "Removing all files from MinIO..."
    minio-mc rm minio/healthstash-files --recursive --force 2>/dev/null || true
    
    # Count remaining files
    remaining=$(minio-mc ls minio/healthstash-files --recursive 2>/dev/null | wc -l)
    echo "Files remaining in MinIO: $remaining"
'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MinIO storage cleared${NC}"
else
    echo -e "${YELLOW}⚠ MinIO clear may have partially failed${NC}"
fi

echo ""

# Step 4: Clear backup files (optional)
echo -e "${BLUE}Step 4: Clear backup files?${NC}"
read -p "Also delete all backup files? (y/N): " clear_backups

if [ "$clear_backups" = "y" ] || [ "$clear_backups" = "Y" ]; then
    echo "Clearing backup files..."
    docker exec healthstash-backup sh -c 'rm -f /backups/healthstash_backup_*.tar.gz* 2>/dev/null || true'
    docker exec healthstash-backup sh -c 'ls -la /backups/*.tar.gz* 2>/dev/null | wc -l || echo "0"'
    echo -e "${GREEN}✓ Backup files cleared${NC}"
else
    echo -e "${BLUE}Backup files preserved${NC}"
fi

echo ""

# Step 5: Clear any temporary files
echo -e "${BLUE}Step 5: Clearing temporary files...${NC}"

# Clear any temp files in containers
docker exec healthstash-backend sh -c 'rm -rf /tmp/* 2>/dev/null || true'
docker exec healthstash-backup sh -c 'rm -rf /tmp/restore_* /tmp/verify_* 2>/dev/null || true'

echo -e "${GREEN}✓ Temporary files cleared${NC}"

echo ""

# Step 6: VERIFICATION - Confirm everything was actually deleted
echo -e "${BLUE}Step 6: Verifying data deletion...${NC}"
echo ""

VERIFICATION_PASSED=true

# Verify PostgreSQL tables are empty
echo "Checking PostgreSQL tables..."
PG_RESULT=$(docker exec healthstash-postgres psql -U healthstash -d healthstash -t << 'EOF'
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':health_records:' || COUNT(*) 
FROM health_records
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':payment_records:' || COUNT(*) 
FROM payment_records
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':payment_files:' || COUNT(*) 
FROM payment_files
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':audit_logs:' || COUNT(*) 
FROM audit_logs
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':backup_history:' || COUNT(*) 
FROM backup_history
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':record_tags:' || COUNT(*) 
FROM record_tags
UNION ALL
SELECT 
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END || ':tags:' || COUNT(*) 
FROM tags
UNION ALL
SELECT 
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END || ':users_preserved:' || COUNT(*) 
FROM users;
EOF
)

while IFS= read -r line; do
    if [[ -z "$line" ]]; then continue; fi
    
    STATUS=$(echo "$line" | cut -d':' -f1 | xargs)
    TABLE=$(echo "$line" | cut -d':' -f2)
    COUNT=$(echo "$line" | cut -d':' -f3 | xargs)
    
    if [[ "$TABLE" == "users_preserved" ]]; then
        if [[ "$STATUS" == "PASS" ]]; then
            echo -e "  ${GREEN}✓${NC} Users preserved: ${COUNT} accounts"
        else
            echo -e "  ${RED}✗${NC} ERROR: No users found! Count: ${COUNT}"
            VERIFICATION_PASSED=false
        fi
    else
        if [[ "$STATUS" == "PASS" ]]; then
            echo -e "  ${GREEN}✓${NC} ${TABLE}: EMPTY (${COUNT} records)"
        else
            echo -e "  ${RED}✗${NC} ${TABLE}: FAILED - Still has ${COUNT} records!"
            VERIFICATION_PASSED=false
        fi
    fi
done <<< "$PG_RESULT"

echo ""

# Verify TimescaleDB is empty
echo "Checking TimescaleDB vital signs..."
# Check if vital_signs table exists and count records
VITAL_EXISTS=$(docker exec healthstash-timescale psql -U healthstash -d healthstash -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'vital_signs';" 2>/dev/null | xargs)

if [[ "$VITAL_EXISTS" == "0" ]]; then
    echo -e "  ${GREEN}✓${NC} vital_signs: Table does not exist (OK)"
else
    VITAL_COUNT=$(docker exec healthstash-timescale psql -U healthstash -d healthstash -t -c "SELECT COUNT(*) FROM vital_signs;" 2>/dev/null | xargs)
    if [[ "$VITAL_COUNT" == "0" ]]; then
        echo -e "  ${GREEN}✓${NC} vital_signs: EMPTY (0 records)"
    else
        echo -e "  ${RED}✗${NC} vital_signs: FAILED - Still has ${VITAL_COUNT} records!"
        VERIFICATION_PASSED=false
    fi
fi

echo ""

# Verify MinIO is empty
echo "Checking MinIO storage..."
MINIO_COUNT=$(docker exec healthstash-backup sh -c '
    minio-mc alias set minio http://${MINIO_ENDPOINT} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} > /dev/null 2>&1
    minio-mc ls minio/healthstash-files --recursive 2>/dev/null | wc -l
' | xargs)

if [[ "$MINIO_COUNT" == "0" ]]; then
    echo -e "  ${GREEN}✓${NC} MinIO storage: EMPTY (${MINIO_COUNT} files)"
else
    echo -e "  ${RED}✗${NC} MinIO storage: FAILED - Still has ${MINIO_COUNT} files!"
    VERIFICATION_PASSED=false
fi

echo ""

# Check if backups were cleared
if [ "$clear_backups" = "y" ] || [ "$clear_backups" = "Y" ]; then
    echo "Checking backup files..."
    BACKUP_COUNT=$(docker exec healthstash-backup sh -c 'ls /backups/healthstash_backup_*.tar.gz* 2>/dev/null | wc -l' | xargs)
    if [[ "$BACKUP_COUNT" == "0" ]]; then
        echo -e "  ${GREEN}✓${NC} Backup files: CLEARED (${BACKUP_COUNT} files)"
    else
        echo -e "  ${RED}✗${NC} Backup files: Still has ${BACKUP_COUNT} files!"
        VERIFICATION_PASSED=false
    fi
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
if [ "$VERIFICATION_PASSED" = true ]; then
    echo -e "${GREEN}    ✓ DATA WIPE VERIFIED SUCCESSFUL     ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo -e "${GREEN}Verification Results:${NC}"
    echo "  ✓ All health records deleted"
    echo "  ✓ All payment records deleted"  
    echo "  ✓ All MinIO files deleted"
    echo "  ✓ All vital signs deleted"
    echo "  ✓ All audit logs deleted"
    echo "  ✓ All backup history deleted"
    echo "  ✓ User accounts preserved"
else
    echo -e "${RED}    ✗ DATA WIPE VERIFICATION FAILED     ${NC}"
    echo -e "${RED}=========================================${NC}"
    echo ""
    echo -e "${RED}ERROR: Some data was not properly deleted!${NC}"
    echo -e "${RED}Check the verification results above.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Note: You may need to refresh your browser and clear cache${NC}"
echo -e "${YELLOW}to see the changes in the web interface.${NC}"