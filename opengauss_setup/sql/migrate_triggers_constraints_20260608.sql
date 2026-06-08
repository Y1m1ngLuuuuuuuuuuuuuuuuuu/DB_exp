-- Integrity, trigger, transaction and view completion migration for openGauss.
-- This script keeps the 3NF design: it does NOT restore selected_count,
-- schedule_text, or gpa_point as base table columns.

START TRANSACTION;

-- Drop dependent objects first so this migration can be re-run safely.
DROP VIEW IF EXISTS v_student_timetable;
DROP VIEW IF EXISTS v_course_offering_detail;
DROP VIEW IF EXISTS v_offering_selected_count;

DROP TRIGGER IF EXISTS trg_student_role_check ON student;
DROP TRIGGER IF EXISTS trg_teacher_role_check ON teacher;
DROP TRIGGER IF EXISTS trg_admin_role_check ON admin_profile;
DROP TRIGGER IF EXISTS trg_prerequisite_no_cycle ON course_prerequisite;
DROP TRIGGER IF EXISTS trg_enrollment_guard ON enrollment;
DROP TRIGGER IF EXISTS trg_score_change_log ON enrollment;
DROP TRIGGER IF EXISTS trg_offering_capacity_check ON course_offering;
DROP TRIGGER IF EXISTS trg_classroom_capacity_update_check ON classroom;

DROP FUNCTION IF EXISTS select_course_tx(VARCHAR, BIGINT) CASCADE;
DROP FUNCTION IF EXISTS trg_score_change_log_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_enrollment_guard_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_prerequisite_no_cycle_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_offering_capacity_check_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_classroom_capacity_update_check_fn() CASCADE;
DROP FUNCTION IF EXISTS trg_profile_role_check_fn() CASCADE;
DROP FUNCTION IF EXISTS check_user_role_fn(BIGINT, VARCHAR) CASCADE;

ALTER TABLE department DROP CONSTRAINT IF EXISTS uq_department_name;
ALTER TABLE major DROP CONSTRAINT IF EXISTS uq_major_dept_name;
ALTER TABLE classroom DROP CONSTRAINT IF EXISTS uq_classroom_location;
ALTER TABLE course_prerequisite DROP CONSTRAINT IF EXISTS chk_prereq_not_self;
ALTER TABLE semester DROP CONSTRAINT IF EXISTS chk_semester_date_range;
ALTER TABLE user_session DROP CONSTRAINT IF EXISTS chk_user_session_time_range;
ALTER TABLE course_schedule DROP CONSTRAINT IF EXISTS chk_schedule_section_range;

-- Data repair before adding cross-table capacity trigger.
-- Existing seed data had MA101 offerings with max_capacity 60 in M201(capacity 50).
UPDATE course_offering co
SET max_capacity = c.capacity
FROM classroom c
WHERE co.classroom_id = c.classroom_id
  AND co.max_capacity > c.capacity;

ALTER TABLE department
    ADD CONSTRAINT uq_department_name UNIQUE (dept_name);

ALTER TABLE major
    ADD CONSTRAINT uq_major_dept_name UNIQUE (dept_id, major_name);

ALTER TABLE classroom
    ADD CONSTRAINT uq_classroom_location UNIQUE (building, room_no);

ALTER TABLE course_prerequisite
    ADD CONSTRAINT chk_prereq_not_self CHECK (course_id <> prereq_course_id);

ALTER TABLE semester
    ADD CONSTRAINT chk_semester_date_range CHECK (
        start_date <= end_date
        AND (
            selection_start IS NULL
            OR selection_end IS NULL
            OR selection_start <= selection_end
        )
    );

ALTER TABLE user_session
    ADD CONSTRAINT chk_user_session_time_range CHECK (
        expires_at > created_at
        AND (revoked_at IS NULL OR revoked_at >= created_at)
    );

ALTER TABLE course_schedule
    ADD CONSTRAINT chk_schedule_section_range CHECK (
        start_section BETWEEN 1 AND 12
        AND end_section BETWEEN start_section AND 12
    );

CREATE OR REPLACE FUNCTION check_user_role_fn(
    p_user_id BIGINT,
    p_expected_role VARCHAR
) RETURNS void AS $$
DECLARE
    v_role VARCHAR(20);
