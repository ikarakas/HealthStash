# HealthStash - Personal Health Data Vault

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.0.4-blue.svg)](https://github.com/yourusername/healthstash/releases)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

A self-hosted, privacy-first personal health data management system for families. HealthStash provides encrypted storage for medical records and health data without any external sharing capabilities.

**Author:** Ilker M. KARAKAS  
**License:** MIT License  
**Latest Version:** 0.0.4

## Features

### Core Capabilities
- **Multi-user Support**: Separate accounts for each family member with role-based access control
- **Encrypted Storage**: End-to-end encryption for all stored files using AES-256
- **File Management**: Support for PDFs, images, DICOM files, lab reports, and documents
- **Health Data Organization**: Chronological timeline, categories, custom tags, and filtering
- **Vital Signs Tracking**: Time-series storage for heart rate, blood pressure, weight, glucose, etc.
- **Mobile Integration**: Import data from Apple HealthKit and Google Fit
- **Automated Backups**: Scheduled encrypted backups with configurable retention
- **Full-text Search**: Search within uploaded documents (PDFs, text files)
- **Audit Logging**: Complete audit trail of all system activities

### Security Features
- User-specific encryption keys derived from passwords
- TLS/SSL support for all communications
- Session management with configurable timeout
- Account lockout after failed login attempts
- No telemetry or external service calls
- Complete data isolation between users

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Minimum 2GB RAM, 2 CPU cores, 50GB storage
- Recommended: 4GB RAM, 4 CPU cores, 500GB storage

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/healthstash.git
cd healthstash
```

2. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your secure passwords and settings
```

3. Generate secure keys:
```bash
# Generate random keys for encryption and JWT
openssl rand -base64 32  # Use for SECRET_KEY
openssl rand -base64 32  # Use for ENCRYPTION_KEY
openssl rand -base64 32  # Use for JWT_SECRET_KEY
```

4. Start the application:
```bash
docker-compose up -d
```

5. Access the application:
- Web Interface: http://localhost
- API Documentation: http://localhost:8000/docs

The first registered user automatically becomes an admin.

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Security (MUST CHANGE)
SECRET_KEY=your-32-char-secret-key
ENCRYPTION_KEY=your-32-char-encryption-key
JWT_SECRET_KEY=your-32-char-jwt-key

# Database
POSTGRES_PASSWORD=strong-password
TIMESCALE_PASSWORD=strong-password
REDIS_PASSWORD=strong-password

# Storage
MINIO_ROOT_PASSWORD=strong-password
MAX_UPLOAD_SIZE_MB=500
DEFAULT_USER_QUOTA_MB=5000

# Backup
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30

# Password Policy
MIN_PASSWORD_LENGTH=12
REQUIRE_UPPERCASE=true
REQUIRE_LOWERCASE=true
REQUIRE_NUMBERS=true
REQUIRE_SPECIAL_CHARS=true
```

### SSL/TLS Configuration

To enable HTTPS:

1. Place your SSL certificates in `nginx/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

2. Uncomment the HTTPS server block in `nginx/nginx.conf`

3. Update the HTTP server to redirect to HTTPS

## Usage

### User Management

**Admin Functions:**
- Create new user accounts
- Reset user passwords
- Set storage quotas
- Monitor system usage
- Manage backups

**User Functions:**
- Upload medical records and documents
- Add personal health notes
- Track vital signs
- Import data from health apps
- Search and filter records
- Download personal data

### File Upload

Supported file types:
- Documents: PDF, DOC, DOCX, TXT, RTF
- Images: JPEG, PNG, GIF, BMP, TIFF
- Medical: DICOM (.dcm)
- Data: XLS, XLSX, CSV, JSON, XML, HL7

Maximum file size: 500MB (configurable)

### Health Data Import

1. **Apple Health:**
   - Export data from Health app
   - Upload the export.zip file
   - Data automatically parsed and stored

2. **Google Fit:**
   - Use Google Takeout to export Fit data
   - Upload the JSON files
   - Vital signs extracted and stored

### Backup and Restore

**Automated Backups:**
- Configured via `BACKUP_SCHEDULE` cron expression
- Includes database, files, and configuration
- Encrypted with optional password
- Old backups auto-deleted based on retention policy

**Manual Backup:**
```bash
docker exec healthstash-backup /backup/backup.sh
```

**Restore from Backup:**
```bash
docker exec healthstash-backup /backup/restore.sh /backups/backup_file.tar.gz
```

## Architecture

### Technology Stack

**Backend:**
- FastAPI (Python) - REST API
- PostgreSQL - Primary database
- TimescaleDB - Time-series data
- Redis - Session management
- MinIO - Object storage
- Celery - Background tasks

**Frontend:**
- Vue.js 3 - UI framework
- Vite - Build tool
- Pinia - State management
- Chart.js - Data visualization
- Tailwind CSS - Styling

**Infrastructure:**
- Docker Compose - Container orchestration
- Nginx - Reverse proxy
- Alpine Linux - Base images

### Data Flow

1. All requests go through Nginx reverse proxy
2. Authentication verified via JWT tokens
3. Files encrypted before storage in MinIO
4. Metadata stored in PostgreSQL
5. Time-series data in TimescaleDB
6. Sessions cached in Redis

## API Documentation

The API follows RESTful principles and is documented with OpenAPI/Swagger.

### Key Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/token` - Login
- `GET /api/records` - List health records
- `POST /api/files/upload` - Upload file
- `GET /api/vitals` - Get vital signs data
- `POST /api/vitals` - Add vital sign measurement
- `GET /api/admin/users` - List users (admin only)
- `POST /api/backup` - Trigger manual backup

Full API documentation available at `/docs` when the application is running.

## Development

### Local Development Setup

1. Install Python 3.11+ and Node.js 18+
2. Set up virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Run services locally:
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
cd frontend
npm run dev
```

### Running Tests

All tests are organized in the `tests/` directory.

```bash
# Quick test runner from root
./test.sh integration    # Run integration tests
./test.sh security       # Run security tests
./test.sh all           # Run all tests

# Or use the test suite directly
cd tests
./run-all-tests.sh      # Run integration tests (default)
./run-tests.sh --all    # Run comprehensive test suite

# Specific test types
python tests/comprehensive_test.py      # System integration test
python tests/test_user_isolation.py     # Security isolation test

# Backend tests
cd backend && pytest tests/

# Frontend tests  
cd frontend && npm test

# End-to-end tests
npx playwright test --config=tests/playwright.config.js
```

See `tests/README.md` for detailed testing documentation.

## Troubleshooting

### Common Issues

**Container fails to start:**
- Check logs: `docker-compose logs [service_name]`
- Verify all required environment variables are set
- Ensure ports 80 and 443 are not in use

**Cannot upload files:**
- Check user storage quota
- Verify file size is under limit
- Ensure file type is allowed

**Backup fails:**
- Check disk space in backup directory
- Verify database credentials
- Review backup container logs

**Performance issues:**
- Increase Docker memory allocation
- Check database query performance
- Consider adding indexes for frequently searched fields

## Security Considerations

1. **Always change default passwords** in production
2. **Use strong, unique passwords** for all services
3. **Enable HTTPS** with valid SSL certificates
4. **Regular backups** to separate storage
5. **Keep Docker images updated** for security patches
6. **Review audit logs** regularly
7. **Restrict network access** to trusted IPs only
8. **Use firewall rules** to limit exposed ports

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation

## Roadmap

Planned features:
- [ ] Two-factor authentication (TOTP)
- [ ] Medication tracking and reminders
- [ ] Family health history charts
- [ ] OCR for automatic document text extraction
- [ ] FHIR standard support
- [ ] Mobile app (PWA enhancement)
- [ ] Appointment scheduling
- [ ] Insurance information management
- [ ] Emergency contact management
- [ ] Medical provider directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Ilker M. KARAKAS**

## Acknowledgments

- Thanks to all the open-source projects that make HealthStash possible
- Special thanks to the FastAPI, Vue.js, PostgreSQL, and Docker communities
- Icons from various emoji sets

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
*Copyright (c) 2025 Ilker M. KARAKAS - All Rights Reserved*