#!/bin/bash

# Start the trigger watcher in background
echo "Starting backup trigger watcher..."
/backup/trigger-watcher.sh >> /var/log/trigger-watcher.log 2>&1 &
WATCHER_PID=$!
echo "Trigger watcher started with PID: ${WATCHER_PID}"

# Setup cron job for automated backups
if [ ! -z "${BACKUP_SCHEDULE}" ]; then
    echo "Setting up backup schedule: ${BACKUP_SCHEDULE}"
    # Run backup script as backup user
    echo "${BACKUP_SCHEDULE} su - backup -c '/backup/backup.sh' >> /var/log/backup.log 2>&1" | crontab -
    
    # Start cron daemon
    echo "Starting cron daemon..."
    crond -f -l 2 &
    CRON_PID=$!
    echo "Cron daemon started with PID: ${CRON_PID}"
else
    echo "No backup schedule configured. Manual mode only."
fi

# Keep container running and monitor processes
echo "Backup service ready. Watching for triggers and scheduled backups..."
while true; do
    # Check if trigger watcher is still running
    if ! kill -0 ${WATCHER_PID} 2>/dev/null; then
        echo "Trigger watcher died, restarting..."
        /backup/trigger-watcher.sh >> /var/log/trigger-watcher.log 2>&1 &
        WATCHER_PID=$!
    fi
    
    sleep 30
done