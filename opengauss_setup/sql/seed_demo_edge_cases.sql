-- Demo edge cases for frontend and trigger testing.
-- This script is idempotent and does not disable triggers.

START TRANSACTION;

-- Remove previous edge-case fixture rows in dependency order.
DELETE FROM enrollment e
USING course_offering co
WHERE e.offering_id = co.offering_id
  AND co.course_id LIKE 'EDGE_%';

DELETE FROM course_prerequisite
WHERE course_id LIKE 'EDGE_%'
   OR prereq_course_id LIKE 'EDGE_%';

DELETE FROM course_schedule cs
USING course_offering co
WHERE cs.offering_id = co.offering_id
  AND co.course_id LIKE 'EDGE_%';

DELETE FROM course_offering
WHERE course_id LIKE 'EDGE_%';

DELETE FROM course
WHERE course_id LIKE 'EDGE_%';

DELETE FROM classroom
WHERE classroom_id LIKE 'EDGE_%';

-- Dedicated small classrooms keep capacities easy to inspect.
INSERT INTO classroom (classroom_id, building, room_no, capacity) VALUES
('EDGE_R101', '演示楼', 'R101', 8),
('EDGE_R102', '演示楼', 'R102', 6),
('EDGE_R103', '演示楼', 'R103', 20),
('EDGE_R104', '演示楼', 'R104', 20),
('EDGE_R105', '演示楼', 'R105', 20),
('EDGE_R106', '演示楼', 'R106', 20);

INSERT INTO course (
    course_id, course_name, course_type, credit, total_hours, dept_id, description, status
) VALUES
('EDGE_FULL',       '演示：已满课程',       'public',   1.0, 16, 'CS', '用于测试容量已满提示。', 'active'),
('EDGE_ONE_LEFT',   '演示：仅剩一名课程',   'public',   1.0, 16, 'CS', '用于测试剩余名额展示。', 'active'),
('EDGE_CONFLICT_A', '演示：时间冲突已选课', 'elective', 1.0, 16, 'CS', '学生 20240009 已选该课程。', 'active'),
('EDGE_CONFLICT_B', '演示：时间冲突待选课', 'elective', 1.0, 16, 'CS', '与 EDGE_CONFLICT_A 时间重叠。', 'active'),
('EDGE_SAME',       '演示：同课跨班限制',   'elective', 1.0, 16, 'CS', '同一学生同学期只能选择一个教学班。', 'active'),
('EDGE_PRE',        '演示：先修基础课',     'required', 1.0, 16, 'CS', 'EDGE_ADV 的先修课程。', 'active'),
('EDGE_ADV',        '演示：先修未满足课程', 'elective', 1.0, 16, 'CS', '用于测试先修课程未满足提示。', 'active');

INSERT INTO course_offering (
    offering_id, course_id, semester_id, teacher_id, classroom_id, max_capacity, status
) VALUES
(9001, 'EDGE_FULL',       '2025-2026-2', 'T001', 'EDGE_R101', 8,  'open'),
(9002, 'EDGE_ONE_LEFT',   '2025-2026-2', 'T001', 'EDGE_R102', 6,  'open'),
(9003, 'EDGE_CONFLICT_A', '2025-2026-2', 'T002', 'EDGE_R103', 20, 'open'),
(9004, 'EDGE_CONFLICT_B', '2025-2026-2', 'T002', 'EDGE_R104', 20, 'open'),
(9005, 'EDGE_SAME',       '2025-2026-2', 'T003', 'EDGE_R105', 20, 'open'),
(9006, 'EDGE_SAME',       '2025-2026-2', 'T004', 'EDGE_R106', 20, 'open'),
(9007, 'EDGE_ADV',        '2025-2026-2', 'T005', 'EDGE_R103', 20, 'open');

-- Weekend slots avoid accidental conflicts with the generated main dataset.
INSERT INTO course_schedule (offering_id, weekday, start_section, end_section) VALUES
(9001, 6, 11, 12),
(9002, 7, 1, 2),
(9003, 6, 1, 2),
(9004, 6, 1, 2),
(9005, 6, 3, 4),
(9006, 7, 5, 6),
(9007, 6, 7, 8);

INSERT INTO course_prerequisite (course_id, prereq_course_id)
VALUES ('EDGE_ADV', 'EDGE_PRE');

-- EDGE_FULL: selected_count = max_capacity = 8.
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240001', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240002', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240003', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240004', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240005', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240006', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240007', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240008', 9001, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：已满课程');

-- EDGE_ONE_LEFT: selected_count = 5, max_capacity = 6.
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240001', 9002, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：仅剩一名');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240002', 9002, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：仅剩一名');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240003', 9002, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：仅剩一名');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240004', 9002, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：仅剩一名');
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240005', 9002, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：仅剩一名');

-- 20240009 already has EDGE_CONFLICT_A. Selecting 9004 should fail with timetable conflict.
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240009', 9003, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：时间冲突基准课');

-- 20240010 already has one offering for EDGE_SAME. Selecting 9006 should fail with same-course limit.
INSERT INTO enrollment (student_id, offering_id, select_time, status, final_score, remark)
VALUES ('20240010', 9005, '2026-06-11 10:00:00', 'selected', NULL, '边界测试：同课跨班基准课');

SELECT setval(
    'course_offering_offering_id_seq',
    GREATEST((SELECT MAX(offering_id) FROM course_offering), 1),
    true
);

COMMIT;

\echo 'Demo edge cases inserted.'
\echo 'Check with: SELECT course_id, course_name, offering_id, selected_count, max_capacity, remaining_capacity FROM v_course_offering_detail WHERE course_id LIKE ''EDGE_%'' ORDER BY course_id, offering_id;'