BEGIN
    SELECT role INTO v_role
    FROM user_account
    WHERE user_id = p_user_id;

    IF v_role IS NULL THEN
        RAISE EXCEPTION 'User account % does not exist', p_user_id;
    END IF;

    IF v_role <> p_expected_role THEN
        RAISE EXCEPTION 'User % role is %, expected %',
            p_user_id, v_role, p_expected_role;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_profile_role_check_fn()
RETURNS trigger AS $$
BEGIN
    PERFORM check_user_role_fn(NEW.user_id, TG_ARGV[0]);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_offering_capacity_check_fn()
RETURNS trigger AS $$
DECLARE
    v_classroom_capacity INTEGER;
    v_selected_count INTEGER;
BEGIN
    IF NEW.classroom_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT capacity INTO v_classroom_capacity
    FROM classroom
    WHERE classroom_id = NEW.classroom_id;

    IF v_classroom_capacity IS NULL THEN
        RAISE EXCEPTION 'Classroom % does not exist', NEW.classroom_id;
    END IF;

    IF NEW.max_capacity > v_classroom_capacity THEN
        RAISE EXCEPTION 'Offering capacity % exceeds classroom % capacity %',
            NEW.max_capacity, NEW.classroom_id, v_classroom_capacity;
    END IF;

    SELECT COUNT(*) INTO v_selected_count
    FROM enrollment
    WHERE offering_id = NEW.offering_id
      AND status = 'selected';

    IF v_selected_count > NEW.max_capacity THEN
        RAISE EXCEPTION 'Offering capacity % is lower than current selected count %',
            NEW.max_capacity, v_selected_count;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_classroom_capacity_update_check_fn()
RETURNS trigger AS $$
DECLARE
    v_over_limit_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_over_limit_count
    FROM course_offering
    WHERE classroom_id = NEW.classroom_id
      AND max_capacity > NEW.capacity;

    IF v_over_limit_count > 0 THEN
        RAISE EXCEPTION 'Classroom % capacity % is lower than existing offering capacity',
            NEW.classroom_id, NEW.capacity;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_prerequisite_no_cycle_fn()
RETURNS trigger AS $$
DECLARE
    v_cycle_found INTEGER;
BEGIN
    IF NEW.course_id = NEW.prereq_course_id THEN
        RAISE EXCEPTION 'Course % cannot be its own prerequisite', NEW.course_id;
    END IF;

    WITH RECURSIVE prereq_chain(course_id, depth) AS (
        SELECT cp.prereq_course_id, 1
        FROM course_prerequisite cp
        WHERE cp.course_id = NEW.prereq_course_id
          AND NOT (
              TG_OP = 'UPDATE'
              AND cp.course_id = OLD.course_id
              AND cp.prereq_course_id = OLD.prereq_course_id
          )
        UNION ALL
        SELECT cp.prereq_course_id, pc.depth + 1
        FROM course_prerequisite cp
        JOIN prereq_chain pc ON cp.course_id = pc.course_id
        WHERE pc.depth < 100
          AND NOT (
              TG_OP = 'UPDATE'
              AND cp.course_id = OLD.course_id
              AND cp.prereq_course_id = OLD.prereq_course_id
          )
    )
    SELECT COUNT(*) INTO v_cycle_found
    FROM prereq_chain
    WHERE course_id = NEW.course_id;

    IF v_cycle_found > 0 THEN
        RAISE EXCEPTION 'Prerequisite relation % -> % would create a cycle',
            NEW.course_id, NEW.prereq_course_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_enrollment_guard_fn()
