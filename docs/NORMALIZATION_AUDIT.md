# 规范化与函数依赖分析

本文档用于期末报告“规范化设计与范式分析”章节。分析依据为 `opengauss_setup/sql/init.sql` 的当前表结构，以及 `services/*.py` 中体现的业务语义。范式判断尽量依据当前可见约束；如果需要额外业务语义才能确认，则标注“不确定”。

## 0. 2026-06-08 3NF 重构后结论

当前项目已经针对原先最明显的反范式点完成结构调整：

- 已新增 `course_schedule(schedule_id, offering_id, weekday, start_section, end_section)`，将原先 `course_offering.schedule_text` 中的多个上课时间片拆分为原子字段。课程列表和页面展示所需的 `schedule_text` 改为查询时由 `course_schedule` 聚合生成。
- 已从 `course_offering` 删除 `selected_count`。当前已选人数由 `enrollment` 中 `status='selected'` 的记录聚合计算，不再保存跨表派生计数字段。
- 已从 `enrollment` 删除 `gpa_point`。成绩单和页面展示所需的绩点由 `final_score` 按固定换算规则查询时计算，不再保存 `final_score -> gpa_point` 的派生字段。
- `selection_service.py` 已基于 `course_schedule` 增加学生选课时间冲突检查，结构化时间片开始承担业务校验作用。

因此，在当前基础表结构下，`course_offering`、`course_schedule`、`enrollment` 已消除原报告中列出的主要 1NF/3NF 风险。仍需结合业务语义确认的点主要包括：`student.class_name` 是否应拆成行政班表、`classroom(building, room_no)` 是否应设置唯一约束，以及绩点规则未来是否需要独立的规则版本表。

## 1. 总体判断

当前数据库模式总体上经过了较好的实体拆分：

- 课程定义 `course` 与具体开课班次 `course_offering` 分离，避免课程名称、学分、学时等信息在每个教学班重复。
- 学生 `student`、教师 `teacher`、管理员资料 `admin_profile` 与统一账号 `user_account` 分离，支持统一登录和角色控制。
- 学生与开课班次的多对多关系通过 `enrollment` 表转换，并把联系自身属性 `select_time/status/final_score/gpa_point` 放在联系表中。
- 课程之间的先修自关联通过 `course_prerequisite` 表转换。
- 成绩修改历史独立为 `score_change_log`，避免覆盖历史状态。

需要重点讨论的问题：

- `course_offering.schedule_text` 以文本保存多个时间片，不利于 1NF 和时间冲突检查。
- `course_offering.selected_count` 是从 `enrollment` 派生的冗余计数字段，依赖触发器维护。
- `enrollment.gpa_point` 可由 `final_score` 和绩点规则计算得到，是派生字段。
- `student.class_name` 目前是文本字段，若班级具有独立属性，应拆出行政班实体。
- `classroom` 的 `(building, room_no)` 在现实中可能唯一确定教室，但当前未设唯一约束，需要结合业务语义确认 BCNF。

## 2. 逐表范式分析

### 2.1 department

关系模式：

`Department(dept_id, dept_name, office_phone, office_location)`

约束：

- 主键：`dept_id`。

可能函数依赖：

- `dept_id -> dept_name, office_phone, office_location`。
- 如果业务规定院系名称唯一，则可能有 `dept_name -> dept_id, office_phone, office_location`，但当前未设置 `UNIQUE(dept_name)`。

范式判断：

- 1NF：满足。字段为原子值。
- 2NF：满足。单属性主键，不存在部分依赖。
- 3NF：满足。未发现非主属性之间的传递依赖。
- BCNF：在只承认 `dept_id` 为候选键时满足；如果 `dept_name` 也应唯一，建议加唯一约束以强化 BCNF。

改进建议：

- 可选增加 `UNIQUE(dept_name)`。

### 2.2 major

关系模式：

`Major(major_id, major_name, dept_id)`

约束：

