DROP TABLE IF EXISTS score_change_log CASCADE;
DROP TABLE IF EXISTS enrollment CASCADE;
DROP TABLE IF EXISTS course_prerequisite CASCADE;
DROP TABLE IF EXISTS course_schedule CASCADE;
DROP TABLE IF EXISTS course_offering CASCADE;
DROP TABLE IF EXISTS classroom CASCADE;
DROP TABLE IF EXISTS course CASCADE;
DROP TABLE IF EXISTS semester CASCADE;
DROP TABLE IF EXISTS admin_profile CASCADE;
DROP TABLE IF EXISTS teacher CASCADE;
DROP TABLE IF EXISTS student CASCADE;
DROP TABLE IF EXISTS user_session CASCADE;
DROP TABLE IF EXISTS user_account CASCADE;
DROP TABLE IF EXISTS major CASCADE;
DROP TABLE IF EXISTS department CASCADE;

CREATE TABLE department (
    dept_id         VARCHAR(10)  NOT NULL,
    dept_name       VARCHAR(50)  NOT NULL,
    office_phone    VARCHAR(20),
    office_location VARCHAR(100),
    PRIMARY KEY (dept_id)
);

CREATE TABLE major (
    major_id   VARCHAR(10)  NOT NULL,
    major_name VARCHAR(50)  NOT NULL,
    dept_id    VARCHAR(10)  NOT NULL,
    PRIMARY KEY (major_id),
    CONSTRAINT fk_major_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id)
);

CREATE TABLE user_account (
    user_id       BIGSERIAL    NOT NULL,
    username      VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(64)  NOT NULL,
    role          VARCHAR(20)  NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'active',
    last_login_at TIMESTAMP,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_username UNIQUE (username),
    CONSTRAINT chk_user_role CHECK (role IN ('admin','student','teacher')),
    CONSTRAINT chk_user_status CHECK (status IN ('active','disabled'))
);