RETURNS trigger AS $$
DECLARE
    v_student_status VARCHAR(20);
    v_course_id VARCHAR(20);
    v_semester_id VARCHAR(20);
    v_offering_status VARCHAR(20);
    v_semester_status VARCHAR(20);
    v_selection_start TIMESTAMP;
    v_selection_end TIMESTAMP;
    v_max_capacity INTEGER;
    v_selected_count INTEGER;
    v_conflict_count INTEGER;
    v_missing_prereq_count INTEGER;
    v_old_enrollment_id BIGINT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        v_old_enrollment_id := OLD.enrollment_id;

        IF NEW.status = 'dropped' THEN
            IF OLD.status = 'completed' THEN
                RAISE EXCEPTION 'Completed enrollment % cannot be dropped', OLD.enrollment_id;
            END IF;

            IF OLD.final_score IS NOT NULL THEN
                RAISE EXCEPTION 'Enrollment % has final score and cannot be dropped',
                    OLD.enrollment_id;
            END IF;

            SELECT co.status, s.status, s.selection_start, s.selection_end
              INTO v_offering_status, v_semester_status, v_selection_start, v_selection_end
            FROM course_offering co
            JOIN semester s ON co.semester_id = s.semester_id
            WHERE co.offering_id = OLD.offering_id;

            IF v_offering_status <> 'open' OR v_semester_status <> 'open' THEN
                RAISE EXCEPTION 'Enrollment % cannot be dropped after offering or semester is closed',
                    OLD.enrollment_id;
            END IF;

            IF v_selection_start IS NOT NULL
               AND v_selection_end IS NOT NULL
               AND CURRENT_TIMESTAMP NOT BETWEEN v_selection_start AND v_selection_end THEN
                RAISE EXCEPTION 'Current time is outside drop window';
            END IF;

            RETURN NEW;
        END IF;
    ELSE
        v_old_enrollment_id := NULL;
    END IF;

    IF NEW.status <> 'selected' THEN
        RETURN NEW;
    END IF;

    SELECT status INTO v_student_status
    FROM student
    WHERE student_id = NEW.student_id;

    IF v_student_status IS NULL THEN
        RAISE EXCEPTION 'Student % does not exist', NEW.student_id;
    END IF;

    IF v_student_status <> 'enrolled' THEN
        RAISE EXCEPTION 'Student % status % cannot select courses',
            NEW.student_id, v_student_status;
    END IF;

    SELECT course_id, semester_id, max_capacity, status
      INTO v_course_id, v_semester_id, v_max_capacity, v_offering_status
    FROM course_offering
    WHERE offering_id = NEW.offering_id
    FOR UPDATE;

    IF v_course_id IS NULL THEN
        RAISE EXCEPTION 'Course offering % does not exist', NEW.offering_id;
    END IF;

    SELECT status, selection_start, selection_end
      INTO v_semester_status, v_selection_start, v_selection_end
    FROM semester
    WHERE semester_id = v_semester_id;

    IF v_offering_status <> 'open' THEN
        RAISE EXCEPTION 'Course offering % is not open', NEW.offering_id;
    END IF;

    IF v_semester_status <> 'open' THEN
        RAISE EXCEPTION 'Semester % is not open for selection', v_semester_id;
    END IF;

    IF v_selection_start IS NOT NULL
       AND v_selection_end IS NOT NULL
       AND CURRENT_TIMESTAMP NOT BETWEEN v_selection_start AND v_selection_end THEN
        RAISE EXCEPTION 'Current time is outside course selection window';
    END IF;

    SELECT COUNT(*) INTO v_selected_count
    FROM enrollment e
    WHERE e.offering_id = NEW.offering_id
      AND e.status = 'selected'
      AND (v_old_enrollment_id IS NULL OR e.enrollment_id <> v_old_enrollment_id);

    IF v_selected_count >= v_max_capacity THEN
        RAISE EXCEPTION 'Course offering % is full', NEW.offering_id;
    END IF;

    SELECT COUNT(*) INTO v_conflict_count
    FROM course_schedule target_schedule
    JOIN course_schedule selected_schedule
      ON target_schedule.weekday = selected_schedule.weekday
     AND selected_schedule.start_section <= target_schedule.end_section
     AND selected_schedule.end_section >= target_schedule.start_section
    JOIN enrollment e
      ON e.offering_id = selected_schedule.offering_id
    JOIN course_offering selected_offering
      ON selected_offering.offering_id = e.offering_id
    WHERE target_schedule.offering_id = NEW.offering_id
      AND e.student_id = NEW.student_id
      AND e.status = 'selected'
      AND selected_offering.semester_id = v_semester_id
      AND (v_old_enrollment_id IS NULL OR e.enrollment_id <> v_old_enrollment_id);

    IF v_conflict_count > 0 THEN
        RAISE EXCEPTION 'Student % has a timetable conflict for offering %',
            NEW.student_id, NEW.offering_id;
    END IF;

    SELECT COUNT(*) INTO v_missing_prereq_count
    FROM course_prerequisite cp
    WHERE cp.course_id = v_course_id
      AND NOT EXISTS (
          SELECT 1
          FROM enrollment e
          JOIN course_offering co2 ON e.offering_id = co2.offering_id
          WHERE e.student_id = NEW.student_id
            AND co2.course_id = cp.prereq_course_id
            AND e.status = 'completed'
            AND e.final_score >= 60
      );

    IF v_missing_prereq_count > 0 THEN
        RAISE EXCEPTION 'Student % has not passed all prerequisites for course %',
            NEW.student_id, v_course_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_score_change_log_fn()
