-- Migration: Make service_date mandatory in health_records
-- Date: 2025-08-25
-- Description: Update existing NULL service_dates to created_at and make column NOT NULL

-- Step 1: Update any existing NULL service_date values to use created_at
UPDATE health_records 
SET service_date = created_at 
WHERE service_date IS NULL;

-- Step 2: Alter the column to make it NOT NULL
ALTER TABLE health_records 
ALTER COLUMN service_date SET NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN health_records.service_date IS 'Date when the health service was provided (mandatory)';