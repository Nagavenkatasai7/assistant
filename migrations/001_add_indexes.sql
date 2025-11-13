-- Migration 001: Add Comprehensive Indexes
-- This migration adds indexes to optimize query performance across all tables
-- Expected performance improvement: 10-100x for filtered queries

-- ============================================================================
-- JOB DESCRIPTIONS TABLE INDEXES
-- ============================================================================

-- Most common query: lookup by company name
-- Usage: Dashboard filters, company search
-- Selectivity: High (many jobs per company)
CREATE INDEX IF NOT EXISTS idx_job_company_name
ON job_descriptions(company_name);

-- Date-based queries for history sidebar
-- Usage: Recent jobs, timeline views
-- Selectivity: High (distributed over time)
CREATE INDEX IF NOT EXISTS idx_job_created
ON job_descriptions(created_at DESC);

-- Composite index for company + date queries
-- Usage: "Show me recent jobs from Company X"
-- Selectivity: Very High
-- Column order: company_name (equality) before created_at (range)
CREATE INDEX IF NOT EXISTS idx_job_company_date
ON job_descriptions(company_name, created_at DESC);

-- Job title search index
-- Usage: Search functionality, filtering by role
-- Selectivity: Medium
CREATE INDEX IF NOT EXISTS idx_job_title
ON job_descriptions(job_title);

-- ============================================================================
-- GENERATED RESUMES TABLE INDEXES
-- ============================================================================

-- Foreign key index for job lookups
-- Usage: JOIN operations, finding resume for specific job
-- Selectivity: High (1:1 relationship enforced by UNIQUE constraint)
CREATE INDEX IF NOT EXISTS idx_resume_job_id
ON generated_resumes(job_description_id);

-- Date-based queries for resume history
-- Usage: Recent resumes, timeline display
-- Selectivity: High
CREATE INDEX IF NOT EXISTS idx_resume_created
ON generated_resumes(created_at DESC);

-- ATS score filtering
-- Usage: "Show me high-scoring resumes", performance analytics
-- Selectivity: Medium
CREATE INDEX IF NOT EXISTS idx_resume_ats_score
ON generated_resumes(ats_score DESC);

-- Composite index for job + date queries
-- Usage: Resume history for specific job
-- Selectivity: Very High
CREATE INDEX IF NOT EXISTS idx_resume_job_date
ON generated_resumes(job_description_id, created_at DESC);

-- ============================================================================
-- GENERATED COVER LETTERS TABLE INDEXES
-- ============================================================================

-- Foreign key index for job lookups
-- Usage: JOIN operations, finding cover letter for specific job
-- Selectivity: High
CREATE INDEX IF NOT EXISTS idx_coverletter_job_id
ON generated_cover_letters(job_description_id);

-- Foreign key index for resume lookups
-- Usage: Finding cover letter associated with specific resume
-- Selectivity: Medium (optional relationship)
CREATE INDEX IF NOT EXISTS idx_coverletter_resume_id
ON generated_cover_letters(resume_id);

-- Date-based queries for cover letter history
-- Usage: Recent cover letters, timeline display
-- Selectivity: High
CREATE INDEX IF NOT EXISTS idx_coverletter_created
ON generated_cover_letters(created_at DESC);

-- ============================================================================
-- COMPANY RESEARCH TABLE INDEXES
-- ============================================================================

-- Company name lookup (already has UNIQUE constraint which creates index)
-- This is a cache table, so the unique constraint on company_name
-- already provides an index. No additional index needed.

-- Date-based index for cache invalidation
-- Usage: Finding stale cache entries, cache cleanup
-- Selectivity: High
CREATE INDEX IF NOT EXISTS idx_research_created
ON company_research(created_at);

-- ============================================================================
-- INDEX STATISTICS & VERIFICATION
-- ============================================================================

-- To verify index usage after migration, run:
-- EXPLAIN QUERY PLAN SELECT * FROM job_descriptions WHERE company_name = 'Google';
-- Should show: SEARCH TABLE job_descriptions USING INDEX idx_job_company_name

-- To check index size:
-- SELECT name, tbl_name FROM sqlite_master WHERE type = 'index';

-- Expected index overhead:
-- - Storage: ~15-25% increase in database size
-- - Write performance: ~5-10% slower inserts (minimal due to low write volume)
-- - Read performance: 10-100x faster for indexed queries

-- ============================================================================
-- PERFORMANCE BENCHMARKS (Expected)
-- ============================================================================

-- Before indexes:
-- - Company lookup: ~500ms on 10k records (full table scan)
-- - Date range query: ~800ms on 10k records (full table scan)
-- - JOIN operations: ~1.2s on 10k records (nested loops)

-- After indexes:
-- - Company lookup: ~5ms (B-tree index seek)
-- - Date range query: ~10ms (index range scan)
-- - JOIN operations: ~15ms (index nested loop join)

-- ============================================================================
-- ROLLBACK PLAN
-- ============================================================================

-- If this migration needs to be rolled back, run:
-- DROP INDEX IF EXISTS idx_job_company_name;
-- DROP INDEX IF EXISTS idx_job_created;
-- DROP INDEX IF EXISTS idx_job_company_date;
-- DROP INDEX IF EXISTS idx_job_title;
-- DROP INDEX IF EXISTS idx_resume_job_id;
-- DROP INDEX IF EXISTS idx_resume_created;
-- DROP INDEX IF EXISTS idx_resume_ats_score;
-- DROP INDEX IF EXISTS idx_resume_job_date;
-- DROP INDEX IF EXISTS idx_coverletter_job_id;
-- DROP INDEX IF EXISTS idx_coverletter_resume_id;
-- DROP INDEX IF EXISTS idx_coverletter_created;
-- DROP INDEX IF EXISTS idx_research_created;
