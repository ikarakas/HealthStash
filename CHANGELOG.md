# Changelog

All notable changes to HealthStash will be documented in this file.

## [0.0.4] - 2025-08-24

### Added
- **Invoice/Payment Vault Feature** - Complete payment tracking system with encryption
  - Create, view, edit, and delete payment records
  - Link payments to health records (optional)
  - Multi-file upload support for invoices and receipts
  - Filter by provider, date range, and payment status
  - Summary statistics dashboard
  - EUR currency support
- **Enhanced Admin Panel**
  - Added creation and update date columns to User Management
  - Shows storage quota information (5GB default per user)
- **Improved Container Health Monitoring**
  - Fixed nginx health check by switching from wget to curl
  - All containers now report healthy status

### Changed
- Default currency changed from USD to EUR
- API endpoints now accept both date and datetime formats
- Improved error handling for date parsing

### Fixed
- Payment API sorting error with underscore fields
- Date/datetime validation errors in forms
- Nginx container health check failures
- API endpoint trailing slash redirects
- Frontend axios configuration for proper authentication

### Technical
- Updated bcrypt authentication library warnings (cosmetic)
- Improved JWT token management
- Enhanced container logging and monitoring

## [0.0.3] - 2025-08-23

### Added
- Password reset functionality
- Enhanced backup and restore features
- Improved test coverage
- Frontend testing with Vitest

### Changed
- Improved backup monitoring system
- Enhanced health record creation workflow
- Better error handling in API endpoints

## [0.0.2] - 2025-08-22

### Added
- Backup monitoring dashboard
- Health record categories
- Thumbnail generation for documents
- Mobile upload feature

### Changed
- Improved sorting logic in Records view
- Enhanced file upload handling
- Better error messages

## [0.0.1] - 2025-08-21

### Initial Release
- Core health record management
- Secure file encryption and storage
- User authentication and authorization
- Basic admin panel
- Docker containerization
- MinIO integration for object storage