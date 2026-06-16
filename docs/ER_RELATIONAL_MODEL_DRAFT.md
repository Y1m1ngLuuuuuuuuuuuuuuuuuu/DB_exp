# ER 模型、关系模型与 Mermaid 草案

本文档用于期末报告“概念结构设计”和“逻辑结构设计”章节。当前项目没有单独的 ER 图文件，因此这里根据 `opengauss_setup/sql/init.sql` 反向抽取实体、属性、联系和关系模式。

> 2026-06-08 更新：当前模式已新增 `course_schedule` 表，用于表达开课班次的结构化上课时间；`course_offering.selected_count`、`course_offering.schedule_text` 和 `enrollment.gpa_point` 已从基础表中删除，展示值改为查询时聚合或计算。正式绘制 ER 图时应以这一版本为准。

## 1. 概念设计概述

本选课系统的核心概念结构包括四类对象：

1. 组织结构：院系、专业、教室。
2. 用户身份：统一账号、学生、教师、管理员。
3. 教学安排：学期、课程、开课班次、先修课程。
4. 选课成绩：选课记录、成绩修改日志。

其中最关键的概念设计是：

- 将“课程”与“开课班次”分离。
- 将“学生选择课程”建模为“学生选择某个开课班次”。
- 将学生与开课班次之间的 M:N 联系转换为 `enrollment`，并把联系属性放入该表。
- 将课程与课程之间的先修自关联转换为 `course_prerequisite`。

## 2. 实体及主要属性

### 2.1 院系 Department

实体说明：

- 表：`department`。
- 主键：`dept_id`。
- 属性：`dept_name`、`office_phone`、`office_location`。

报告表述：

> 院系是学校组织结构的上层实体，专业、教师和课程都可以归属到某个院系。

### 2.2 专业 Major

实体说明：

- 表：`major`。
- 主键：`major_id`。
- 外键：`dept_id`。
- 属性：`major_name`。

联系：

- 院系 1:N 专业。

### 2.3 用户账号 UserAccount

实体说明：

- 表：`user_account`。
- 主键：`user_id`。
- 候选键：`username`。
- 属性：`password_hash`、`role`、`status`、`last_login_at`、`created_at`。

联系：

- 用户账号与学生资料 1:1。
- 用户账号与教师资料 1:1。
- 用户账号与管理员资料 1:1。
- 用户账号与登录会话 1:N。

### 2.4 登录会话 UserSession

实体说明：

- 表：`user_session`。
- 主键：`session_id`。
- 候选键：`token_hash`。
- 外键：`user_id`。
- 属性：`created_at`、`expires_at`、`revoked_at`、`last_seen_at`。

联系：

- 一个用户账号可拥有多个会话。
- 删除用户账号时，会话级联删除。

### 2.5 学生 Student

实体说明：

- 表：`student`。
- 主键：`student_id`。
- 候选键：`user_id`。
- 外键：`major_id`、`user_id`。
- 属性：`student_name`、`gender`、`birth_date`、`enroll_year`、`class_name`、`phone`、`email`、`status`。

联系：

- 专业 1:N 学生。
- 用户账号 1:1 学生。
- 学生 M:N 开课班次，通过 `enrollment` 转换。

### 2.6 教师 Teacher

实体说明：

- 表：`teacher`。
- 主键：`teacher_id`。
- 候选键：`user_id`。
- 外键：`dept_id`、`user_id`。
- 属性：`teacher_name`、`gender`、`title`、`phone`、`email`、`status`。

联系：

- 院系 1:N 教师。
- 用户账号 1:1 教师。
- 教师 1:N 开课班次。

### 2.7 管理员 AdminProfile

实体说明：

- 表：`admin_profile`。
- 主键：`admin_id`。
- 候选键：`user_id`。
- 属性：`admin_name`、`phone`。

联系：

- 用户账号 1:1 管理员资料。

### 2.8 学期 Semester

实体说明：

- 表：`semester`。
- 主键：`semester_id`。
- 属性：`semester_name`、`start_date`、`end_date`、`selection_start`、`selection_end`、`status`。

