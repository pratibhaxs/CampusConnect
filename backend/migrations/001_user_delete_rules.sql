-- Run ONCE on an existing MySQL database (create_all() does not alter existing tables).
-- New databases created from the updated models already have these rules.
--
-- 1. Find the auto-generated foreign key names:
--      SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
--      WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME = 'users' AND COLUMN_NAME = 'user_id';
-- 2. Replace the names below (typically experiences_ibfk_1, reports_ibfk_1, bookmarks_ibfk_1, helpful_votes_ibfk_1).

ALTER TABLE experiences MODIFY user_id INT NULL;
ALTER TABLE experiences DROP FOREIGN KEY experiences_ibfk_1;
ALTER TABLE experiences ADD CONSTRAINT fk_experiences_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE reports MODIFY user_id INT NULL;
ALTER TABLE reports DROP FOREIGN KEY reports_ibfk_1;
ALTER TABLE reports ADD CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE bookmarks DROP FOREIGN KEY bookmarks_ibfk_1;
ALTER TABLE bookmarks ADD CONSTRAINT fk_bookmarks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE helpful_votes DROP FOREIGN KEY helpful_votes_ibfk_1;
ALTER TABLE helpful_votes ADD CONSTRAINT fk_helpful_votes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
