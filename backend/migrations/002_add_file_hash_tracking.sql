-- Migration: Add file hash tracking for duplicate detection
-- Date: 2025-12-05

-- Add file_hash column to test_results table
ALTER TABLE test_results 
ADD COLUMN file_hash VARCHAR(64);

-- Create index for fast lookups (user_id + file_hash for duplicate detection)
CREATE INDEX idx_test_results_file_hash ON test_results(user_id, file_hash);

-- Add comment for documentation
COMMENT ON COLUMN test_results.file_hash IS 'SHA-256 hash of the uploaded file for duplicate detection. Scoped per user.';
