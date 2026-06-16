-- Grade policy versioning migration for openGauss.
-- This keeps the 3NF direction: enrollment.gpa_point is NOT restored.

START TRANSACTION;

DROP VIEW IF EXISTS v_student_gpa_summary;
DROP VIEW IF EXISTS v_enrollment_grade_detail;

DROP FUNCTION IF EXISTS trg_grade_scale_no_overlap_fn() CASCADE;
DROP FUNCTION IF EXISTS calculate_gpa(NUMERIC, BIGINT) CASCADE;

CREATE TABLE IF NOT EXISTS grade_policy (
    policy_id          BIGSERIAL    NOT NULL,
    policy_code        VARCHAR(30)  NOT NULL,
    policy_name        VARCHAR(100) NOT NULL,
    version_no         VARCHAR(20)  NOT NULL,
    effective_from     DATE         NOT NULL,
    effective_to       DATE,
    status             VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_by_user_id BIGINT,
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (policy_id)
);

CREATE TABLE IF NOT EXISTS grade_scale (
    scale_id    BIGSERIAL    NOT NULL,
    policy_id   BIGINT       NOT NULL,
    min_score   DECIMAL(5,2) NOT NULL,
    max_score   DECIMAL(5,2) NOT NULL,
    gpa_point   DECIMAL(3,2) NOT NULL,
    grade_label VARCHAR(10),
    sort_order  INTEGER,
    PRIMARY KEY (scale_id)
);

DROP TRIGGER IF EXISTS trg_grade_scale_no_overlap ON grade_scale;

ALTER TABLE grade_policy DROP CONSTRAINT IF EXISTS uq_grade_policy_code_version;
ALTER TABLE grade_policy DROP CONSTRAINT IF EXISTS chk_grade_policy_status;
ALTER TABLE grade_policy DROP CONSTRAINT IF EXISTS chk_grade_policy_effective_range;
ALTER TABLE grade_policy DROP CONSTRAINT IF EXISTS fk_grade_policy_created_by;

ALTER TABLE grade_scale DROP CONSTRAINT IF EXISTS fk_grade_scale_policy;
ALTER TABLE grade_scale DROP CONSTRAINT IF EXISTS chk_grade_scale_score_range;
ALTER TABLE grade_scale DROP CONSTRAINT IF EXISTS chk_grade_scale_gpa_range;
ALTER TABLE grade_scale DROP CONSTRAINT IF EXISTS uq_grade_scale_range;

ALTER TABLE semester DROP CONSTRAINT IF EXISTS fk_semester_grade_policy;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'semester'
          AND column_name = 'grade_policy_id'
    ) THEN
        ALTER TABLE semester ADD COLUMN grade_policy_id BIGINT;
    END IF;
END;
$$;

ALTER TABLE grade_policy
    ADD CONSTRAINT uq_grade_policy_code_version UNIQUE (policy_code, version_no);

ALTER TABLE grade_policy
    ADD CONSTRAINT chk_grade_policy_status CHECK (status IN ('draft','active','retired'));

ALTER TABLE grade_policy
    ADD CONSTRAINT chk_grade_policy_effective_range
    CHECK (effective_to IS NULL OR effective_to >= effective_from);

ALTER TABLE grade_policy
    ADD CONSTRAINT fk_grade_policy_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES user_account (user_id);

ALTER TABLE grade_scale
    ADD CONSTRAINT fk_grade_scale_policy
    FOREIGN KEY (policy_id) REFERENCES grade_policy (policy_id) ON DELETE CASCADE;

ALTER TABLE grade_scale
    ADD CONSTRAINT chk_grade_scale_score_range
    CHECK (min_score >= 0 AND max_score <= 100 AND max_score >= min_score);

ALTER TABLE grade_scale
    ADD CONSTRAINT chk_grade_scale_gpa_range
    CHECK (gpa_point >= 0 AND gpa_point <= 5);

ALTER TABLE grade_scale
    ADD CONSTRAINT uq_grade_scale_range UNIQUE (policy_id, min_score, max_score);

ALTER TABLE semester
    ADD CONSTRAINT fk_semester_grade_policy
    FOREIGN KEY (grade_policy_id) REFERENCES grade_policy (policy_id);

CREATE OR REPLACE FUNCTION trg_grade_scale_no_overlap_fn()
RETURNS trigger AS $$
DECLARE
    v_overlap_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_overlap_count
    FROM grade_scale gs
    WHERE gs.policy_id = NEW.policy_id
      AND NEW.min_score <= gs.max_score
      AND NEW.max_score >= gs.min_score
      AND (
          TG_OP = 'INSERT'
          OR gs.scale_id <> NEW.scale_id
      );

    IF v_overlap_count > 0 THEN
        RAISE EXCEPTION 'Grade scale range %.% overlaps existing range for policy %',
            NEW.min_score, NEW.max_score, NEW.policy_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_grade_scale_no_overlap
BEFORE INSERT OR UPDATE OF policy_id, min_score, max_score ON grade_scale
FOR EACH ROW
EXECUTE PROCEDURE trg_grade_scale_no_overlap_fn();

