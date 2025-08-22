#!/bin/bash

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="healthstash_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Alerting function
send_alert() {
    local message="$1"
    local severity="${2:-ERROR}"
    
    # Log to file
    echo "[${severity}] $(date): ${message}" >> /var/log/backup-alerts.log
    
    # If webhook URL is configured, send alert
    if [ ! -z "${ALERT_WEBHOOK_URL}" ]; then
        curl -X POST "${ALERT_WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[HealthStash Backup ${severity}] ${message}\"}" 2>/dev/null || true
    fi
}

# Trap errors and alert
trap 'send_alert "Backup failed at line $LINENO: $BASH_COMMAND" ERROR; exit 1' ERR

echo "Starting backup at $(date)"

# Optional: Enable maintenance mode
if [ "${ENABLE_MAINTENANCE_MODE}" = "true" ]; then
    echo "Enabling maintenance mode..."
    touch /backups/.maintenance_mode
    sleep 5  # Give applications time to see maintenance mode
fi

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

# Encryption with multiple options
if [ "${ENCRYPTION_METHOD}" = "age" ] && command -v age &> /dev/null; then
    # Use age encryption if available (more modern)
    echo "Encrypting backup with age..."
    BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}"
    echo "${BACKUP_ENCRYPTION_KEY}" | age -e -p -o ${BACKUP_PATH}.tar.gz.age ${BACKUP_PATH}.tar.gz
    rm ${BACKUP_PATH}.tar.gz
    FINAL_BACKUP="${BACKUP_PATH}.tar.gz.age"
else
    # Fallback to OpenSSL with CBC (since GCM not available in Alpine)
    BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}"
    echo "Encrypting backup with OpenSSL AES-256-CBC..."
    
    openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
        -in ${BACKUP_PATH}.tar.gz \
        -out ${BACKUP_PATH}.tar.gz.enc \
        -pass pass:"${BACKUP_ENCRYPTION_KEY}"
    
    if [ $? -eq 0 ]; then
        rm ${BACKUP_PATH}.tar.gz
        FINAL_BACKUP="${BACKUP_PATH}.tar.gz.enc"
        
        # If no key was provided, save the generated key securely
        if [ -z "${BACKUP_ENCRYPTION_KEY_PROVIDED}" ]; then
            echo "WARNING: Generated encryption key: ${BACKUP_ENCRYPTION_KEY}"
            echo "IMPORTANT: Save this key securely - you'll need it to restore the backup!"
        fi
    else
        send_alert "Encryption failed, keeping unencrypted backup" "WARNING"
        FINAL_BACKUP="${BACKUP_PATH}.tar.gz"
    fi
fi

# Clean up uncompressed files
rm -rf ${BACKUP_PATH}

# Upload to offsite storage if configured
if [ ! -z "${OFFSITE_BACKUP_ENDPOINT}" ]; then
    echo "Uploading backup to offsite storage..."
    
    if [ "${OFFSITE_TYPE}" = "s3" ]; then
        # Configure offsite S3-compatible storage
        minio-mc alias set offsite ${OFFSITE_BACKUP_ENDPOINT} ${OFFSITE_ACCESS_KEY} ${OFFSITE_SECRET_KEY}
        
        # Upload with versioning
        minio-mc cp ${FINAL_BACKUP} offsite/${OFFSITE_BUCKET}/backups/
        
        # Enable versioning and object lock if configured
        if [ "${ENABLE_IMMUTABILITY}" = "true" ]; then
            minio-mc version enable offsite/${OFFSITE_BUCKET}
            minio-mc retention set --default GOVERNANCE 30d offsite/${OFFSITE_BUCKET}
        fi
        
        send_alert "Backup uploaded to offsite storage: ${OFFSITE_BACKUP_ENDPOINT}" "INFO"
    elif [ "${OFFSITE_TYPE}" = "rsync" ]; then
        # Use rsync for offsite backup
        rsync -avz ${FINAL_BACKUP} ${OFFSITE_RSYNC_DEST}
        send_alert "Backup synced to offsite location: ${OFFSITE_RSYNC_DEST}" "INFO"
    fi
fi

# Remove old backups based on retention policy
if [ ! -z "${BACKUP_RETENTION_DAYS}" ]; then
    echo "Removing backups older than ${BACKUP_RETENTION_DAYS} days..."
    find ${BACKUP_DIR} -name "healthstash_backup_*.tar.gz*" -mtime +${BACKUP_RETENTION_DAYS} -delete
fi

# Disable maintenance mode
if [ "${ENABLE_MAINTENANCE_MODE}" = "true" ]; then
    echo "Disabling maintenance mode..."
    rm -f /backups/.maintenance_mode
fi

echo "Backup completed successfully: ${FINAL_BACKUP}"
echo "Backup size: $(du -h ${FINAL_BACKUP} | cut -f1)"

# Update backup status in database - don't fail entire backup if this fails
update_backup_status() {
    local backup_size_bytes=$(stat -c%s "${FINAL_BACKUP}" 2>/dev/null || echo "0")
    local backup_id=$(uuidgen || echo "backup_$(date +%s)")
    
    # Check if pgcrypto extension exists
    PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST} \
        -U ${POSTGRES_USER} \
        -d ${POSTGRES_DB} \
        -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" 2>/dev/null || true
    
    PGPASSWORD=${POSTGRES_PASSWORD} psql \
        -h ${POSTGRES_HOST} \
        -U ${POSTGRES_USER} \
        -d ${POSTGRES_DB} \
        -c "INSERT INTO backup_history (id, backup_type, status, file_path, file_size, size_mb, completed_at, created_at) 
            VALUES ('${backup_id}', 'FULL', 'COMPLETED', '${FINAL_BACKUP}', 
            ${backup_size_bytes}, $(echo "scale=2; ${backup_size_bytes}/1048576" | bc), NOW(), NOW());" 2>/dev/null || \
    echo "Warning: Failed to update backup history in database"
}

trap update_backup_status EXIT

# Send success alert
send_alert "Backup completed successfully: ${FINAL_BACKUP} ($(du -h ${FINAL_BACKUP} | cut -f1))" "SUCCESS"