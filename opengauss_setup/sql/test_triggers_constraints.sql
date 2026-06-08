-- SQL tests for integrity constraints, triggers, views, and transactional guards.
-- Run after migrate_triggers_constraints_20260608.sql.
-- The whole script rolls back so seed data is not polluted.

START TRANSACTION;

\echo 'Running trigger and constraint tests. All test data will be rolled back.'

DO $$
DECLARE
    v_admin_user BIGINT;
    v_teacher_user BIGINT;
    v_student_user BIGINT;
    v_student_user_2 BIGINT;
    v_student_user_3 BIGINT;
    v_student_user_4 BIGINT;
    v_student_id VARCHAR(20) := 'TST_STU_001';
    v_student_id_2 VARCHAR(20) := 'TST_STU_002';
    v_student_id_3 VARCHAR(20) := 'TST_STU_003';
    v_student_id_4 VARCHAR(20) := 'TST_STU_004';
    v_semester_id VARCHAR(20) := 'TST-SEM-1';
    v_capacity_offering BIGINT;
    v_time_offering_1 BIGINT;
    v_time_offering_2 BIGINT;
    v_unique_offering BIGINT;
    v_score_enrollment BIGINT;
    v_log_count INTEGER;
    v_failed BOOLEAN;
BEGIN
    SELECT user_id INTO v_admin_user FROM user_account WHERE username = 'admin';

    INSERT INTO user_account (username, password_hash, role)
    VALUES ('tst_teacher_user', 'test_hash', 'teacher')
    RETURNING user_id INTO v_teacher_user;

    INSERT INTO user_account (username, password_hash, role)
    VALUES ('tst_student_user', 'test_hash', 'student')
    RETURNING user_id INTO v_student_user;

    INSERT INTO user_account (username, password_hash, role)
    VALUES ('tst_student_user_2', 'test_hash', 'student')
    RETURNING user_id INTO v_student_user_2;

    INSERT INTO user_account (username, password_hash, role)
    VALUES ('tst_student_user_3', 'test_hash', 'student')
    RETURNING user_id INTO v_student_user_3;

    INSERT INTO user_account (username, password_hash, role)
    VALUES ('tst_student_user_4', 'test_hash', 'student')
    RETURNING user_id INTO v_student_user_4;

    v_failed := FALSE;
    BEGIN
        INSERT INTO student (student_id, user_id, student_name, major_id, status)
        VALUES ('TST_BAD_STU', v_teacher_user, '错误学生档案', 'CS01', 'enrolled');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS role check teacher-as-student failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected teacher user inserted as student to fail';
    END IF;

    v_failed := FALSE;
    BEGIN
        INSERT INTO teacher (teacher_id, user_id, teacher_name, dept_id, status)
        VALUES ('TST_BAD_TEA', v_student_user, '错误教师档案', 'CS', 'active');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS role check student-as-teacher failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected student user inserted as teacher to fail';
    END IF;

    INSERT INTO student (student_id, user_id, student_name, major_id, status)
    VALUES
        (v_student_id, v_student_user, '测试学生一', 'CS01', 'enrolled'),
        (v_student_id_2, v_student_user_2, '测试学生二', 'CS01', 'enrolled'),
        (v_student_id_3, v_student_user_3, '测试学生三', 'CS01', 'enrolled'),
        (v_student_id_4, v_student_user_4, '测试学生四', 'CS01', 'enrolled');

    INSERT INTO course (course_id, course_name, course_type, credit, total_hours, dept_id)
    VALUES
        ('TST_A', '测试课程A', 'elective', 1.0, 16, 'CS'),
        ('TST_B', '测试课程B', 'elective', 1.0, 16, 'CS'),
        ('TST_C', '测试课程C', 'elective', 1.0, 16, 'CS'),
        ('TST_CAP', '测试容量课程', 'elective', 1.0, 16, 'CS'),
        ('TST_TIME1', '测试时间课程1', 'elective', 1.0, 16, 'CS'),
        ('TST_TIME2', '测试时间课程2', 'elective', 1.0, 16, 'CS'),
        ('TST_UNIQ', '测试重复课程', 'elective', 1.0, 16, 'CS');

    v_failed := FALSE;
    BEGIN
        INSERT INTO course_prerequisite (course_id, prereq_course_id)
        VALUES ('CS101', 'CS101');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS self prerequisite failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected self prerequisite to fail';
    END IF;

    INSERT INTO course_prerequisite (course_id, prereq_course_id)
    VALUES ('TST_A', 'TST_B'), ('TST_B', 'TST_C');

    v_failed := FALSE;
    BEGIN
        INSERT INTO course_prerequisite (course_id, prereq_course_id)
        VALUES ('TST_C', 'TST_A');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS prerequisite cycle failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected prerequisite cycle to fail';
    END IF;

    INSERT INTO classroom (classroom_id, building, room_no, capacity)
    VALUES ('TST_R1', '测试楼', '101', 1),
           ('TST_R2', '测试楼', '102', 10);

    INSERT INTO semester (
        semester_id, semester_name, start_date, end_date,
        selection_start, selection_end, status
    ) VALUES (
        v_semester_id, '测试学期',
        CURRENT_DATE - 1, CURRENT_DATE + 30,
        CURRENT_TIMESTAMP - INTERVAL '1 day',
        CURRENT_TIMESTAMP + INTERVAL '1 day',
        'open'
    );

    INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, status)
    VALUES ('TST_CAP', v_semester_id, 'T001', 'TST_R1', 1, 'open')
    RETURNING offering_id INTO v_capacity_offering;
    INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
    VALUES (v_capacity_offering, 6, 11, 12);

    INSERT INTO enrollment (student_id, offering_id, status)
    VALUES (v_student_id, v_capacity_offering, 'selected');

    v_failed := FALSE;
    BEGIN
        INSERT INTO enrollment (student_id, offering_id, status)
        VALUES (v_student_id_2, v_capacity_offering, 'selected');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS capacity full failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected second enrollment over capacity to fail';
    END IF;

    INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, status)
    VALUES ('TST_TIME1', v_semester_id, 'T001', 'TST_R2', 10, 'open')
    RETURNING offering_id INTO v_time_offering_1;
    INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
    VALUES (v_time_offering_1, 2, 3, 4);

    INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, status)
    VALUES ('TST_TIME2', v_semester_id, 'T001', 'TST_R2', 10, 'open')
    RETURNING offering_id INTO v_time_offering_2;
    INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
    VALUES (v_time_offering_2, 2, 4, 5);

    INSERT INTO enrollment (student_id, offering_id, status)
    VALUES (v_student_id_3, v_time_offering_1, 'selected');

    v_failed := FALSE;
    BEGIN
        INSERT INTO enrollment (student_id, offering_id, status)
        VALUES (v_student_id_3, v_time_offering_2, 'selected');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS timetable conflict failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected timetable conflict to fail';
    END IF;

    INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, status)
    VALUES ('TST_UNIQ', v_semester_id, 'T001', 'TST_R2', 10, 'open')
    RETURNING offering_id INTO v_unique_offering;
    INSERT INTO course_schedule (offering_id, weekday, start_section, end_section)
    VALUES (v_unique_offering, 4, 9, 10);

    INSERT INTO enrollment (student_id, offering_id, status)
    VALUES (v_student_id_4, v_unique_offering, 'dropped');

    v_failed := FALSE;
    BEGIN
        INSERT INTO enrollment (student_id, offering_id, status)
        VALUES (v_student_id_4, v_unique_offering, 'selected');
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS unique student/offering failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected duplicate student/offering to fail';
    END IF;

    INSERT INTO enrollment (student_id, offering_id, status)
    VALUES (v_student_id_2, v_time_offering_1, 'selected')
    RETURNING enrollment_id INTO v_score_enrollment;

    v_failed := FALSE;
    BEGIN
        UPDATE enrollment
        SET final_score = 80
        WHERE enrollment_id = v_score_enrollment;
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS score update without user failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected score update without app.current_user_id to fail';
    END IF;

    PERFORM set_config('app.current_user_id', CAST(v_admin_user AS VARCHAR), true);
    PERFORM set_config('app.score_change_reason', 'SQL trigger test', true);

    UPDATE enrollment
    SET final_score = 88,
        status = 'completed'
    WHERE enrollment_id = v_score_enrollment;

    SELECT COUNT(*) INTO v_log_count
    FROM score_change_log
    WHERE enrollment_id = v_score_enrollment
      AND old_score IS NULL
      AND new_score = 88
      AND changed_by_user_id = v_admin_user;

    IF v_log_count <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one score_change_log row, got %', v_log_count;
    END IF;
    RAISE NOTICE 'PASS score audit trigger inserted log row';

    v_failed := FALSE;
    BEGIN
        UPDATE enrollment
        SET status = 'dropped'
        WHERE enrollment_id = v_score_enrollment;
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS completed enrollment drop failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected completed enrollment drop to fail';
    END IF;
END;
$$;

\echo 'View smoke test: v_offering_selected_count'
SELECT offering_id, max_capacity, selected_count, remaining_capacity
FROM v_offering_selected_count
ORDER BY offering_id
LIMIT 5;

\echo 'View smoke test: v_course_offering_detail'
SELECT offering_id, course_name, teacher_name, selected_count, remaining_capacity, schedule_text
FROM v_course_offering_detail
ORDER BY offering_id
LIMIT 5;

\echo 'View smoke test: v_student_timetable'
SELECT student_id, course_name, weekday, start_section, end_section
FROM v_student_timetable
ORDER BY student_id, weekday, start_section
LIMIT 5;

ROLLBACK;

\echo 'Trigger and constraint tests finished with rollback.'