- 主键：`major_id`。
- 外键：`dept_id -> department(dept_id)`。

可能函数依赖：

- `major_id -> major_name, dept_id`。
- 如果专业名称全校唯一，可能有 `major_name -> major_id, dept_id`，当前未显式约束。

范式判断：

- 1NF：满足。
- 2NF：满足。单属性主键。
- 3NF：满足。`dept_id` 是外键，不代表把院系名称冗余进本表。
- BCNF：在只承认 `major_id` 为候选键时满足；若 `major_name` 也唯一，需要加唯一约束。

改进建议：

- 如报告需要体现“数据字典”，可说明 `major_id` 是专业的稳定业务标识。

### 2.3 user_account

关系模式：

`UserAccount(user_id, username, password_hash, role, status, last_login_at, created_at)`

约束：

- 主键：`user_id`。
- 唯一约束：`username`。
- CHECK：`role IN ('admin','student','teacher')`，`status IN ('active','disabled')`。

可能函数依赖：

- `user_id -> username, password_hash, role, status, last_login_at, created_at`。
- `username -> user_id, password_hash, role, status, last_login_at, created_at`。

范式判断：

- 1NF：满足。
- 2NF：满足。候选键为单属性。
- 3NF：满足。非主属性依赖候选键，没有明显传递依赖。
- BCNF：满足。`user_id` 和 `username` 都是候选键，决定因素均为候选键。

设计价值：

- 账号表与学生/教师/管理员资料表分离，避免登录信息在多个角色表中重复。

### 2.4 user_session

关系模式：

`UserSession(session_id, user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at)`

约束：

- 主键：`session_id`。
- 唯一约束：`token_hash`。
- 外键：`user_id -> user_account(user_id)`，并设置 `ON DELETE CASCADE`。
- 显式索引：`idx_user_session_user`，`idx_user_session_valid`。

可能函数依赖：

- `session_id -> user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at`。
- `token_hash -> session_id, user_id, created_at, expires_at, revoked_at, last_seen_at`。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。
- BCNF：满足。`session_id` 和 `token_hash` 都是候选键。

设计价值：

- 登录 Cookie 只保存随机 token，数据库保存哈希，有利于安全性和会话撤销。

### 2.5 student

关系模式：

`Student(student_id, user_id, student_name, gender, birth_date, enroll_year, major_id, class_name, phone, email, status)`

约束：

- 主键：`student_id`。
- 唯一约束：`user_id`。
- 外键：`user_id -> user_account(user_id)`，`major_id -> major(major_id)`。
- CHECK：性别、学生状态。

可能函数依赖：

- `student_id -> user_id, student_name, gender, birth_date, enroll_year, major_id, class_name, phone, email, status`。
- `user_id -> student_id, student_name, gender, birth_date, enroll_year, major_id, class_name, phone, email, status`。

范式判断：

- 1NF：基本满足。各字段为单值字段。
- 2NF：满足。候选键为单属性。
- 3NF：基本满足。专业名称、院系名称没有冗余在学生表中，只保存 `major_id`。
- BCNF：在当前约束下基本满足，因为 `student_id` 和 `user_id` 都是候选键。

需要谨慎说明：

- `class_name` 当前只是文本。如果业务中“班级”有年级、专业、辅导员、班主任等独立属性，则 `class_name -> major_id/enroll_year/...` 可能出现传递依赖，应拆为 `class(class_id, class_name, major_id, enroll_year, ...)`，学生表保存 `class_id`。
- `email`、`phone` 未设唯一约束，是否应唯一取决于业务。

### 2.6 teacher

关系模式：

`Teacher(teacher_id, user_id, teacher_name, gender, dept_id, title, phone, email, status)`

约束：

- 主键：`teacher_id`。
- 唯一约束：`user_id`。
- 外键：`user_id -> user_account(user_id)`，`dept_id -> department(dept_id)`。
- CHECK：性别、教师状态。