RETURNS trigger AS $$
DECLARE
    v_changed_by_user_id BIGINT;
    v_reason VARCHAR(200);
BEGIN
    IF (OLD.final_score IS NULL AND NEW.final_score IS NULL)
       OR (
           OLD.final_score IS NOT NULL
           AND NEW.final_score IS NOT NULL
           AND OLD.final_score = NEW.final_score
       ) THEN
        RETURN NEW;
    END IF;

    BEGIN
        v_changed_by_user_id := current_setting('app.current_user_id')::BIGINT;
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Score update requires app.current_user_id in the current transaction';
    END;

    BEGIN
        v_reason := current_setting('app.score_change_reason');
    EXCEPTION WHEN OTHERS THEN
        v_reason := 'score updated';
    END;

    IF v_reason IS NULL OR LENGTH(TRIM(v_reason)) = 0 THEN
        v_reason := 'score updated';
    END IF;

    INSERT INTO score_change_log
        (enrollment_id, old_score, new_score, changed_by_user_id, reason)
    VALUES
        (NEW.enrollment_id, OLD.final_score, NEW.final_score,
         v_changed_by_user_id, v_reason);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION select_course_tx(
    p_student_id VARCHAR,
    p_offering_id BIGINT
) RETURNS BIGINT AS $$
DECLARE
    v_enrollment_id BIGINT;
    v_existing_status VARCHAR(20);
BEGIN
    SELECT enrollment_id, status
      INTO v_enrollment_id, v_existing_status
    FROM enrollment
    WHERE student_id = p_student_id
      AND offering_id = p_offering_id
    FOR UPDATE;

    IF v_enrollment_id IS NOT NULL THEN
        IF v_existing_status = 'selected' THEN
            RAISE EXCEPTION 'Student % has already selected offering %',
                p_student_id, p_offering_id;
        END IF;

        IF v_existing_status = 'completed' THEN
            RAISE EXCEPTION 'Completed enrollment cannot be selected again';
        END IF;

        UPDATE enrollment
        SET status = 'selected',
            select_time = CURRENT_TIMESTAMP
        WHERE enrollment_id = v_enrollment_id
        RETURNING enrollment_id INTO v_enrollment_id;

        RETURN v_enrollment_id;
    END IF;

    PERFORM 1
    FROM course_offering
    WHERE offering_id = p_offering_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Course offering % does not exist', p_offering_id;
    END IF;

    INSERT INTO enrollment (student_id, offering_id, status, select_time)
    VALUES (p_student_id, p_offering_id, 'selected', CURRENT_TIMESTAMP)
    RETURNING enrollment_id INTO v_enrollment_id;

    RETURN v_enrollment_id;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_student_role_check
BEFORE INSERT OR UPDATE OF user_id ON student
FOR EACH ROW
EXECUTE PROCEDURE trg_profile_role_check_fn('student');

CREATE TRIGGER trg_teacher_role_check
BEFORE INSERT OR UPDATE OF user_id ON teacher
FOR EACH ROW
EXECUTE PROCEDURE trg_profile_role_check_fn('teacher');

CREATE TRIGGER trg_admin_role_check
BEFORE INSERT OR UPDATE OF user_id ON admin_profile
FOR EACH ROW
EXECUTE PROCEDURE trg_profile_role_check_fn('admin');

CREATE TRIGGER trg_offering_capacity_check
BEFORE INSERT OR UPDATE OF classroom_id, max_capacity ON course_offering
FOR EACH ROW
EXECUTE PROCEDURE trg_offering_capacity_check_fn();