CREATE TABLE user_session (
    session_id   BIGSERIAL   NOT NULL,
    user_id      BIGINT      NOT NULL,
    token_hash   VARCHAR(64) NOT NULL,
    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP   NOT NULL,
    revoked_at   TIMESTAMP,
    last_seen_at TIMESTAMP,
    PRIMARY KEY (session_id),
    CONSTRAINT uq_user_session_token UNIQUE (token_hash),
    CONSTRAINT fk_user_session_user FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

CREATE INDEX idx_user_session_user ON user_session (user_id);
CREATE INDEX idx_user_session_valid ON user_session (token_hash, expires_at, revoked_at);

CREATE TABLE student (
    student_id   VARCHAR(20)  NOT NULL,
    user_id      BIGINT       NOT NULL,
    student_name VARCHAR(30)  NOT NULL,
    gender       VARCHAR(1),
    birth_date   DATE,
    enroll_year  SMALLINT,
    major_id     VARCHAR(10),
    class_name   VARCHAR(30),
    phone        VARCHAR(20),
    email        VARCHAR(100),
    status       VARCHAR(20)  NOT NULL DEFAULT 'enrolled',
    PRIMARY KEY (student_id),
    CONSTRAINT uq_student_user UNIQUE (user_id),
    CONSTRAINT fk_student_user  FOREIGN KEY (user_id)   REFERENCES user_account (user_id),
    CONSTRAINT fk_student_major FOREIGN KEY (major_id)  REFERENCES major (major_id),
    CONSTRAINT chk_student_gender CHECK (gender IS NULL OR gender IN ('M','F','O')),
    CONSTRAINT chk_student_status CHECK (status IN ('enrolled','suspended','graduated','dropped'))
);

CREATE TABLE teacher (
    teacher_id   VARCHAR(20)  NOT NULL,
    user_id      BIGINT       NOT NULL,
    teacher_name VARCHAR(30)  NOT NULL,
    gender       VARCHAR(1),
    dept_id      VARCHAR(10),
    title        VARCHAR(20),
    phone        VARCHAR(20),
    email        VARCHAR(100),
    status       VARCHAR(20)  NOT NULL DEFAULT 'active',
    PRIMARY KEY (teacher_id),
    CONSTRAINT uq_teacher_user UNIQUE (user_id),
    CONSTRAINT fk_teacher_user FOREIGN KEY (user_id)  REFERENCES user_account (user_id),
    CONSTRAINT fk_teacher_dept FOREIGN KEY (dept_id)  REFERENCES department (dept_id),
    CONSTRAINT chk_teacher_gender CHECK (gender IS NULL OR gender IN ('M','F','O')),
    CONSTRAINT chk_teacher_status CHECK (status IN ('active','retired','leave'))
);

CREATE TABLE admin_profile (
    admin_id   VARCHAR(20)  NOT NULL,
    user_id    BIGINT       NOT NULL,
    admin_name VARCHAR(30)  NOT NULL,
    phone      VARCHAR(20),
    PRIMARY KEY (admin_id),
    CONSTRAINT uq_admin_user UNIQUE (user_id),
    CONSTRAINT fk_admin_user FOREIGN KEY (user_id) REFERENCES user_account (user_id)
);

CREATE TABLE semester (
    semester_id     VARCHAR(20)  NOT NULL,
    semester_name   VARCHAR(30)  NOT NULL,
    start_date      DATE         NOT NULL,
    end_date        DATE         NOT NULL,
    selection_start TIMESTAMP,
    selection_end   TIMESTAMP,
    status          VARCHAR(20)  NOT NULL DEFAULT 'planned',
    PRIMARY KEY (semester_id),
    CONSTRAINT chk_semester_status CHECK (status IN ('planned','open','closed'))
);

CREATE TABLE course (
    course_id   VARCHAR(20)   NOT NULL,
    course_name VARCHAR(100)  NOT NULL,
    course_type VARCHAR(20)   NOT NULL DEFAULT 'required',
    credit      DECIMAL(3,1)  NOT NULL,
    total_hours INTEGER       NOT NULL,
    dept_id     VARCHAR(10),
    description TEXT,
    status      VARCHAR(20)   NOT NULL DEFAULT 'active',
    PRIMARY KEY (course_id),
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id),
    CONSTRAINT chk_course_type CHECK (course_type IN ('required','elective','public')),
    CONSTRAINT chk_course_status CHECK (status IN ('active','inactive')),
    CONSTRAINT chk_credit CHECK (credit > 0),
    CONSTRAINT chk_total_hours CHECK (total_hours > 0)
);

CREATE TABLE classroom (
    classroom_id VARCHAR(20)  NOT NULL,
    building     VARCHAR(50)  NOT NULL,
    room_no      VARCHAR(20)  NOT NULL,
    capacity     INTEGER      NOT NULL,
    PRIMARY KEY (classroom_id),
    CONSTRAINT chk_capacity CHECK (capacity > 0)
);

CREATE TABLE course_offering (
    offering_id    BIGSERIAL    NOT NULL,
    course_id      VARCHAR(20)  NOT NULL,
    semester_id    VARCHAR(20)  NOT NULL,
    teacher_id     VARCHAR(20)  NOT NULL,
    classroom_id   VARCHAR(20),
    max_capacity   INTEGER      NOT NULL DEFAULT 60,
    status         VARCHAR(20)  NOT NULL DEFAULT 'open',
    PRIMARY KEY (offering_id),
    CONSTRAINT fk_offering_course    FOREIGN KEY (course_id)    REFERENCES course (course_id),
    CONSTRAINT fk_offering_semester  FOREIGN KEY (semester_id)  REFERENCES semester (semester_id),
    CONSTRAINT fk_offering_teacher   FOREIGN KEY (teacher_id)   REFERENCES teacher (teacher_id),
    CONSTRAINT fk_offering_classroom FOREIGN KEY (classroom_id) REFERENCES classroom (classroom_id),
    CONSTRAINT chk_offering_status CHECK (status IN ('open','closed','cancelled')),
    CONSTRAINT chk_max_capacity CHECK (max_capacity > 0)
);

