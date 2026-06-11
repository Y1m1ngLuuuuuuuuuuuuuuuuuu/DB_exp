-- Database role and least-privilege grant design for openGauss.
-- Run after migrate_triggers_constraints_20260608.sql and
-- migrate_grade_policy_20260611.sql so all views/functions exist.
-- This script is optional for production hardening. The current demo app still
-- connects through the configured application account, so do not run this
-- blindly against a shared environment without reviewing the grants.

START TRANSACTION;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'db_student_role') THEN
        EXECUTE 'CREATE ROLE db_student_role WITH NOLOGIN PASSWORD DISABLE';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'db_teacher_role') THEN
        EXECUTE 'CREATE ROLE db_teacher_role WITH NOLOGIN PASSWORD DISABLE';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'db_admin_role') THEN
        EXECUTE 'CREATE ROLE db_admin_role WITH NOLOGIN PASSWORD DISABLE';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'db_app_role') THEN
        EXECUTE 'CREATE ROLE db_app_role WITH NOLOGIN PASSWORD DISABLE';
    END IF;
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO
    db_student_role,
    db_teacher_role,
    db_admin_role,
    db_app_role;

-- Student-facing direct database role: read course/catalog capacity views only.
-- Per-student filtering remains an application-layer responsibility.
GRANT SELECT ON
    v_course_offering_detail,
    v_offering_selected_count,
    v_student_gpa_summary
TO db_student_role;

-- Teacher-facing direct database role: read teaching task and score audit data.
-- Score writes should still go through the application service or controlled
-- functions so app.current_user_id can be set for audit triggers.
GRANT SELECT ON
    v_course_offering_detail,
    v_student_timetable,
    v_enrollment_grade_detail,
    v_student_gpa_summary,
    score_change_log,
    enrollment,
    student
TO db_teacher_role;

-- Application service role: can execute guarded functions and use base tables.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO db_app_role;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO db_app_role;
GRANT EXECUTE ON FUNCTION select_course_tx(VARCHAR, BIGINT) TO db_app_role;
GRANT EXECUTE ON FUNCTION calculate_gpa(DECIMAL, BIGINT) TO db_app_role;

-- Admin role for database-level maintenance.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO db_admin_role;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO db_admin_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO db_admin_role;

COMMIT;
