#!/bin/bash

# Setup cron job for automated backups
if [ ! -z "${BACKUP_SCHEDULE}" ]; then
    echo "Setting up backup schedule: ${BACKUP_SCHEDULE}"
    echo "${BACKUP_SCHEDULE} /backup/backup.sh >> /var/log/backup.log 2>&1" | crontab -
    
    # Start cron daemon
    crond -f -l 2
else
    echo "No backup schedule configured. Running in manual mode."
    tail -f /dev/null
fi