CREATE OR REPLACE FUNCTION calculate_gpa(
    p_score DECIMAL,
    p_policy_id BIGINT
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    v_match_count INTEGER;
    v_gpa DECIMAL(3,2);
BEGIN
    IF p_score IS NULL THEN
        RETURN NULL;
    END IF;

    IF p_policy_id IS NULL THEN
        RAISE EXCEPTION 'Grade policy is required when calculating GPA';
    END IF;

    SELECT COUNT(*), MIN(gpa_point)
      INTO v_match_count, v_gpa
    FROM grade_scale
    WHERE policy_id = p_policy_id
      AND p_score >= min_score
      AND p_score <= max_score;

    IF v_match_count = 0 THEN
        RAISE EXCEPTION 'No GPA scale found for score % under policy %',
            p_score, p_policy_id;
    END IF;

    IF v_match_count > 1 THEN
        RAISE EXCEPTION 'Multiple GPA scales found for score % under policy %',
            p_score, p_policy_id;
    END IF;

    RETURN v_gpa;
END;
$$ LANGUAGE plpgsql;

INSERT INTO grade_policy (
    policy_code, policy_name, version_no,
    effective_from, effective_to, status, created_by_user_id
)
SELECT
    'DEFAULT_4_0',
    '默认百分制绩点规则',
    'v1',
    DATE '2025-09-01',
    NULL,
    'active',
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM grade_policy
    WHERE policy_code = 'DEFAULT_4_0'
      AND version_no = 'v1'
);

UPDATE grade_policy
SET policy_name = '默认百分制绩点规则',
    effective_from = DATE '2025-09-01',
    effective_to = NULL,
    status = 'active'
WHERE policy_code = 'DEFAULT_4_0'
  AND version_no = 'v1';

DELETE FROM grade_scale
WHERE policy_id = (
    SELECT policy_id
    FROM grade_policy
    WHERE policy_code = 'DEFAULT_4_0'
      AND version_no = 'v1'
);

INSERT INTO grade_scale (
    policy_id, min_score, max_score, gpa_point, grade_label, sort_order
)
SELECT p.policy_id, v.min_score, v.max_score, v.gpa_point, v.grade_label, v.sort_order
FROM grade_policy p
CROSS JOIN (
    VALUES
        (90.00::DECIMAL(5,2), 100.00::DECIMAL(5,2), 4.00::DECIMAL(3,2), 'A',  1),
        (85.00::DECIMAL(5,2),  89.99::DECIMAL(5,2), 3.70::DECIMAL(3,2), 'A-', 2),
        (82.00::DECIMAL(5,2),  84.99::DECIMAL(5,2), 3.30::DECIMAL(3,2), 'B+', 3),
        (78.00::DECIMAL(5,2),  81.99::DECIMAL(5,2), 3.00::DECIMAL(3,2), 'B',  4),
        (75.00::DECIMAL(5,2),  77.99::DECIMAL(5,2), 2.70::DECIMAL(3,2), 'B-', 5),
        (72.00::DECIMAL(5,2),  74.99::DECIMAL(5,2), 2.30::DECIMAL(3,2), 'C+', 6),
        (68.00::DECIMAL(5,2),  71.99::DECIMAL(5,2), 2.00::DECIMAL(3,2), 'C',  7),
        (64.00::DECIMAL(5,2),  67.99::DECIMAL(5,2), 1.50::DECIMAL(3,2), 'D+', 8),
        (60.00::DECIMAL(5,2),  63.99::DECIMAL(5,2), 1.00::DECIMAL(3,2), 'D',  9),
        ( 0.00::DECIMAL(5,2),  59.99::DECIMAL(5,2), 0.00::DECIMAL(3,2), 'F', 10)
) AS v(min_score, max_score, gpa_point, grade_label, sort_order)
WHERE p.policy_code = 'DEFAULT_4_0'
  AND p.version_no = 'v1';

UPDATE semester
SET grade_policy_id = (
    SELECT policy_id
    FROM grade_policy
    WHERE policy_code = 'DEFAULT_4_0'
      AND version_no = 'v1'
)
WHERE grade_policy_id IS NULL;

CREATE OR REPLACE VIEW v_enrollment_grade_detail AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.offering_id,
    co.course_id,
    co.semester_id,
    e.status AS enrollment_status,
    e.final_score,
    sem.grade_policy_id AS policy_id,
    gp.policy_name,
    gp.version_no,
    gs.grade_label,
    CASE
        WHEN e.final_score IS NULL THEN NULL
        ELSE calculate_gpa(e.final_score, sem.grade_policy_id)
    END AS gpa_point,
    c.credit
FROM enrollment e
JOIN course_offering co ON e.offering_id = co.offering_id
JOIN semester sem ON co.semester_id = sem.semester_id
JOIN course c ON co.course_id = c.course_id
LEFT JOIN grade_policy gp ON sem.grade_policy_id = gp.policy_id
LEFT JOIN grade_scale gs
  ON gs.policy_id = sem.grade_policy_id
 AND e.final_score >= gs.min_score
 AND e.final_score <= gs.max_score;

CREATE OR REPLACE VIEW v_student_gpa_summary AS
SELECT
    student_id,
    semester_id,
    SUM(credit)::DECIMAL(8,2) AS total_credits,
    ROUND(
        SUM(gpa_point * credit) / NULLIF(SUM(credit), 0),
        2
    )::DECIMAL(4,2) AS weighted_gpa,
    COUNT(*)::INTEGER AS completed_course_count
FROM v_enrollment_grade_detail
WHERE enrollment_status = 'completed'
  AND final_score IS NOT NULL
  AND gpa_point IS NOT NULL
  AND credit > 0
GROUP BY student_id, semester_id;

CREATE INDEX IF NOT EXISTS idx_semester_grade_policy
    ON semester (grade_policy_id);
CREATE INDEX IF NOT EXISTS idx_grade_scale_policy_range
    ON grade_scale (policy_id, min_score, max_score);

COMMIT;
