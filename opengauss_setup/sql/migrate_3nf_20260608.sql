-- 3NF normalization migration for existing openGauss databases.
-- Review and back up the database before running this script.
-- The project code after 2026-06-08 expects:
--   1. course_schedule exists.
--   2. course_offering.selected_count no longer exists.
--   3. course_offering.schedule_text no longer exists.
--   4. enrollment.gpa_point no longer exists.

START TRANSACTION;

DROP TRIGGER IF EXISTS trg_enrollment_insert ON enrollment;
DROP TRIGGER IF EXISTS trg_enrollment_update ON enrollment;
DROP FUNCTION IF EXISTS trg_enrollment_insert_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_enrollment_update_fn() CASCADE;

CREATE TABLE IF NOT EXISTS course_schedule (
    schedule_id   BIGSERIAL   NOT NULL,
    offering_id   BIGINT      NOT NULL,
    weekday       SMALLINT    NOT NULL,
    start_section SMALLINT    NOT NULL,
    end_section   SMALLINT    NOT NULL,
    PRIMARY KEY (schedule_id),
    CONSTRAINT fk_schedule_offering FOREIGN KEY (offering_id)
        REFERENCES course_offering (offering_id) ON DELETE CASCADE,
    CONSTRAINT uq_schedule_slot UNIQUE (offering_id, weekday, start_section, end_section),
    CONSTRAINT chk_schedule_weekday CHECK (weekday BETWEEN 1 AND 7),
    CONSTRAINT chk_schedule_section CHECK (start_section > 0 AND end_section >= start_section)
);

-- The parser below supports the format used by the app:
--   周一 1-2 节 / 周三 3-4 节
-- If your database contains custom schedule text, inspect course_schedule
-- before dropping course_offering.schedule_text.
INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
SELECT parsed.offering_id,
       parsed.weekday,
       parsed.start_section,
       parsed.end_section
FROM (
    SELECT co.offering_id,
           CASE SUBSTRING(TRIM(part) FROM '周[一二三四五六日天]')
               WHEN '周一' THEN 1
               WHEN '周二' THEN 2
               WHEN '周三' THEN 3
               WHEN '周四' THEN 4
               WHEN '周五' THEN 5
               WHEN '周六' THEN 6
               WHEN '周日' THEN 7
               WHEN '周天' THEN 7
           END AS weekday,
           CAST(SUBSTRING(TRIM(part) FROM '[0-9]+') AS SMALLINT) AS start_section,
           CAST(SUBSTRING(TRIM(part) FROM '-[ ]*([0-9]+)') AS SMALLINT) AS end_section
    FROM course_offering co,
         REGEXP_SPLIT_TO_TABLE(co.schedule_text, '[ ]*/[ ]*') AS part
    WHERE co.schedule_text IS NOT NULL
      AND TRIM(part) <> ''
) parsed
WHERE parsed.weekday IS NOT NULL
  AND parsed.start_section IS NOT NULL
  AND parsed.end_section IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM course_schedule cs
      WHERE cs.offering_id = parsed.offering_id
        AND cs.weekday = parsed.weekday
        AND cs.start_section = parsed.start_section
        AND cs.end_section = parsed.end_section
  );

ALTER TABLE course_offering DROP COLUMN IF EXISTS selected_count;
ALTER TABLE course_offering DROP COLUMN IF EXISTS schedule_text;
ALTER TABLE enrollment DROP COLUMN IF EXISTS gpa_point;

CREATE INDEX IF NOT EXISTS idx_offering_course_semester
    ON course_offering (course_id, semester_id);
CREATE INDEX IF NOT EXISTS idx_offering_teacher_semester
    ON course_offering (teacher_id, semester_id);
CREATE INDEX IF NOT EXISTS idx_schedule_offering
    ON course_schedule (offering_id);
CREATE INDEX IF NOT EXISTS idx_schedule_time
    ON course_schedule (weekday, start_section, end_section);
CREATE INDEX IF NOT EXISTS idx_enrollment_student_status
    ON enrollment (student_id, status);
CREATE INDEX IF NOT EXISTS idx_enrollment_offering_status
    ON enrollment (offering_id, status);

COMMIT;
