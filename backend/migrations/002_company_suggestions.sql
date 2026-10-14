-- Run ONCE on an existing MySQL database, BEFORE deploying the new backend.
-- (create_all() only creates missing tables; it does not add columns.)
-- Then run:  python migrations/002_backfill_normalized_names.py

ALTER TABLE companies
  ADD COLUMN normalized_name VARCHAR(200) NULL,
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved',
  ADD COLUMN created_by INT NULL,
  ADD COLUMN similar_to_id INT NULL,
  ADD CONSTRAINT fk_companies_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  ADD CONSTRAINT fk_companies_similar_to FOREIGN KEY (similar_to_id) REFERENCES companies(id) ON DELETE SET NULL;

ALTER TABLE roles
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved',
  ADD COLUMN created_by INT NULL,
  ADD CONSTRAINT fk_roles_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- After the backfill script has filled normalized_name for every row:
-- ALTER TABLE companies MODIFY normalized_name VARCHAR(200) NOT NULL, ADD UNIQUE KEY uq_companies_normalized_name (normalized_name);
