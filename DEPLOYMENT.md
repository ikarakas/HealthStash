# HealthStash Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed
- 2GB RAM minimum (4GB recommended)
- 50GB storage minimum

### 2. Initial Setup

```bash
# Clone or download the repository
cd HealthStash

# Make scripts executable
chmod +x startup.sh

# Run the initialization script
./startup.sh
```

The startup script will:
- Create `.env` from template
- Generate secure encryption keys
- Build Docker images
- Start all services

### 3. First Login

1. Open your browser to http://localhost
2. Click "Register" to create the first account
3. The first user automatically becomes admin

## Manual Setup

If you prefer manual setup:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate secure keys
openssl rand -base64 32  # Use for SECRET_KEY
openssl rand -base64 32  # Use for ENCRYPTION_KEY
openssl rand -base64 32  # Use for JWT_SECRET_KEY

# 3. Edit .env file with your keys and passwords

# 4. Build and start services
docker-compose build
docker-compose up -d

# 5. Check service health
docker-compose ps
```

## Using Make Commands

The Makefile provides convenient commands:

```bash
make init      # Initialize application (first time)
make up        # Start services
make down      # Stop services
make logs      # View logs
make backup    # Create backup
make health    # Check service health
```

## Configuration

### Essential Settings in `.env`

```env
# MUST CHANGE - Security Keys
SECRET_KEY=<generated-32-char-key>
ENCRYPTION_KEY=<generated-32-char-key>
JWT_SECRET_KEY=<generated-32-char-key>

# MUST CHANGE - Database Passwords
POSTGRES_PASSWORD=<strong-password>
TIMESCALE_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
MINIO_ROOT_PASSWORD=<strong-password>

# Optional - Adjust as needed
MAX_UPLOAD_SIZE_MB=500
DEFAULT_USER_QUOTA_MB=5000
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
```

### SSL/TLS Setup

For production deployment with HTTPS:

1. Obtain SSL certificates
2. Place certificates in `nginx/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key
3. Update `nginx/nginx.conf` to enable HTTPS
4. Update `.env`: `VITE_API_URL=https://yourdomain.com`

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs [service_name]

# Check if ports are in use
netstat -tulpn | grep -E '80|443|8000'

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker exec -it healthstash-postgres psql -U healthstash -d healthstash
```

### Storage Issues

```bash
# Check MinIO
docker-compose logs minio

# Access MinIO console (if enabled)
# Set MINIO_BROWSER=on in .env
# Visit http://localhost:9001
```

### Reset Everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Remove data directories
rm -rf postgres_data timescale_data redis_data minio_data backup_data

# Start fresh
make init
```

## Backup and Restore

### Create Backup

```bash
# Manual backup
make backup

# Or using docker directly
docker exec healthstash-backup /backup/backup.sh
```

### Restore from Backup

```bash
# Using make
make restore
# Enter backup file path when prompted

# Or directly
docker exec healthstash-backup /backup/restore.sh /backups/backup_file.tar.gz
```

### Automated Backups

Backups run automatically based on `BACKUP_SCHEDULE` in `.env` (cron format).

Default: `0 2 * * *` (daily at 2 AM)

## Security Checklist

- [ ] Changed all default passwords in `.env`
- [ ] Generated new encryption keys
- [ ] Configured firewall rules
- [ ] Enabled HTTPS for production
- [ ] Regular backup schedule configured
- [ ] Restricted database access
- [ ] Updated all Docker images

## Monitoring

### Check Service Health

```bash
make health
```

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Resource Usage

```bash
docker stats
```

## Updating

To update HealthStash:

1. Backup your data first
2. Pull latest changes
3. Rebuild images:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify configuration in `.env`
3. Ensure all prerequisites are met
4. Check available disk space