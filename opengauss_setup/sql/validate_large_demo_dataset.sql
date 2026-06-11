\echo 'Large demo dataset validation'

\echo '1. Data volume'
SELECT 'department_count' AS metric, COUNT(*) AS value FROM department;
SELECT 'major_count' AS metric, COUNT(*) AS value FROM major;
SELECT 'student_count' AS metric, COUNT(*) AS value FROM student;
SELECT 'teacher_count' AS metric, COUNT(*) AS value FROM teacher;
SELECT 'admin_count' AS metric, COUNT(*) AS value FROM admin_profile;
SELECT 'course_count' AS metric, COUNT(*) AS value FROM course;
SELECT 'semester_count' AS metric, COUNT(*) AS value FROM semester;
SELECT 'classroom_count' AS metric, COUNT(*) AS value FROM classroom;
SELECT 'offering_count' AS metric, COUNT(*) AS value FROM course_offering;
SELECT 'schedule_slot_count' AS metric, COUNT(*) AS value FROM course_schedule;
SELECT 'enrollment_count' AS metric, COUNT(*) AS value FROM enrollment;
SELECT 'score_change_log_count' AS metric, COUNT(*) AS value FROM score_change_log;

\echo '2. Department distribution'
SELECT d.dept_id, d.dept_name,
       COUNT(DISTINCT s.student_id) AS student_count,
       COUNT(DISTINCT t.teacher_id) AS teacher_count,
       COUNT(DISTINCT c.course_id) AS course_count
FROM department d
LEFT JOIN major m ON m.dept_id = d.dept_id
LEFT JOIN student s ON s.major_id = m.major_id
LEFT JOIN teacher t ON t.dept_id = d.dept_id
LEFT JOIN course c ON c.dept_id = d.dept_id
GROUP BY d.dept_id, d.dept_name
ORDER BY d.dept_id;

\echo '3. Selected enrollment capacity violations'
WITH selected_count AS (
    SELECT offering_id, COUNT(*) AS selected_count
    FROM enrollment
    WHERE status = 'selected'
    GROUP BY offering_id
)
SELECT COUNT(*) AS violation_count
FROM course_offering co
LEFT JOIN selected_count sc ON sc.offering_id = co.offering_id
WHERE COALESCE(sc.selected_count, 0) > co.max_capacity;

WITH selected_count AS (
    SELECT offering_id, COUNT(*) AS selected_count
    FROM enrollment
    WHERE status = 'selected'
    GROUP BY offering_id
)
SELECT co.offering_id, co.max_capacity, COALESCE(sc.selected_count, 0) AS selected_count
FROM course_offering co
LEFT JOIN selected_count sc ON sc.offering_id = co.offering_id
WHERE COALESCE(sc.selected_count, 0) > co.max_capacity
ORDER BY co.offering_id
LIMIT 10;

\echo '4. Classroom capacity violations'
SELECT COUNT(*) AS violation_count
FROM course_offering co
JOIN classroom cr ON cr.classroom_id = co.classroom_id
WHERE co.max_capacity > cr.capacity;

SELECT co.offering_id, co.max_capacity, cr.classroom_id, cr.capacity
FROM course_offering co
JOIN classroom cr ON cr.classroom_id = co.classroom_id
WHERE co.max_capacity > cr.capacity
ORDER BY co.offering_id
LIMIT 10;

\echo '5. Duplicate student/offering violations'
SELECT COUNT(*) AS violation_count
FROM (
    SELECT student_id, offering_id
    FROM enrollment
    GROUP BY student_id, offering_id
    HAVING COUNT(*) > 1
) AS duplicated;

\echo '6. Same course cross-offering selected violations'
SELECT COUNT(*) AS violation_count
FROM (
    SELECT e.student_id, co.semester_id, co.course_id, COUNT(DISTINCT co.offering_id) AS offering_count
    FROM enrollment e
    JOIN course_offering co ON co.offering_id = e.offering_id
    WHERE e.status = 'selected'
    GROUP BY e.student_id, co.semester_id, co.course_id
    HAVING COUNT(DISTINCT co.offering_id) > 1
) AS cross_offering;

SELECT e.student_id, co.semester_id, co.course_id, COUNT(DISTINCT co.offering_id) AS offering_count
FROM enrollment e
JOIN course_offering co ON co.offering_id = e.offering_id
WHERE e.status = 'selected'
GROUP BY e.student_id, co.semester_id, co.course_id
HAVING COUNT(DISTINCT co.offering_id) > 1
ORDER BY e.student_id, co.semester_id, co.course_id
LIMIT 10;

\echo '7. Selected timetable conflict violations'
SELECT COUNT(*) AS violation_count
FROM enrollment e1
JOIN enrollment e2
  ON e1.student_id = e2.student_id
 AND e1.enrollment_id < e2.enrollment_id
