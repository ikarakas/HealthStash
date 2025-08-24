#!/bin/bash
# Watch for backup triggers and execute backup.sh when triggered

TRIGGER_DIR="/backups/triggers"
BACKUP_SCRIPT="/backup/backup.sh"

echo "Starting backup trigger watcher..."
echo "Watching directory: ${TRIGGER_DIR}"

# Create trigger directory if it doesn't exist
mkdir -p ${TRIGGER_DIR}

while true; do
    # Check for trigger files
    shopt -s nullglob
    for trigger_file in ${TRIGGER_DIR}/*.trigger; do
        if [ -f "${trigger_file}" ]; then
            echo "Found trigger file: ${trigger_file}"
            
            # Extract backup ID from filename
            BACKUP_ID=$(basename "${trigger_file}" .trigger)
            
            # Read trigger contents
            source "${trigger_file}"
            
            echo "Processing backup ${BACKUP_ID}..."
            
            # Execute the backup script
            export BACKUP_ID="${BACKUP_ID}"
            export BACKUP_SOURCE="${BACKUP_SOURCE:-manual}"
            
            # Run backup and capture result
            if ${BACKUP_SCRIPT}; then
                echo "SUCCESS" > "${TRIGGER_DIR}/${BACKUP_ID}.complete"
                
                # Get the latest backup file info
                LATEST_BACKUP=$(ls -t /backups/healthstash_backup_*.tar.gz.enc 2>/dev/null | head -1)
                if [ -f "${LATEST_BACKUP}" ]; then
                    SIZE_MB=$(du -m "${LATEST_BACKUP}" | cut -f1)
                    echo "FILE=${LATEST_BACKUP}" > "${TRIGGER_DIR}/${BACKUP_ID}.info"
                    echo "SIZE_MB=${SIZE_MB}" >> "${TRIGGER_DIR}/${BACKUP_ID}.info"
                fi
            else
                echo "FAILED: Backup script execution failed" > "${TRIGGER_DIR}/${BACKUP_ID}.complete"
            fi
            
            # Remove trigger file
            rm -f "${trigger_file}"
            
            echo "Backup ${BACKUP_ID} completed"
        fi
    done
    
    # Wait before checking again
    sleep 2
done