可能函数依赖：

- `teacher_id -> user_id, teacher_name, gender, dept_id, title, phone, email, status`。
- `user_id -> teacher_id, teacher_name, gender, dept_id, title, phone, email, status`。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。院系名称没有冗余在教师表中。
- BCNF：基本满足。

改进建议：

- 如果后续管理职称等级、职称序列，可拆出 `teacher_title` 字典表，但当前不是必要项。

### 2.7 admin_profile

关系模式：

`AdminProfile(admin_id, user_id, admin_name, phone)`

约束：

- 主键：`admin_id`。
- 唯一约束：`user_id`。
- 外键：`user_id -> user_account(user_id)`。

可能函数依赖：

- `admin_id -> user_id, admin_name, phone`。
- `user_id -> admin_id, admin_name, phone`。

范式判断：

- 1NF、2NF、3NF、BCNF：基本满足。

设计价值：

- 与 `student`、`teacher` 同构，体现统一账号和角色资料分离。

### 2.8 semester

关系模式：

`Semester(semester_id, semester_name, start_date, end_date, selection_start, selection_end, status)`

约束：

- 主键：`semester_id`。
- CHECK：`status IN ('planned','open','closed')`。

可能函数依赖：

- `semester_id -> semester_name, start_date, end_date, selection_start, selection_end, status`。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。
- BCNF：在当前候选键为 `semester_id` 的前提下满足。

改进建议：

- 可增加跨字段 CHECK，例如 `start_date <= end_date`、`selection_start <= selection_end`、选课窗口在学期范围内。当前未实现。
- 如 `semester_name` 业务唯一，可加唯一约束。

### 2.9 course

关系模式：

`Course(course_id, course_name, course_type, credit, total_hours, dept_id, description, status)`

约束：

- 主键：`course_id`。
- 外键：`dept_id -> department(dept_id)`。
- CHECK：课程类型、状态、学分、学时。

可能函数依赖：

- `course_id -> course_name, course_type, credit, total_hours, dept_id, description, status`。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。课程所属院系通过 `dept_id` 引用，没有冗余 `dept_name`。
- BCNF：在当前候选键为 `course_id` 的前提下满足。

设计价值：

- 将课程基本信息独立于开课班次，是规范化设计中的亮点。

### 2.10 classroom

关系模式：

`Classroom(classroom_id, building, room_no, capacity)`

约束：

- 主键：`classroom_id`。
- CHECK：`capacity > 0`。

可能函数依赖：

- `classroom_id -> building, room_no, capacity`。
- 现实语义上通常有 `(building, room_no) -> classroom_id, capacity`，但当前未设置唯一约束。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。
- BCNF：如果只把 `classroom_id` 看作候选键，则满足；如果承认 `(building, room_no)` 也能唯一确定教室，则当前缺少相应候选键约束，BCNF 需要补强。

改进建议：

- 增加 `UNIQUE(building, room_no)`。

### 2.11 course_offering

关系模式：

`CourseOffering(offering_id, course_id, semester_id, teacher_id, classroom_id, max_capacity, selected_count, schedule_text, status)`

约束：

- 主键：`offering_id`。
- 外键：`course_id -> course`，`semester_id -> semester`，`teacher_id -> teacher`，`classroom_id -> classroom`。
- CHECK：状态、容量、已选人数非负。

可能函数依赖：

- `offering_id -> course_id, semester_id, teacher_id, classroom_id, max_capacity, selected_count, schedule_text, status`。
- 如果业务定义同一课程同一学期同一教师同一时间只能有一个班，则可能存在 `(course_id, semester_id, teacher_id, schedule_text) -> offering_id`，但当前未约束。
- `selected_count` 实际由 `enrollment` 中状态为 `selected` 的记录数派生，不是独立事实。

范式判断：

