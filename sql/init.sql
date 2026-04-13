-- ============================================================
-- 选课管理系统 · MySQL 初始化脚本
-- 技术栈: Python + Streamlit + PyMySQL + Docker MySQL 8.x
-- 密码约定: 初始密码均为 123456
--           hash = SHA2('123456', 256)
-- ============================================================

-- 强制客户端以 utf8mb4 发送和接收，防止中文乱码
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection = utf8mb4;

CREATE DATABASE IF NOT EXISTS course_system
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE course_system;

-- ============================================================
-- 1. 院系表
-- ============================================================
CREATE TABLE IF NOT EXISTS department (
    dept_id         VARCHAR(10)  NOT NULL COMMENT '院系编号',
    dept_name       VARCHAR(50)  NOT NULL COMMENT '院系名称',
    office_phone    VARCHAR(20)           COMMENT '联系电话',
    office_location VARCHAR(100)          COMMENT '办公地点',
    PRIMARY KEY (dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='院系表';

-- ============================================================
-- 2. 专业表
-- ============================================================
CREATE TABLE IF NOT EXISTS major (
    major_id   VARCHAR(10)  NOT NULL COMMENT '专业编号',
    major_name VARCHAR(50)  NOT NULL COMMENT '专业名称',
    dept_id    VARCHAR(10)  NOT NULL COMMENT '所属院系',
    PRIMARY KEY (major_id),
    CONSTRAINT fk_major_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专业表';

-- ============================================================
-- 3. 统一账号表（学生/教师/管理员共用）
-- ============================================================
CREATE TABLE IF NOT EXISTS user_account (
    user_id       BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户编号',
    username      VARCHAR(50)  NOT NULL COMMENT '登录名',
    password_hash VARCHAR(64)  NOT NULL COMMENT '密码 SHA-256 密文',
    role          ENUM('admin','student','teacher') NOT NULL COMMENT '角色',
    status        ENUM('active','disabled') NOT NULL DEFAULT 'active' COMMENT '账号状态',
    last_login_at DATETIME              COMMENT '最近登录时间',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统一账号表';

-- ============================================================
-- 4. 学生表
-- ============================================================
CREATE TABLE IF NOT EXISTS student (
    student_id   VARCHAR(20)  NOT NULL COMMENT '学号',
    user_id      BIGINT       NOT NULL COMMENT '账号编号',
    student_name VARCHAR(30)  NOT NULL COMMENT '姓名',
    gender       ENUM('M','F','O') COMMENT '性别 M/F/O',
    birth_date   DATE                  COMMENT '出生日期',
    enroll_year  SMALLINT              COMMENT '入学年份',
    major_id     VARCHAR(10)           COMMENT '所属专业',
    class_name   VARCHAR(30)           COMMENT '班级',
    phone        VARCHAR(20)           COMMENT '联系电话',
    email        VARCHAR(100)          COMMENT '邮箱',
    status       ENUM('enrolled','suspended','graduated','dropped')
                              NOT NULL DEFAULT 'enrolled' COMMENT '学籍状态',
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_student_user (user_id),
    CONSTRAINT fk_student_user  FOREIGN KEY (user_id)   REFERENCES user_account (user_id),
    CONSTRAINT fk_student_major FOREIGN KEY (major_id)  REFERENCES major (major_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生表';

-- ============================================================
-- 5. 教师表
-- ============================================================
CREATE TABLE IF NOT EXISTS teacher (
    teacher_id   VARCHAR(20)  NOT NULL COMMENT '教师号',
    user_id      BIGINT       NOT NULL COMMENT '账号编号',
    teacher_name VARCHAR(30)  NOT NULL COMMENT '姓名',
    gender       ENUM('M','F','O') COMMENT '性别',
    dept_id      VARCHAR(10)           COMMENT '所属院系',
    title        VARCHAR(20)           COMMENT '职称',
    phone        VARCHAR(20)           COMMENT '联系电话',
    email        VARCHAR(100)          COMMENT '邮箱',
    status       ENUM('active','retired','leave') NOT NULL DEFAULT 'active' COMMENT '在职状态',
    PRIMARY KEY (teacher_id),
    UNIQUE KEY uq_teacher_user (user_id),
    CONSTRAINT fk_teacher_user FOREIGN KEY (user_id)  REFERENCES user_account (user_id),
    CONSTRAINT fk_teacher_dept FOREIGN KEY (dept_id)  REFERENCES department (dept_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师表';

-- ============================================================
-- 6. 管理员资料表
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_profile (
    admin_id   VARCHAR(20)  NOT NULL COMMENT '管理员编号',
    user_id    BIGINT       NOT NULL COMMENT '账号编号',
    admin_name VARCHAR(30)  NOT NULL COMMENT '管理员姓名',
    phone      VARCHAR(20)           COMMENT '联系电话',
    PRIMARY KEY (admin_id),
    UNIQUE KEY uq_admin_user (user_id),
    CONSTRAINT fk_admin_user FOREIGN KEY (user_id) REFERENCES user_account (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员资料表';

-- ============================================================
-- 7. 学期表
-- ============================================================
CREATE TABLE IF NOT EXISTS semester (
    semester_id   VARCHAR(20)  NOT NULL COMMENT '学期编号',
    semester_name VARCHAR(30)  NOT NULL COMMENT '学期名称，如 2025-2026-1',
    start_date    DATE         NOT NULL COMMENT '开始日期',
    end_date      DATE         NOT NULL COMMENT '结束日期',
    selection_start DATETIME           COMMENT '选课开始时间',
    selection_end   DATETIME           COMMENT '选课截止时间',
    status        ENUM('planned','open','closed') NOT NULL DEFAULT 'planned' COMMENT '状态',
    PRIMARY KEY (semester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学期表';

-- ============================================================
-- 8. 课程基础定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS course (
    course_id   VARCHAR(20)  NOT NULL COMMENT '课程号',
    course_name VARCHAR(100) NOT NULL COMMENT '课程名',
    course_type ENUM('required','elective','public') NOT NULL DEFAULT 'required' COMMENT '课程类型',
    credit      DECIMAL(3,1) NOT NULL COMMENT '学分',
    total_hours INT          NOT NULL COMMENT '总学时',
    dept_id     VARCHAR(10)           COMMENT '开课院系',
    description TEXT                  COMMENT '课程简介',
    status      ENUM('active','inactive') NOT NULL DEFAULT 'active' COMMENT '课程状态',
    PRIMARY KEY (course_id),
    CONSTRAINT fk_course_dept FOREIGN KEY (dept_id) REFERENCES department (dept_id),
    CONSTRAINT chk_credit      CHECK (credit > 0),
    CONSTRAINT chk_total_hours CHECK (total_hours > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程基础定义表';

-- ============================================================
-- 9. 教室表
-- ============================================================
CREATE TABLE IF NOT EXISTS classroom (
    classroom_id VARCHAR(20)  NOT NULL COMMENT '教室编号',
    building     VARCHAR(50)  NOT NULL COMMENT '教学楼',
    room_no      VARCHAR(20)  NOT NULL COMMENT '房间号',
    capacity     INT          NOT NULL COMMENT '容量',
    PRIMARY KEY (classroom_id),
    CONSTRAINT chk_capacity CHECK (capacity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教室表';

-- ============================================================
-- 10. 开课表（某学期某课程某教师的具体教学安排）
-- ============================================================
CREATE TABLE IF NOT EXISTS course_offering (
    offering_id    BIGINT       NOT NULL AUTO_INCREMENT COMMENT '开课编号',
    course_id      VARCHAR(20)  NOT NULL COMMENT '课程号',
    semester_id    VARCHAR(20)  NOT NULL COMMENT '学期编号',
    teacher_id     VARCHAR(20)  NOT NULL COMMENT '任课教师号',
    classroom_id   VARCHAR(20)           COMMENT '教室编号',
    max_capacity   INT          NOT NULL DEFAULT 60 COMMENT '最大容量',
    selected_count INT          NOT NULL DEFAULT 0  COMMENT '当前已选人数',
    schedule_text  VARCHAR(200)          COMMENT '上课时间说明，如 周一3-4节',
    status         ENUM('open','closed','cancelled') NOT NULL DEFAULT 'open' COMMENT '开课状态',
    PRIMARY KEY (offering_id),
    CONSTRAINT fk_offering_course    FOREIGN KEY (course_id)    REFERENCES course (course_id),
    CONSTRAINT fk_offering_semester  FOREIGN KEY (semester_id)  REFERENCES semester (semester_id),
    CONSTRAINT fk_offering_teacher   FOREIGN KEY (teacher_id)   REFERENCES teacher (teacher_id),
    CONSTRAINT fk_offering_classroom FOREIGN KEY (classroom_id) REFERENCES classroom (classroom_id),
    CONSTRAINT chk_max_capacity      CHECK (max_capacity > 0),
    CONSTRAINT chk_selected_count    CHECK (selected_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='开课表';

-- ============================================================
-- 11. 先修课程关系表
-- ============================================================
CREATE TABLE IF NOT EXISTS course_prerequisite (
    course_id       VARCHAR(20) NOT NULL COMMENT '课程号',
    prereq_course_id VARCHAR(20) NOT NULL COMMENT '先修课程号',
    PRIMARY KEY (course_id, prereq_course_id),
    CONSTRAINT fk_prereq_course  FOREIGN KEY (course_id)        REFERENCES course (course_id),
    CONSTRAINT fk_prereq_pre     FOREIGN KEY (prereq_course_id) REFERENCES course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='先修课程关系表';

-- ============================================================
-- 12. 选课表（学生 ↔ 开课班次，多对多）
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id BIGINT       NOT NULL AUTO_INCREMENT COMMENT '选课记录编号',
    student_id    VARCHAR(20)  NOT NULL COMMENT '学号',
    offering_id   BIGINT       NOT NULL COMMENT '开课编号',
    select_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
    status        ENUM('selected','dropped','completed') NOT NULL DEFAULT 'selected' COMMENT '选课状态',
    final_score   DECIMAL(5,2)          COMMENT '最终成绩',
    gpa_point     DECIMAL(3,2)          COMMENT '绩点',
    remark        VARCHAR(200)          COMMENT '备注',
    PRIMARY KEY (enrollment_id),
    UNIQUE KEY uq_student_offering (student_id, offering_id),
    CONSTRAINT fk_enrollment_student  FOREIGN KEY (student_id)  REFERENCES student (student_id),
    CONSTRAINT fk_enrollment_offering FOREIGN KEY (offering_id) REFERENCES course_offering (offering_id),
    CONSTRAINT chk_final_score CHECK (final_score IS NULL OR (final_score >= 0 AND final_score <= 100)),
    CONSTRAINT chk_gpa_point   CHECK (gpa_point   IS NULL OR (gpa_point   >= 0 AND gpa_point   <= 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='选课表';

-- ============================================================
-- 13. 成绩修改日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS score_change_log (
    log_id              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '日志编号',
    enrollment_id       BIGINT       NOT NULL COMMENT '选课记录编号',
    old_score           DECIMAL(5,2)          COMMENT '旧成绩',
    new_score           DECIMAL(5,2)          COMMENT '新成绩',
    changed_by_user_id  BIGINT       NOT NULL COMMENT '修改人账号编号',
    changed_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
    reason              VARCHAR(200)          COMMENT '修改原因',
    PRIMARY KEY (log_id),
    CONSTRAINT fk_log_enrollment FOREIGN KEY (enrollment_id)      REFERENCES enrollment (enrollment_id),
    CONSTRAINT fk_log_user       FOREIGN KEY (changed_by_user_id) REFERENCES user_account (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成绩修改日志表';

-- ============================================================
-- 自动维护 selected_count 的触发器
-- ============================================================
DELIMITER $$

-- 选课后 +1
CREATE TRIGGER trg_enrollment_insert
AFTER INSERT ON enrollment
FOR EACH ROW
BEGIN
    IF NEW.status = 'selected' THEN
        UPDATE course_offering
        SET selected_count = selected_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END$$

-- 退课后 -1
CREATE TRIGGER trg_enrollment_update
AFTER UPDATE ON enrollment
FOR EACH ROW
BEGIN
    IF OLD.status = 'selected' AND NEW.status = 'dropped' THEN
        UPDATE course_offering
        SET selected_count = GREATEST(selected_count - 1, 0)
        WHERE offering_id = NEW.offering_id;
    END IF;
    IF OLD.status = 'dropped' AND NEW.status = 'selected' THEN
        UPDATE course_offering
        SET selected_count = selected_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- 样本数据（测试用）
-- 所有初始密码均为 123456
-- SHA2('123456', 256) = 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
-- ============================================================

-- 院系
INSERT INTO department (dept_id, dept_name, office_phone, office_location) VALUES
('CS',  '计算机学院',   '010-88881111', '综合楼 A301'),
('MATH','数学学院',     '010-88882222', '综合楼 B201');

-- 专业
INSERT INTO major (major_id, major_name, dept_id) VALUES
('CS01', '计算机科学与技术', 'CS'),
('CS02', '软件工程',         'CS'),
('MA01', '数学与应用数学',   'MATH');

-- 账号（admin × 1, teacher × 4, student × 12）
INSERT INTO user_account (username, password_hash, role) VALUES
('admin',    SHA2('123456', 256), 'admin'),
('t_zhang',  SHA2('123456', 256), 'teacher'),
('t_li',     SHA2('123456', 256), 'teacher'),
('t_wang',   SHA2('123456', 256), 'teacher'),
('t_sun',    SHA2('123456', 256), 'teacher'),
('s_001',    SHA2('123456', 256), 'student'),
('s_002',    SHA2('123456', 256), 'student'),
('s_003',    SHA2('123456', 256), 'student'),
('s_004',    SHA2('123456', 256), 'student'),
('s_005',    SHA2('123456', 256), 'student'),
('s_006',    SHA2('123456', 256), 'student'),
('s_007',    SHA2('123456', 256), 'student'),
('s_008',    SHA2('123456', 256), 'student'),
('s_009',    SHA2('123456', 256), 'student'),
('s_010',    SHA2('123456', 256), 'student'),
('s_011',    SHA2('123456', 256), 'student'),
('s_012',    SHA2('123456', 256), 'student');

-- 管理员资料
INSERT INTO admin_profile (admin_id, user_id, admin_name, phone)
SELECT 'A001', user_id, '系统管理员', '010-88880000'
FROM user_account WHERE username = 'admin';

-- 教师
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

-- 学生
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

-- 学期
INSERT INTO semester (semester_id, semester_name, start_date, end_date, selection_start, selection_end, status) VALUES
('2025-2026-1', '2025-2026学年第一学期',
 '2025-09-01', '2026-01-20',
 '2025-08-20 09:00:00', '2025-09-10 18:00:00',
 'closed'),
('2025-2026-2', '2025-2026学年第二学期',
 '2026-02-24', '2026-07-10',
 '2026-02-10 09:00:00', '2026-02-20 18:00:00',
 'open');

-- 课程
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

-- 先修关系
INSERT INTO course_prerequisite (course_id, prereq_course_id) VALUES
('CS201', 'CS101'),
('CS221', 'CS201'),
('CS301', 'CS201'),
('CS402', 'CS301'),
('MA301', 'MA201');

-- 教室
INSERT INTO classroom (classroom_id, building, room_no, capacity) VALUES
('C101', '综合楼', '101', 60),
('C201', '综合楼', '201', 40),
('C301', '实验楼', '301', 30),
('M201', '数理楼', '201', 50),
('M301', '数理楼', '301', 40);

-- 开课（当前学期）
INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, schedule_text) VALUES
('CS101', '2025-2026-2', 'T001', 'C101', 60, '周一 1-2 节 / 周三 3-4 节'),
('CS201', '2025-2026-2', 'T001', 'C201', 40, '周二 3-4 节 / 周四 5-6 节'),
('CS221', '2025-2026-2', 'T003', 'C201', 40, '周五 1-2 节 / 周五 3-4 节'),
('CS301', '2025-2026-2', 'T003', 'C301', 30, '周三 1-2 节 / 周四 1-2 节'),
('MA101', '2025-2026-2', 'T002', 'M201', 60, '周一 5-6 节 / 周五 1-2 节'),
('MA201', '2025-2026-2', 'T004', 'M301', 40, '周二 1-2 节 / 周四 3-4 节'),
('MA301', '2025-2026-2', 'T004', 'M301', 40, '周三 5-6 节 / 周五 5-6 节'),
('CS401', '2025-2026-2', 'T001', 'C301', 30, '周三 7-8 节'),
('CS402', '2025-2026-2', 'T003', 'C301', 30, '周二 7-8 节');

-- 选课记录（部分学生已选）
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

-- 补充：上学期已结课成绩（用于成绩单演示）
INSERT INTO course_offering (course_id, semester_id, teacher_id, classroom_id, max_capacity, schedule_text, status) VALUES
('CS101', '2025-2026-1', 'T001', 'C101', 60, '周一 1-2 节', 'closed'),
('MA101', '2025-2026-1', 'T002', 'M201', 60, '周二 3-4 节', 'closed'),
('MA201', '2025-2026-1', 'T004', 'M301', 40, '周四 1-2 节', 'closed');

INSERT INTO enrollment (student_id, offering_id, status, final_score, gpa_point) VALUES
('20240001', 10, 'completed', 88.0, 3.5),
('20240002', 10, 'completed', 92.0, 4.0),
('20240003', 10, 'completed', 75.0, 3.0),
('20240009', 11, 'completed', 91.0, 4.0),
('20240010', 11, 'completed', 84.0, 3.3),
('20240011', 11, 'completed', 78.0, 3.0),
('20240009', 12, 'completed', 87.0, 3.7),
('20240010', 12, 'completed', 82.0, 3.3),
('20240012', 12, 'completed', 73.0, 2.3);