CREATE TRIGGER trg_classroom_capacity_update_check
BEFORE UPDATE OF capacity ON classroom
FOR EACH ROW
EXECUTE PROCEDURE trg_classroom_capacity_update_check_fn();

CREATE TRIGGER trg_prerequisite_no_cycle
BEFORE INSERT OR UPDATE ON course_prerequisite
FOR EACH ROW
EXECUTE PROCEDURE trg_prerequisite_no_cycle_fn();

CREATE TRIGGER trg_enrollment_guard
BEFORE INSERT OR UPDATE OF student_id, offering_id, status ON enrollment
FOR EACH ROW
EXECUTE PROCEDURE trg_enrollment_guard_fn();

CREATE TRIGGER trg_score_change_log
AFTER UPDATE OF final_score ON enrollment
FOR EACH ROW
EXECUTE PROCEDURE trg_score_change_log_fn();

CREATE OR REPLACE VIEW v_offering_selected_count AS
SELECT
    co.offering_id,
    co.max_capacity,
    COALESCE(COUNT(e.enrollment_id), 0)::INTEGER AS selected_count,
    (co.max_capacity - COALESCE(COUNT(e.enrollment_id), 0))::INTEGER AS remaining_capacity
FROM course_offering co
LEFT JOIN enrollment e
  ON e.offering_id = co.offering_id
 AND e.status = 'selected'
GROUP BY co.offering_id, co.max_capacity;

CREATE OR REPLACE VIEW v_course_offering_detail AS
SELECT
    co.offering_id,
    co.course_id,
    c.course_name,
    c.course_type,
    c.credit,
    co.semester_id,
    sem.semester_name,
    co.teacher_id,
    t.teacher_name,
    co.classroom_id,
    cl.building,
    cl.room_no,
    cl.capacity AS classroom_capacity,
    co.max_capacity,
    v.selected_count,
    v.remaining_capacity,
    co.status,
    COALESCE((
        SELECT STRING_AGG(
            CASE cs.weekday
                WHEN 1 THEN '周一'
                WHEN 2 THEN '周二'
                WHEN 3 THEN '周三'
                WHEN 4 THEN '周四'
                WHEN 5 THEN '周五'
                WHEN 6 THEN '周六'
                WHEN 7 THEN '周日'
            END || ' ' || CAST(cs.start_section AS VARCHAR) || '-' ||
            CAST(cs.end_section AS VARCHAR) || ' 节',
            ' / ' ORDER BY cs.weekday, cs.start_section, cs.end_section
        )
        FROM course_schedule cs
        WHERE cs.offering_id = co.offering_id
    ), '') AS schedule_text
FROM course_offering co
JOIN course c ON co.course_id = c.course_id
JOIN semester sem ON co.semester_id = sem.semester_id
JOIN teacher t ON co.teacher_id = t.teacher_id
LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
JOIN v_offering_selected_count v ON co.offering_id = v.offering_id;

CREATE OR REPLACE VIEW v_student_timetable AS
SELECT
    s.student_id,
    s.student_name,
    e.enrollment_id,
    co.offering_id,
    co.semester_id,
    sem.semester_name,
    c.course_id,
    c.course_name,
    t.teacher_id,
    t.teacher_name,
    cl.building,
    cl.room_no,
    cs.weekday,
    cs.start_section,
    cs.end_section
FROM student s
JOIN enrollment e ON s.student_id = e.student_id
JOIN course_offering co ON e.offering_id = co.offering_id
JOIN semester sem ON co.semester_id = sem.semester_id
JOIN course c ON co.course_id = c.course_id
JOIN teacher t ON co.teacher_id = t.teacher_id
LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
JOIN course_schedule cs ON co.offering_id = cs.offering_id
WHERE e.status = 'selected';

CREATE INDEX IF NOT EXISTS idx_score_log_enrollment
    ON score_change_log (enrollment_id);
CREATE INDEX IF NOT EXISTS idx_score_log_changed_at
    ON score_change_log (changed_at);
CREATE INDEX IF NOT EXISTS idx_course_prereq_prereq
    ON course_prerequisite (prereq_course_id);

COMMIT;