- 1NF：存在争议。`schedule_text` 当前可能包含多个时间段，例如“周一 1-2 节 / 周三 3-4 节”。如果把每个时间段看作独立数据项，则不满足严格 1NF。
- 2NF：主键为单属性，表内非主属性不存在对复合键的部分依赖。
- 3NF：在表内依赖看，基本满足；但 `selected_count` 是跨表派生字段，属于反规范化设计。
- BCNF：在只承认 `offering_id` 为候选键时基本满足；但若存在其他业务候选键，则需要补充唯一约束后再判断。

反规范化说明：

- `selected_count` 提高列表查询和容量展示效率，避免每次都聚合 `enrollment`。
- 当前通过 `trg_enrollment_insert` 和 `trg_enrollment_update` 维护，但需要明确它表示“当前占用名额”还是“历史修读人数”。

改进建议：

- 拆出 `course_schedule(offering_id, weekday, start_section, end_section)`。
- 增加 `CHECK(max_capacity >= selected_count)`，但这仍不能解决并发超选。
- 对 `max_capacity <= classroom.capacity` 使用触发器或应用层事务检查，因为普通 CHECK 不能跨表查询。
- 结合业务增加唯一约束，如 `(course_id, semester_id, teacher_id, schedule_text)` 或更规范的时间表约束。

### 2.12 course_prerequisite

关系模式：

`CoursePrerequisite(course_id, prereq_course_id)`

约束：

- 主键：`(course_id, prereq_course_id)`。
- 外键：两列都引用 `course(course_id)`。

可能函数依赖：

- 该表只有主属性，没有非主属性。
- 非平凡依赖主要是候选键决定整行。

范式判断：

- 1NF：满足。
- 2NF：满足。无非主属性，不存在部分依赖。
- 3NF：满足。
- BCNF：满足。

改进建议：

- 增加 `CHECK(course_id <> prereq_course_id)` 防止课程以自身为先修。
- 防止先修环路需要递归查询或触发器，当前未实现，可作为设计完善点。

### 2.13 enrollment

关系模式：

`Enrollment(enrollment_id, student_id, offering_id, select_time, status, final_score, gpa_point, remark)`

约束：

- 主键：`enrollment_id`。
- 唯一约束：`(student_id, offering_id)`。
- 外键：`student_id -> student`，`offering_id -> course_offering`。
- CHECK：选课状态、成绩范围、绩点范围。

可能函数依赖：

- `enrollment_id -> student_id, offering_id, select_time, status, final_score, gpa_point, remark`。
- `(student_id, offering_id) -> enrollment_id, select_time, status, final_score, gpa_point, remark`。
- 在当前绩点规则固定时，`final_score -> gpa_point`，但这是业务计算规则，不是实体标识依赖。

范式判断：

- 1NF：满足。字段为单值。
- 2NF：满足。虽然存在复合候选键 `(student_id, offering_id)`，但 `select_time/status/final_score/gpa_point/remark` 都依赖整个选课事实，而不是只依赖学生或只依赖班次。
- 3NF：存在可讨论点。若 `gpa_point` 完全由 `final_score` 决定，则 `final_score -> gpa_point` 使 `gpa_point` 成为派生字段，严格 3NF 下应考虑移除或独立为成绩规则表。若系统需要保存历史绩点快照，则可解释为有意反规范化。
- BCNF：在不考虑 `final_score -> gpa_point` 的情况下基本满足；考虑该依赖时不满足 BCNF，因为 `final_score` 不是候选键。

业务限制不足：

- 当前唯一约束只能防止重复选择同一 `offering_id`，不能防止同一学期选择同一课程的不同教学班。因为 `course_id`、`semester_id` 在 `course_offering` 中，无法直接用普通唯一约束跨表表达。

改进建议：

- 若要限制同一学期同一课程只能选一次，可使用触发器检查，或在 `enrollment` 冗余 `course_id/semester_id` 后设置 `UNIQUE(student_id, semester_id, course_id)`。
- `gpa_point` 可改为查询时计算，或建立 `grade_rule` 表并记录规则版本。