联系：

- 学期 1:N 开课班次。

### 2.9 课程 Course

实体说明：

- 表：`course`。
- 主键：`course_id`。
- 外键：`dept_id`。
- 属性：`course_name`、`course_type`、`credit`、`total_hours`、`description`、`status`。

联系：

- 院系 1:N 课程。
- 课程 1:N 开课班次。
- 课程 M:N 课程，通过 `course_prerequisite` 表示先修关系。

### 2.10 教室 Classroom

实体说明：

- 表：`classroom`。
- 主键：`classroom_id`。
- 属性：`building`、`room_no`、`capacity`。

联系：

- 教室 1:N 开课班次。

### 2.11 开课班次 CourseOffering

实体说明：

- 表：`course_offering`。
- 主键：`offering_id`。
- 外键：`course_id`、`semester_id`、`teacher_id`、`classroom_id`。
- 属性：`max_capacity`、`selected_count`、`schedule_text`、`status`。

概念意义：

- 表示“某课程在某学期由某教师在某教室开设的具体教学班”。
- 是连接课程、学期、教师、教室和选课记录的中心实体。

### 2.12 选课记录 Enrollment

实体/联系说明：

- 表：`enrollment`。
- 主键：`enrollment_id`。
- 候选键：`(student_id, offering_id)`。
- 外键：`student_id`、`offering_id`。
- 属性：`select_time`、`status`、`final_score`、`gpa_point`、`remark`。

概念意义：

- 这是学生与开课班次 M:N 联系转换后的关系。
- 它不仅表示“选了某班次”，还保存该联系的状态和成绩。

### 2.13 先修关系 CoursePrerequisite

实体/联系说明：

- 表：`course_prerequisite`。
- 主键：`(course_id, prereq_course_id)`。
- 外键：两列均引用 `course(course_id)`。

概念意义：

- 表示课程对课程的自关联。
- 例如 `CS301` 需要先通过 `CS201`。

### 2.14 成绩修改日志 ScoreChangeLog

实体说明：

- 表：`score_change_log`。
- 主键：`log_id`。
- 外键：`enrollment_id`、`changed_by_user_id`。
- 属性：`old_score`、`new_score`、`changed_at`、`reason`。

联系：

- 选课记录 1:N 成绩修改日志。
- 用户账号 1:N 成绩修改日志。

## 3. 联系和基数

| 联系 | 基数 | 实现方式 |
|---|---|---|
| 院系-专业 | 1:N | `major.dept_id` 外键。 |
| 专业-学生 | 1:N | `student.major_id` 外键。 |
| 院系-教师 | 1:N | `teacher.dept_id` 外键。 |
| 院系-课程 | 1:N | `course.dept_id` 外键。 |
| 用户账号-学生 | 1:1 | `student.user_id UNIQUE`。 |
| 用户账号-教师 | 1:1 | `teacher.user_id UNIQUE`。 |
| 用户账号-管理员 | 1:1 | `admin_profile.user_id UNIQUE`。 |
| 用户账号-会话 | 1:N | `user_session.user_id` 外键。 |
| 课程-开课班次 | 1:N | `course_offering.course_id` 外键。 |
| 学期-开课班次 | 1:N | `course_offering.semester_id` 外键。 |
| 教师-开课班次 | 1:N | `course_offering.teacher_id` 外键。 |
| 教室-开课班次 | 1:N | `course_offering.classroom_id` 外键。 |
| 学生-开课班次 | M:N | 中间表 `enrollment`。 |
| 课程-先修课程 | M:N 自关联 | 中间表 `course_prerequisite`。 |
| 选课记录-成绩日志 | 1:N | `score_change_log.enrollment_id` 外键。 |
| 用户账号-成绩日志 | 1:N | `score_change_log.changed_by_user_id` 外键。 |

## 4. 主要关系模式

### 4.1 组织结构

`Department(dept_id PK, dept_name, office_phone, office_location)`

