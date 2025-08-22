#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."

# Load environment variables
source .env

# Apply migration to fix schema mismatches
docker exec -i postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < database/migrations/001_fix_schema_mismatches.sql

if [ $? -eq 0 ]; then
    echo "✓ Migration 001_fix_schema_mismatches.sql applied successfully"
else
    echo "✗ Failed to apply migration 001_fix_schema_mismatches.sql"
    exit 1
fi

echo "All migrations completed successfully!"