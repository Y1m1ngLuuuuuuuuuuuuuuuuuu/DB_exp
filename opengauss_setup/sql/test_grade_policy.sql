-- SQL tests for grade policy versioning.
-- Run after migrate_grade_policy_20260611.sql.
-- The whole script rolls back test-only rows.

START TRANSACTION;

\echo 'Running grade policy tests. Test-only data will be rolled back.'

DO $$
DECLARE
    v_default_policy_id BIGINT;
    v_test_policy_id BIGINT;
    v_gpa DECIMAL(3,2);
    v_count INTEGER;
    v_failed BOOLEAN;
BEGIN
    SELECT policy_id INTO v_default_policy_id
    FROM grade_policy
    WHERE policy_code = 'DEFAULT_4_0'
      AND version_no = 'v1';

    IF v_default_policy_id IS NULL THEN
        RAISE EXCEPTION 'Default grade policy not found';
    END IF;

    SELECT calculate_gpa(95.00, v_default_policy_id) INTO v_gpa;
    IF v_gpa <> 4.00 THEN
        RAISE EXCEPTION 'Expected GPA 4.00 for score 95, got %', v_gpa;
    END IF;
    RAISE NOTICE 'PASS calculate_gpa 95 -> 4.00';

    SELECT calculate_gpa(59.00, v_default_policy_id) INTO v_gpa;
    IF v_gpa <> 0.00 THEN
        RAISE EXCEPTION 'Expected GPA 0.00 for score 59, got %', v_gpa;
    END IF;
    RAISE NOTICE 'PASS calculate_gpa 59 -> 0.00';

    INSERT INTO grade_policy (
        policy_code, policy_name, version_no, effective_from, status
    )
    VALUES (
        'TEST_POLICY', '测试绩点规则', 'v1', CURRENT_DATE, 'draft'
    )
    RETURNING policy_id INTO v_test_policy_id;

    INSERT INTO grade_scale (
        policy_id, min_score, max_score, gpa_point, grade_label, sort_order
    )
    VALUES
        (v_test_policy_id, 0.00, 59.99, 0.00, 'F', 1),
        (v_test_policy_id, 60.00, 100.00, 4.00, 'P', 2);

    v_failed := FALSE;
    BEGIN
        INSERT INTO grade_scale (
            policy_id, min_score, max_score, gpa_point, grade_label, sort_order
        )
        VALUES (v_test_policy_id, 50.00, 70.00, 2.00, 'X', 3);
    EXCEPTION WHEN OTHERS THEN
        v_failed := TRUE;
        RAISE NOTICE 'PASS overlap grade scale failed: %', SQLERRM;
    END;
    IF NOT v_failed THEN
        RAISE EXCEPTION 'Expected overlapping grade scale to fail';
    END IF;

    SELECT COUNT(*) INTO v_count
    FROM v_enrollment_grade_detail
    WHERE final_score IS NOT NULL
      AND gpa_point IS NOT NULL;
    IF v_count = 0 THEN
        RAISE EXCEPTION 'Expected v_enrollment_grade_detail to return GPA rows';
    END IF;
    RAISE NOTICE 'PASS v_enrollment_grade_detail returned % GPA rows', v_count;

    SELECT COUNT(*) INTO v_count
    FROM v_student_gpa_summary
    WHERE weighted_gpa IS NOT NULL;
    IF v_count = 0 THEN
        RAISE EXCEPTION 'Expected v_student_gpa_summary to return summary rows';
    END IF;
    RAISE NOTICE 'PASS v_student_gpa_summary returned % summary rows', v_count;
END;
$$;

\echo 'View smoke test: v_enrollment_grade_detail'
SELECT student_id, course_id, semester_id, final_score, grade_label, gpa_point
FROM v_enrollment_grade_detail
WHERE final_score IS NOT NULL
ORDER BY student_id, course_id
LIMIT 5;

\echo 'View smoke test: v_student_gpa_summary'
SELECT student_id, semester_id, total_credits, weighted_gpa, completed_course_count
FROM v_student_gpa_summary
ORDER BY student_id, semester_id
LIMIT 5;

ROLLBACK;

\echo 'Grade policy tests finished with rollback.'