JOIN course_offering co1 ON co1.offering_id = e1.offering_id
JOIN course_offering co2 ON co2.offering_id = e2.offering_id
JOIN course_schedule cs1 ON cs1.offering_id = co1.offering_id
JOIN course_schedule cs2 ON cs2.offering_id = co2.offering_id
WHERE e1.status = 'selected'
  AND e2.status = 'selected'
  AND co1.semester_id = co2.semester_id
  AND cs1.weekday = cs2.weekday
  AND cs1.start_section <= cs2.end_section
  AND cs1.end_section >= cs2.start_section;

\echo '8. Prerequisite violations for selected/completed records'
SELECT COUNT(*) AS violation_count
FROM enrollment e
JOIN course_offering co ON co.offering_id = e.offering_id
JOIN course_prerequisite cp ON cp.course_id = co.course_id
WHERE e.status IN ('selected','completed')
  AND NOT EXISTS (
      SELECT 1
      FROM enrollment ep
      JOIN course_offering cop ON cop.offering_id = ep.offering_id
      WHERE ep.student_id = e.student_id
        AND cop.course_id = cp.prereq_course_id
        AND ep.status = 'completed'
        AND ep.final_score >= 60
  );

SELECT e.student_id, co.course_id, cp.prereq_course_id, e.status
FROM enrollment e
JOIN course_offering co ON co.offering_id = e.offering_id
JOIN course_prerequisite cp ON cp.course_id = co.course_id
WHERE e.status IN ('selected','completed')
  AND NOT EXISTS (
      SELECT 1
      FROM enrollment ep
      JOIN course_offering cop ON cop.offering_id = ep.offering_id
      WHERE ep.student_id = e.student_id
        AND cop.course_id = cp.prereq_course_id
        AND ep.status = 'completed'
        AND ep.final_score >= 60
  )
ORDER BY e.student_id, co.course_id
LIMIT 10;

\echo '9. Grade consistency violations'
SELECT 'completed_without_score' AS check_name, COUNT(*) AS violation_count
FROM enrollment
WHERE status = 'completed' AND final_score IS NULL;

SELECT 'selected_with_score' AS check_name, COUNT(*) AS violation_count
FROM enrollment
WHERE status = 'selected' AND final_score IS NOT NULL;

SELECT 'score_out_of_range' AS check_name, COUNT(*) AS violation_count
FROM enrollment
WHERE final_score IS NOT NULL AND (final_score < 0 OR final_score > 100);

\echo '10. Account/profile consistency violations'
SELECT 'student_role_mismatch' AS check_name, COUNT(*) AS violation_count
FROM student s
LEFT JOIN user_account u ON u.user_id = s.user_id
WHERE u.user_id IS NULL OR u.role <> 'student' OR u.username <> s.student_id;

SELECT 'teacher_role_mismatch' AS check_name, COUNT(*) AS violation_count
FROM teacher t
LEFT JOIN user_account u ON u.user_id = t.user_id
WHERE u.user_id IS NULL OR u.role <> 'teacher' OR u.username <> t.teacher_id;

SELECT 'admin_role_mismatch' AS check_name, COUNT(*) AS violation_count
FROM admin_profile a
LEFT JOIN user_account u ON u.user_id = a.user_id
WHERE u.user_id IS NULL OR u.role <> 'admin' OR u.username <> a.admin_id;

\echo '11. Prerequisite self-reference and cycle violations'
SELECT 'self_prerequisite' AS check_name, COUNT(*) AS violation_count
FROM course_prerequisite
WHERE course_id = prereq_course_id;

WITH RECURSIVE prereq_path(course_id, prereq_course_id, depth) AS (
    SELECT course_id, prereq_course_id, 1
    FROM course_prerequisite
    UNION ALL
    SELECT pp.course_id, cp.prereq_course_id, pp.depth + 1
    FROM prereq_path pp
    JOIN course_prerequisite cp ON cp.course_id = pp.prereq_course_id
    WHERE pp.depth < 20
)
SELECT 'prerequisite_cycle' AS check_name, COUNT(*) AS violation_count
FROM prereq_path
WHERE course_id = prereq_course_id;

\echo '12. Score audit log consistency violations'
SELECT 'invalid_log_enrollment' AS check_name, COUNT(*) AS violation_count
FROM score_change_log scl
LEFT JOIN enrollment e ON e.enrollment_id = scl.enrollment_id
WHERE e.enrollment_id IS NULL;

SELECT 'invalid_log_user' AS check_name, COUNT(*) AS violation_count
FROM score_change_log scl
LEFT JOIN user_account u ON u.user_id = scl.changed_by_user_id
WHERE u.user_id IS NULL;

\echo '13. GPA view smoke checks'
SELECT COUNT(*) AS enrollment_grade_detail_rows
FROM v_enrollment_grade_detail;

SELECT COUNT(*) AS student_gpa_summary_rows
FROM v_student_gpa_summary;