`Major(major_id PK, major_name, dept_id FK -> Department.dept_id)`

`Classroom(classroom_id PK, building, room_no, capacity)`

### 4.2 用户与角色

`UserAccount(user_id PK, username UNIQUE, password_hash, role, status, last_login_at, created_at)`

`UserSession(session_id PK, user_id FK -> UserAccount.user_id, token_hash UNIQUE, created_at, expires_at, revoked_at, last_seen_at)`

`Student(student_id PK, user_id UNIQUE FK -> UserAccount.user_id, student_name, gender, birth_date, enroll_year, major_id FK -> Major.major_id, class_name, phone, email, status)`

`Teacher(teacher_id PK, user_id UNIQUE FK -> UserAccount.user_id, teacher_name, gender, dept_id FK -> Department.dept_id, title, phone, email, status)`

`AdminProfile(admin_id PK, user_id UNIQUE FK -> UserAccount.user_id, admin_name, phone)`

### 4.3 教学安排

`Semester(semester_id PK, semester_name, start_date, end_date, selection_start, selection_end, status)`

`Course(course_id PK, course_name, course_type, credit, total_hours, dept_id FK -> Department.dept_id, description, status)`

`CourseOffering(offering_id PK, course_id FK -> Course.course_id, semester_id FK -> Semester.semester_id, teacher_id FK -> Teacher.teacher_id, classroom_id FK -> Classroom.classroom_id, max_capacity, selected_count, schedule_text, status)`

`CoursePrerequisite(course_id PK/FK -> Course.course_id, prereq_course_id PK/FK -> Course.course_id)`

### 4.4 选课成绩

`Enrollment(enrollment_id PK, student_id FK -> Student.student_id, offering_id FK -> CourseOffering.offering_id, select_time, status, final_score, gpa_point, remark, UNIQUE(student_id, offering_id))`

`ScoreChangeLog(log_id PK, enrollment_id FK -> Enrollment.enrollment_id, old_score, new_score, changed_by_user_id FK -> UserAccount.user_id, changed_at, reason)`

## 5. Mermaid ER 图草案

```mermaid
erDiagram
    DEPARTMENT ||--o{ MAJOR : "has"
    DEPARTMENT ||--o{ TEACHER : "employs"
    DEPARTMENT ||--o{ COURSE : "offers"

    USER_ACCOUNT ||--o{ USER_SESSION : "owns"
    USER_ACCOUNT ||--o| STUDENT : "student_profile"
    USER_ACCOUNT ||--o| TEACHER : "teacher_profile"
    USER_ACCOUNT ||--o| ADMIN_PROFILE : "admin_profile"

    MAJOR ||--o{ STUDENT : "contains"
    COURSE ||--o{ COURSE_OFFERING : "is_opened_as"
    SEMESTER ||--o{ COURSE_OFFERING : "contains"
    TEACHER ||--o{ COURSE_OFFERING : "teaches"
    CLASSROOM ||--o{ COURSE_OFFERING : "hosts"

    STUDENT ||--o{ ENROLLMENT : "selects"
    COURSE_OFFERING ||--o{ ENROLLMENT : "has"

    COURSE ||--o{ COURSE_PREREQUISITE : "target_course"
    COURSE ||--o{ COURSE_PREREQUISITE : "prerequisite_course"

    ENROLLMENT ||--o{ SCORE_CHANGE_LOG : "score_changes"
    USER_ACCOUNT ||--o{ SCORE_CHANGE_LOG : "changes_score"

    DEPARTMENT {
        string dept_id PK
        string dept_name
        string office_phone
        string office_location
    }

    MAJOR {
        string major_id PK
        string major_name
        string dept_id FK
    }

    USER_ACCOUNT {
        bigint user_id PK
        string username UK
        string password_hash
        string role
        string status
        timestamp last_login_at
        timestamp created_at
    }

    USER_SESSION {
        bigint session_id PK
        bigint user_id FK
        string token_hash UK
        timestamp created_at
        timestamp expires_at
        timestamp revoked_at
        timestamp last_seen_at
    }

    STUDENT {
        string student_id PK
        bigint user_id FK_UK
        string student_name
        string gender
        date birth_date
        smallint enroll_year
        string major_id FK
        string class_name
        string phone
        string email
        string status
    }

    TEACHER {
        string teacher_id PK
        bigint user_id FK_UK
        string teacher_name
        string gender
        string dept_id FK
        string title
        string phone
        string email
        string status
    }

    ADMIN_PROFILE {
        string admin_id PK
        bigint user_id FK_UK
        string admin_name
        string phone
    }

    SEMESTER {
        string semester_id PK
        string semester_name
        date start_date
        date end_date
        timestamp selection_start
        timestamp selection_end
        string status
    }

    COURSE {
        string course_id PK
        string course_name
        string course_type
        decimal credit
        int total_hours
        string dept_id FK
        text description
        string status
    }

    CLASSROOM {
        string classroom_id PK
        string building
        string room_no
        int capacity
    }

    COURSE_OFFERING {
        bigint offering_id PK
        string course_id FK
        string semester_id FK
        string teacher_id FK
        string classroom_id FK
        int max_capacity
        int selected_count
        string schedule_text
        string status
    }

    COURSE_PREREQUISITE {
        string course_id PK_FK
        string prereq_course_id PK_FK
    }

    ENROLLMENT {
        bigint enrollment_id PK
        string student_id FK
        bigint offering_id FK
        timestamp select_time
        string status
        decimal final_score
        decimal gpa_point
        string remark
    }

    SCORE_CHANGE_LOG {
        bigint log_id PK
        bigint enrollment_id FK
        decimal old_score
        decimal new_score
        bigint changed_by_user_id FK
        timestamp changed_at
        string reason
    }
```