### 2.14 score_change_log

关系模式：

`ScoreChangeLog(log_id, enrollment_id, old_score, new_score, changed_by_user_id, changed_at, reason)`

约束：

- 主键：`log_id`。
- 外键：`enrollment_id -> enrollment`，`changed_by_user_id -> user_account`。

可能函数依赖：

- `log_id -> enrollment_id, old_score, new_score, changed_by_user_id, changed_at, reason`。

范式判断：

- 1NF：满足。
- 2NF：满足。
- 3NF：满足。日志表保存事件事实，旧值和新值不是冗余当前状态，而是历史审计数据。
- BCNF：基本满足。

改进建议：

- 可增加 CHECK：`new_score BETWEEN 0 AND 100`，`old_score IS NULL OR old_score BETWEEN 0 AND 100`。
- 可增加索引：`(enrollment_id)`、`(changed_at DESC)`。

## 3. 当前设计中符合规范化的亮点

1. 课程与开课班次分离：`course` 保存稳定课程信息，`course_offering` 保存学期、教师、教室、容量和时间。
2. 多对多联系独立成表：`enrollment` 和 `course_prerequisite` 都是 ER 模型向关系模型转换的典型结果。
3. 用户账号与角色资料分离：统一登录信息放在 `user_account`，避免学生/教师表重复密码字段。
4. 院系、专业、学生分层：学生保存 `major_id`，专业保存 `dept_id`，避免学生表中重复保存院系名称。
5. 成绩日志独立：`score_change_log` 保留历史变更，不覆盖 `enrollment` 当前成绩。

## 4. 可能违反范式或需要解释的地方

| 问题 | 涉及表/字段 | 范式风险 | 当前原因 | 改进方向 |
|---|---|---|---|---|
| 上课时间文本化 | `course_offering.schedule_text` | 严格 1NF 风险 | 实现简单，便于显示 | 拆 `course_schedule` |
| 已选人数冗余 | `course_offering.selected_count` | 派生数据冗余 | 提高容量展示和查询性能 | 触发器/事务严格维护，或查询时聚合 |
| 绩点冗余 | `enrollment.gpa_point` | 3NF/BCNF 风险 | 成绩单展示方便，保存历史快照 | 查询时计算，或引入绩点规则版本 |
| 班级文本 | `student.class_name` | 潜在传递依赖 | 当前只展示班级名 | 拆 `class` 表 |
| 教室自然键未约束 | `classroom.building, room_no` | BCNF 需确认 | 使用 `classroom_id` 作为主键 | 加 `UNIQUE(building, room_no)` |
| 同课跨班重复 | `enrollment` 与 `course_offering` | 业务约束缺失 | 跨表唯一难以直接表达 | 触发器或冗余 `course_id/semester_id` |

## 5. 可以写入报告的规范化结论

正式报告可以这样表述：

> 本系统在逻辑结构设计中采用规范化思想，将稳定实体与业务过程分离。课程基础信息存放在 `course`，具体教学班存放在 `course_offering`，选课结果与成绩作为学生和教学班之间联系的属性存放在 `enrollment`。这种设计避免了课程名称、学分、学时等属性在选课记录中重复出现，有利于减少更新异常和插入异常。

同时也要如实说明：

> 系统中仍存在少量出于实现简化和查询效率考虑的反规范化设计。例如 `course_offering.selected_count` 可由 `enrollment` 聚合得到，但为了快速显示剩余容量，系统将其作为冗余字段保存，并通过触发器维护。`enrollment.gpa_point` 可由成绩计算得到，但为了成绩单查询方便也进行了保存。这些设计需要配合事务和触发器保证一致性。

最后提出完善方向：

> 为进一步提高规范化程度，可将文本型上课时间拆分为 `course_schedule`，将班级信息拆分为独立行政班表，并对教室自然键、学期日期范围、同课跨班重复选择等业务规则增加约束或触发器。