CREATE TABLE course_schedule (
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

CREATE TABLE course_prerequisite (
    course_id        VARCHAR(20) NOT NULL,
    prereq_course_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (course_id, prereq_course_id),
    CONSTRAINT fk_prereq_course FOREIGN KEY (course_id)        REFERENCES course (course_id),
    CONSTRAINT fk_prereq_pre    FOREIGN KEY (prereq_course_id) REFERENCES course (course_id)
);

CREATE TABLE enrollment (
    enrollment_id BIGSERIAL    NOT NULL,
    student_id    VARCHAR(20)  NOT NULL,
    offering_id   BIGINT       NOT NULL,
    select_time   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status        VARCHAR(20)  NOT NULL DEFAULT 'selected',
    final_score   DECIMAL(5,2),
    remark        VARCHAR(200),
    PRIMARY KEY (enrollment_id),
    CONSTRAINT uq_student_offering UNIQUE (student_id, offering_id),
    CONSTRAINT fk_enrollment_student  FOREIGN KEY (student_id)  REFERENCES student (student_id),
    CONSTRAINT fk_enrollment_offering FOREIGN KEY (offering_id) REFERENCES course_offering (offering_id),
    CONSTRAINT chk_enrollment_status CHECK (status IN ('selected','dropped','completed')),
    CONSTRAINT chk_final_score CHECK (final_score IS NULL OR (final_score >= 0 AND final_score <= 100))
);

CREATE TABLE score_change_log (
    log_id              BIGSERIAL    NOT NULL,
    enrollment_id       BIGINT       NOT NULL,
    old_score           DECIMAL(5,2),
    new_score           DECIMAL(5,2),
    changed_by_user_id  BIGINT       NOT NULL,
    changed_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason              VARCHAR(200),
    PRIMARY KEY (log_id),
    CONSTRAINT fk_log_enrollment FOREIGN KEY (enrollment_id)      REFERENCES enrollment (enrollment_id),
    CONSTRAINT fk_log_user       FOREIGN KEY (changed_by_user_id) REFERENCES user_account (user_id)
);

INSERT INTO department (dept_id, dept_name, office_phone, office_location) VALUES
('CS',  '计算机学院',   '010-88881111', '综合楼 A301'),
('MATH','数学学院',     '010-88882222', '综合楼 B201');

INSERT INTO major (major_id, major_name, dept_id) VALUES
('CS01', '计算机科学与技术', 'CS'),
('CS02', '软件工程',         'CS'),
('MA01', '数学与应用数学',   'MATH');

INSERT INTO user_account (username, password_hash, role) VALUES
('admin',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'admin'),
('t_zhang',  '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'teacher'),
('t_li',     '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'teacher'),
('t_wang',   '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'teacher'),
('t_sun',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'teacher'),
('s_001',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_002',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_003',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_004',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_005',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_006',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_007',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_008',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_009',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_010',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_011',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student'),
('s_012',    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'student');

INSERT INTO admin_profile (admin_id, user_id, admin_name, phone)
SELECT 'A001', user_id, '系统管理员', '010-88880000'
FROM user_account WHERE username = 'admin';

INSERT INTO teacher (teacher_id, user_id, teacher_name, gender, dept_id, title, email)
SELECT 'T001', user_id, '张明', 'M', 'CS', '副教授', 'zhangming@edu.cn'
FROM user_account WHERE username = 't_zhang';

INSERT INTO teacher (teacher_id, user_id, teacher_name, gender, dept_id, title, email)
SELECT 'T002', user_id, '李晓华', 'F', 'MATH', '讲师', 'lixiaohua@edu.cn'
FROM user_account WHERE username = 't_li';

INSERT INTO teacher (teacher_id, user_id, teacher_name, gender, dept_id, title, email)
SELECT 'T003', user_id, '王志强', 'M', 'CS', '讲师', 'wangzhiqiang@edu.cn'
FROM user_account WHERE username = 't_wang';

INSERT INTO teacher (teacher_id, user_id, teacher_name, gender, dept_id, title, email)
SELECT 'T004', user_id, '孙敏', 'F', 'MATH', '副教授', 'sunmin@edu.cn'
FROM user_account WHERE username = 't_sun';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240001', user_id, '王小明', 'M', 2024, 'CS01', '计科2401', 'wxm@stu.edu.cn'
FROM user_account WHERE username = 's_001';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240002', user_id, '陈雨欣', 'F', 2024, 'CS01', '计科2401', 'cyx@stu.edu.cn'
FROM user_account WHERE username = 's_002';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240003', user_id, '刘强', 'M', 2024, 'CS02', '软工2401', 'lq@stu.edu.cn'
FROM user_account WHERE username = 's_003';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240004', user_id, '赵雨桐', 'F', 2024, 'CS01', '计科2402', 'zyt@stu.edu.cn'
FROM user_account WHERE username = 's_004';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240005', user_id, '周子豪', 'M', 2024, 'CS01', '计科2402', 'zzh@stu.edu.cn'
FROM user_account WHERE username = 's_005';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240006', user_id, '林可欣', 'F', 2024, 'CS02', '软工2401', 'lkx@stu.edu.cn'
FROM user_account WHERE username = 's_006';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240007', user_id, '何俊杰', 'M', 2024, 'CS02', '软工2402', 'hjj@stu.edu.cn'
FROM user_account WHERE username = 's_007';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240008', user_id, '郭书瑶', 'F', 2024, 'CS02', '软工2402', 'gsy@stu.edu.cn'
FROM user_account WHERE username = 's_008';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240009', user_id, '许嘉宁', 'F', 2024, 'MA01', '数学2401', 'xjn@stu.edu.cn'
FROM user_account WHERE username = 's_009';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240010', user_id, '高远', 'M', 2024, 'MA01', '数学2401', 'gy@stu.edu.cn'
FROM user_account WHERE username = 's_010';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240011', user_id, '唐诗雨', 'F', 2024, 'MA01', '数学2402', 'tsy@stu.edu.cn'
FROM user_account WHERE username = 's_011';

INSERT INTO student (student_id, user_id, student_name, gender, enroll_year, major_id, class_name, email)
SELECT '20240012', user_id, '冯博文', 'M', 2024, 'MA01', '数学2402', 'fbw@stu.edu.cn'
FROM user_account WHERE username = 's_012';

INSERT INTO semester (semester_id, semester_name, start_date, end_date, selection_start, selection_end, status) VALUES
('2025-2026-1', '2025-2026学年第一学期',
 '2025-09-01', '2026-01-20',
 '2025-08-20 09:00:00', '2025-09-10 18:00:00',
 'closed'),
('2025-2026-2', '2025-2026学年第二学期',
 '2026-02-24', '2026-07-10',
 '2026-02-10 09:00:00', '2026-02-20 18:00:00',
 'open');

INSERT INTO course (course_id, course_name, course_type, credit, total_hours, dept_id, description) VALUES
('CS101', '程序设计基础',   'required', 3.0, 48, 'CS',   'C 语言基础程序设计'),
('CS201', '数据结构',       'required', 3.0, 48, 'CS',   '线性表、树、图及常用算法'),
('CS221', '操作系统',       'required', 3.5, 56, 'CS',   '进程管理、内存管理、文件系统与设备管理'),
('CS301', '数据库原理',     'required', 3.0, 48, 'CS',   '关系模型与 SQL，数据库设计'),
('CS402', 'Web 应用开发',   'elective', 2.5, 40, 'CS',   '前后端基础、数据库交互与应用部署'),
('MA101', '高等数学',       'required', 4.0, 64, 'MATH', '微积分与级数'),
('MA201', '线性代数',       'required', 3.0, 48, 'MATH', '矩阵、行列式与线性方程组'),
('MA301', '概率论与数理统计','required', 3.0, 48, 'MATH', '随机变量、常见分布与统计推断'),
('CS401', 'Python 程序设计','elective', 2.0, 32, 'CS',   'Python 基础与常用库');

INSERT INTO course_prerequisite (course_id, prereq_course_id) VALUES
('CS201', 'CS101'),
('CS221', 'CS201'),
('CS301', 'CS201'),
('CS402', 'CS301'),
('MA301', 'MA201');

INSERT INTO classroom (classroom_id, building, room_no, capacity) VALUES
('C101', '综合楼', '101', 60),
('C201', '综合楼', '201', 40),
('C301', '实验楼', '301', 30),
('M201', '数理楼', '201', 50),
('M301', '数理楼', '301', 40);

INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity) VALUES
('CS101', '2025-2026-2', 'T001', 'C101', 60),
('CS201', '2025-2026-2', 'T001', 'C201', 40),
('CS221', '2025-2026-2', 'T003', 'C201', 40),
('CS301', '2025-2026-2', 'T003', 'C301', 30),
('MA101', '2025-2026-2', 'T002', 'M201', 50),
('MA201', '2025-2026-2', 'T004', 'M301', 40),
('MA301', '2025-2026-2', 'T004', 'M301', 40),
('CS401', '2025-2026-2', 'T001', 'C301', 30),
('CS402', '2025-2026-2', 'T003', 'C301', 30);

INSERT INTO course_schedule (offering_id, weekday, start_section, end_section) VALUES
(1, 1, 1, 2),
(1, 3, 3, 4),
(2, 2, 3, 4),
(2, 4, 5, 6),
(3, 5, 1, 2),
(3, 5, 3, 4),
(4, 3, 1, 2),
(4, 4, 1, 2),
(5, 1, 5, 6),
(5, 5, 1, 2),
(6, 2, 1, 2),
(6, 4, 3, 4),
(7, 3, 5, 6),
(7, 5, 5, 6),
(8, 3, 7, 8),
(9, 2, 7, 8);

INSERT INTO enrollment (student_id, offering_id, status) VALUES
('20240001', 1, 'selected'),
('20240001', 5, 'selected'),
('20240002', 1, 'selected'),
('20240002', 8, 'selected'),
('20240003', 2, 'selected'),
('20240003', 3, 'selected'),
('20240004', 1, 'selected'),
('20240004', 5, 'selected'),
('20240005', 1, 'selected'),
('20240005', 8, 'selected'),
('20240006', 2, 'selected'),
('20240006', 3, 'selected'),
('20240007', 3, 'selected'),
('20240007', 8, 'selected'),
('20240008', 2, 'selected'),
('20240008', 9, 'selected'),
('20240009', 5, 'selected'),
('20240009', 6, 'selected'),
('20240010', 5, 'selected'),
('20240010', 7, 'selected'),
('20240011', 6, 'selected'),
('20240011', 7, 'selected'),
('20240012', 5, 'selected'),
('20240012', 9, 'selected');

INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, status) VALUES
('CS101', '2025-2026-1', 'T001', 'C101', 60, 'closed'),
('MA101', '2025-2026-1', 'T002', 'M201', 50, 'closed'),
('MA201', '2025-2026-1', 'T004', 'M301', 40, 'closed');

INSERT INTO course_schedule (offering_id, weekday, start_section, end_section) VALUES
(10, 1, 1, 2),
(11, 2, 3, 4),
(12, 4, 1, 2);

INSERT INTO enrollment (student_id, offering_id, status, final_score) VALUES
('20240001', 10, 'completed', 88.0),
('20240002', 10, 'completed', 92.0),
('20240003', 10, 'completed', 75.0),
('20240009', 11, 'completed', 91.0),
('20240010', 11, 'completed', 84.0),
('20240011', 11, 'completed', 78.0),
('20240009', 12, 'completed', 87.0),
('20240010', 12, 'completed', 82.0),
('20240012', 12, 'completed', 73.0);

CREATE INDEX idx_offering_course_semester ON course_offering (course_id, semester_id);
CREATE INDEX idx_offering_teacher_semester ON course_offering (teacher_id, semester_id);
CREATE INDEX idx_schedule_offering ON course_schedule (offering_id);
CREATE INDEX idx_schedule_time ON course_schedule (weekday, start_section, end_section);
CREATE INDEX idx_enrollment_student_status ON enrollment (student_id, status);
CREATE INDEX idx_enrollment_offering_status ON enrollment (offering_id, status);

-- Clean database initialization should be followed by
-- opengauss_setup/sql/migrate_triggers_constraints_20260608.sql.
-- opengauss_setup/docker/init_db.sh applies that migration automatically so
-- constraints, triggers, functions, and reporting views are present after setup.