## 6. 关系模型设计评价

### 6.1 课程和开课班次分离的价值

如果不分离 `course` 和 `course_offering`，可能出现以下问题：

- 同一课程每学期、每个教师开设时重复保存课程名、学分、学时，产生更新异常。
- 修改课程学分时需要修改多条教学班记录。
- 无法清晰表示“课程定义”和“本学期教学安排”的不同生命周期。
- 成绩和选课记录难以区分学生选的是课程本身还是具体教学班。

当前设计通过 `course_id` 连接 `course` 和 `course_offering`：

- `course` 保存稳定课程属性。
- `course_offering` 保存学期、教师、教室、容量、时间、状态。
- `enrollment` 指向具体 `offering_id`，保证成绩和选课记录落到具体教学班。

这是报告中最值得重点展示的逻辑设计成果。

### 6.2 多对多关系转换

学生与开课班次：

- ER 中为 M:N。
- 转换为 `Enrollment(student_id, offering_id, ...)`。
- `UNIQUE(student_id, offering_id)` 防止重复同一教学班。
- 联系属性包括 `select_time/status/final_score/gpa_point`。

课程与先修课程：

- ER 中是课程实体自身的 M:N 联系。
- 转换为 `CoursePrerequisite(course_id, prereq_course_id)`。
- 复合主键防止重复先修关系。

### 6.3 参照完整性

外键使系统保持数据相容性：

- 不存在没有院系的专业。
- 不存在没有课程、学期、教师的开课班次。
- 不存在没有学生或教学班的选课记录。
- 不存在没有选课记录的成绩修改日志。

### 6.4 可扩展点

可作为报告“后续完善”的关系模型扩展：

1. `CourseSchedule(schedule_id, offering_id, weekday, start_section, end_section)`：结构化上课时间。
2. `Class(class_id, class_name, major_id, enroll_year, advisor_teacher_id)`：行政班管理。
3. `EnrollmentAudit(audit_id, enrollment_id, action, old_status, new_status, operator_id, changed_at)`：选课退课审计。
4. `GradeRule(rule_id, min_score, max_score, gpa_point, effective_from, effective_to)`：绩点规则版本化。
5. `DbRolePermission(role, resource, action)`：更细粒度权限设计。
