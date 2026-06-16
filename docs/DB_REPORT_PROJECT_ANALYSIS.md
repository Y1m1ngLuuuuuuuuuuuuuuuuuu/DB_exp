# 选课系统项目分析与期末报告素材梳理

本文档面向“数据库原理2”期末报告写作，依据当前项目代码、openGauss 初始化 SQL 以及课堂笔记进行分析。重点不是单纯介绍功能，而是把项目设计映射到数据库设计流程、ER 建模、关系模型、规范化、完整性、触发器、事务、并发控制、物理设计和运行维护等课程知识点。

## 0. 分析依据

主要项目文件：

- `README.md`：功能说明、数据库表说明、项目结构、部署方式。
- `opengauss_setup/sql/init.sql`：当前数据库主建表脚本，包含 14 张表、主键、外键、唯一约束、CHECK 约束、默认值、索引和样本数据。
- `opengauss_setup/sql/add_user_session.sql`：为旧库补充 `user_session` 表的迁移脚本。
- `db/connection.py`：基于 `psycopg2` 的 openGauss 连接和 `DBSession` 事务上下文。
- `services/*.py`：数据访问层和业务规则实现。
- `pages/*.py`：Streamlit 页面层和角色入口。
- `opengauss_setup/schema_query_optimization.md`：已有的模式设计与查询优化分析，可作为报告性能优化和后续改进材料。

课堂笔记对应关系：

- `chapter7.md`：数据库系统设计流程，规划、需求分析、概念设计、逻辑设计、物理设计、实现与运行维护。
- `chapter8.md`：事务 ACID、恢复、并发控制、封锁、两段锁、完整性规则、触发器、安全性。
- `chapter9.md`：分布式数据库。当前项目为集中式部署，可在扩展章节中说明后续分布式部署方向。
- `chapter10.md`：对象关系数据库。当前项目仍是关系模型，可作为“未采用对象关系特性”的说明。

> 2026-06-08 更新：项目已完成 3NF 方向的结构调整，新增 `course_schedule` 表，删除 `course_offering.selected_count`、`course_offering.schedule_text` 和 `enrollment.gpa_point` 三个反范式风险字段；`selection_service.enroll()` 也已改为 `DBSession` 单事务并使用 `SELECT ... FOR UPDATE` 锁定开课班次。本文中旧字段相关表述可作为“重构前问题与改进动机”材料，当前结论以 `docs/THIRD_NORMAL_FORM_REFACTOR.md` 和 `opengauss_setup/sql/init.sql` 为准。

## 1. 项目结构扫描

当前项目为 Python + Streamlit + psycopg2 + Docker openGauss 的选课系统。没有 ORM 模型，没有 Alembic 等 migration 框架，数据库模式主要由 SQL 脚本维护。

| 模块 | 文件 | 数据库相关作用 |
|---|---|---|
| 数据库连接 | `config.py` | 配置 openGauss 主机、端口、账号、数据库名；当前端口为 `15432`，驱动为 psycopg2。 |
| 数据库访问层 | `db/connection.py` | `get_connection()` 建立 openGauss 连接；`DBSession` 在上下文退出时 commit/rollback；`query/query_one/execute/execute_many` 封装 SQL 执行。 |
| 建表与初始化 | `opengauss_setup/sql/init.sql` | 创建所有核心表、约束、触发器并装入样本数据，是报告中最主要的数据库设计证据。 |
| 增量迁移 | `opengauss_setup/sql/add_user_session.sql` | 为已有数据库补充登录会话表 `user_session`。 |
| 容器初始化 | `opengauss_setup/docker/docker-compose.yml`、`init_db.sh`、`start_opengauss.sh` | 使用 Docker 启动 openGauss，并导入初始化 SQL。 |
| 用户认证 | `services/auth_service.py` | 校验 `user_account`，创建/恢复/撤销 `user_session`，维护登录状态。 |
| 学生维护 | `services/student_service.py` | 学生查询、新增、修改、删除；新增学生时在同一 `DBSession` 中插入 `user_account` 和 `student`。 |
| 教师维护 | `services/teacher_service.py` | 教师查询、新增、修改、删除；删除教师前检查是否存在 `course_offering`。 |
| 课程与教学班 | `services/course_service.py` | 学期、课程、开课班次 CRUD；学生可选课程查询；已选课程查询。 |
| 选课退课 | `services/selection_service.py` | 实现选课、退课、恢复选课，包含容量、开放时间、先修课、成绩后不可退课等应用层校验。 |
| 成绩管理 | `services/score_service.py` | 成绩录入、绩点计算、教师权限判断、成绩分布、成绩修改日志查询。 |
| 权限控制 | `app.py`、`pages/_guards.py` | 根据 `role` 分配页面；`require_role()` 阻止未授权访问。 |
| 页面层 | `pages/*.py` | 调用 service 层完成管理员、教师、学生对应功能。 |
| 优化文档 | `opengauss_setup/schema_query_optimization.md` | 已整理索引、事务、查询改写和模式优化建议，可并入报告“物理设计与优化”章节。 |

## 2. 业务需求分析

### 2.1 系统用户角色

| 角色 | 当前实现 | 证据 |
|---|---|---|
| 学生 | 登录后访问“我的选课”“我的成绩单”；可查询可选课程、选课、退课、查看成绩。 | `app.py` 中 `_NAV["student"]`；`pages/student_select.py`；`pages/student_report.py`。 |
| 教师 | 登录后访问“成绩管理”；只能维护自己负责的开课班次成绩。 | `app.py` 中 `_NAV["teacher"]`；`services/score_service.py` 的 `can_manage_offering_score()`。 |
| 管理员 | 拥有首页、学期管理、开课安排、课程维护、成绩管理、学生维护、教师维护。 | `app.py` 中 `_NAV["admin"]`；各 `pages/*_manage.py`。 |

### 2.2 核心功能

| 功能 | 当前状态 | 说明 |
|---|---|---|
| 登录认证 | 已实现 | `user_account` 存储账号、密码哈希、角色；`user_session` 支持 Cookie 持久登录。 |
| 角色权限 | 已实现，应用层为主 | 页面入口通过 `require_role()` 控制；数据库层未建立不同 DB 用户权限。 |
| 课程查询 | 已实现 | 管理员课程维护、学生可选课程、已选课程都通过多表 JOIN 查询。 |
| 选课 | 已实现，应用层校验 | 校验学期开放、班次开放、选课窗口、容量、先修课、重复同一班次。 |
| 退课 | 已实现，应用层校验 | 只允许退自己的课、状态必须为 `selected`、成绩已录入不能退、选退课窗口内才允许。 |
| 课程管理 | 已实现 | 管理员可新增、修改、删除课程；删除前检查是否存在开课安排。 |
| 开课班次管理 | 已实现 | 管理员分配课程、教师、教室、学期、容量、上课时间；有选课记录时禁止删除。 |
| 学期管理 | 已实现 | 管理员维护学期、起止日期、选课时间窗口和状态。 |
| 学生/教师维护 | 已实现 | 新增时同步创建登录账号；删除受外键或业务检查限制。 |
| 成绩录入 | 已实现 | 教师或管理员批量录入；教师只能维护自己班次。 |
| 成绩修改日志 | 已实现，应用层写日志 | `score_change_log` 保存旧成绩、新成绩、操作人和原因。 |
| 时间冲突检查 | 未实现 | `schedule_text` 是文本，系统没有拆分时间片，也没有检查学生不同班次时间冲突。 |
| 同一课程跨班重复限制 | 部分实现 | `UNIQUE(student_id, offering_id)` 防止重复同一教学班，但未防止同一学期选同一课程的多个班次。 |
| 数据库级业务触发器 | 部分实现 | 只有 `enrollment` 插入/状态更新维护 `course_offering.selected_count`，容量和时间冲突未放到触发器。 |

### 2.3 数据需求

系统需要长期保存以下核心数据：

- 组织结构：院系 `department`、专业 `major`、教室 `classroom`。
- 用户身份：统一账号 `user_account`、登录会话 `user_session`、学生 `student`、教师 `teacher`、管理员 `admin_profile`。
- 教学资源：学期 `semester`、课程定义 `course`、开课班次 `course_offering`、先修关系 `course_prerequisite`。
- 过程数据：选课记录 `enrollment`，包括选课状态、选课时间、成绩、绩点。
- 审计数据：成绩修改日志 `score_change_log`。

### 2.4 业务规则实现矩阵

| 业务规则 | 当前实现位置 | 实现状态 | 报告写法 |
|---|---|---|---|
| 学生不能重复选择同一教学班 | 数据库层 `UNIQUE(student_id, offering_id)`；应用层先查 existing | 已实现 | 可归入实体完整性和用户定义完整性。 |
| 容量不能超过上限 | 应用层比较 `selected_count >= max_capacity`；触发器只维护人数 | 部分实现 | 单用户流程可用，并发下存在超选风险；建议事务锁补强。 |
| 选课时间窗口 | 应用层检查 `CURRENT_TIMESTAMP BETWEEN selection_start AND selection_end` | 已实现，应用层 | 可写为应用层业务完整性。 |
| 学期必须开放 | 应用层检查 `semester.status='open'` | 已实现，应用层 | 与 `semester.status` 的 CHECK 配合。 |
| 开课班次必须开放 | 应用层检查 `course_offering.status='open'` | 已实现，应用层 | 与 `course_offering.status` 的 CHECK 配合。 |
| 先修课程必须通过 | 应用层 `_has_passed_prerequisites()` | 已实现，应用层 | 查询 `course_prerequisite` 和历史 `enrollment`。 |
| 时间冲突检查 | 无 | 未实现 | 可作为设计完善点：拆 `course_schedule` 表并在应用层或触发器检查。 |
| 成绩录入后不能退课 | 应用层 `drop()` 检查 `final_score IS NOT NULL` | 已实现，应用层 | 可写入退课规则。 |
| 退课后恢复余量 | 数据库触发器在 `selected -> dropped` 时 `selected_count - 1` | 已实现，数据库层 | 可重点展示触发器 ECA 规则。 |
| 恢复选课后占用余量 | 数据库触发器在 `dropped -> selected` 时 `selected_count + 1` | 已实现，数据库层 | 可重点展示触发器。 |
| 成绩修改写日志 | 应用层 `update_score()` 先更新 `enrollment` 再插入 `score_change_log` | 已实现但事务不足 | 建议放入同一事务或触发器。 |
| 删除课程时保护历史 | 应用层检查有开课安排时禁止删除；外键也会阻止部分删除 | 部分实现 | 可说明当前以“限制删除”为主，后续可软删除。 |
| 删除学生时保护历史选课 | 依赖外键阻止；应用层未提前统计选课记录 | 部分实现 | 可作为维护策略改进：有历史记录时禁删或软删除。 |

## 3. 概念设计分析

本项目概念模型较清晰，已经把“课程”与“开课班次”分离，这是选课系统数据库设计中最重要的建模点之一：

- `course` 表示抽象课程，例如“数据库原理”，属性包括课程号、课程名、课程类型、学分、学时和开课院系。
- `course_offering` 表示某一学期由某教师在某教室开设的具体教学班，属性包括容量、已选人数、上课时间和状态。
- `enrollment` 把学生和开课班次连接起来，实现学生与开课班次的多对多关系，同时承载选课状态、成绩和绩点。

主要实体：

- 学生：`student(student_id, user_id, student_name, gender, enroll_year, major_id, class_name, phone, email, status)`。
- 教师：`teacher(teacher_id, user_id, teacher_name, gender, dept_id, title, phone, email, status)`。
- 管理员：`admin_profile(admin_id, user_id, admin_name, phone)`。
- 用户账号：`user_account(user_id, username, password_hash, role, status, last_login_at, created_at)`。
- 院系：`department(dept_id, dept_name, office_phone, office_location)`。
- 专业：`major(major_id, major_name, dept_id)`。
- 学期：`semester(semester_id, semester_name, start_date, end_date, selection_start, selection_end, status)`。
- 课程：`course(course_id, course_name, course_type, credit, total_hours, dept_id, description, status)`。
- 教室：`classroom(classroom_id, building, room_no, capacity)`。
- 开课班次：`course_offering(offering_id, course_id, semester_id, teacher_id, classroom_id, max_capacity, selected_count, schedule_text, status)`。
- 选课记录：`enrollment(enrollment_id, student_id, offering_id, select_time, status, final_score, gpa_point, remark)`。
- 先修关系：`course_prerequisite(course_id, prereq_course_id)`。
- 成绩日志：`score_change_log(log_id, enrollment_id, old_score, new_score, changed_by_user_id, changed_at, reason)`。

主要联系：

- 院系 1:N 专业，`major.dept_id -> department.dept_id`。
- 院系 1:N 课程，`course.dept_id -> department.dept_id`。
- 院系 1:N 教师，`teacher.dept_id -> department.dept_id`。
- 专业 1:N 学生，`student.major_id -> major.major_id`。
- 用户账号 1:1 学生/教师/管理员资料，通过各资料表的 `user_id UNIQUE` 实现。
- 学期 1:N 开课班次，`course_offering.semester_id -> semester.semester_id`。
- 课程 1:N 开课班次，`course_offering.course_id -> course.course_id`。
- 教师 1:N 开课班次，`course_offering.teacher_id -> teacher.teacher_id`。
- 教室 1:N 开课班次，`course_offering.classroom_id -> classroom.classroom_id`。
- 学生 M:N 开课班次，通过 `enrollment` 转换为两个 1:N。
- 课程 M:N 课程，即先修自关联，通过 `course_prerequisite` 转换。
- 成绩修改日志 N:1 选课记录，N:1 操作用户。

## 4. 逻辑设计分析

关系模型已经覆盖选课系统主要实体和联系。最值得在报告中强调的是：

1. `course` 与 `course_offering` 分离，避免把“课程定义”和“某学期教学班”混在一张表里。
2. `enrollment` 是学生和开课班次多对多联系的关系化结果，且增加了联系自身属性，如 `select_time`、`status`、`final_score`、`gpa_point`。
3. `course_prerequisite` 是课程自关联的关系化结果，主键为 `(course_id, prereq_course_id)`。
4. `user_account` 与学生/教师/管理员资料分离，支持统一登录和角色控制。

当前所有主要关系模式、主键和外键详见 `ER_RELATIONAL_MODEL_DRAFT.md`。

## 5. 规范化和范式概览

总体上，组织、用户、课程、学期、开课班次、选课记录等核心表均围绕主键组织，主体结构达到 3NF 的基础较好。需要重点讨论的设计点：

- `schedule_text` 使用一个字符串保存多个上课时间，例如“周一 1-2 节 / 周三 3-4 节”。如果把每个时间段视为独立数据项，则该字段不完全满足 1NF，建议拆成 `course_schedule(offering_id, weekday, start_section, end_section)`。
- `course_offering.selected_count` 是从 `enrollment` 派生的冗余计数字段，当前由触发器维护。它有利于快速展示剩余名额，但存在同步语义和并发一致性要求。
- `enrollment.gpa_point` 可由 `final_score` 和绩点规则计算得到，是出于查询和成绩单展示简化的反规范化字段。如果绩点规则变化，需要考虑历史快照还是重新计算。
- `student.class_name` 只是普通文本，当前没有 `class` 行政班表。若后续需要管理班级、辅导员、年级等信息，可拆出班级实体。
- `classroom` 中 `building + room_no` 在业务上通常可唯一确定教室，但当前未设唯一约束；是否违反 BCNF 取决于业务语义。

逐表范式判断详见 `NORMALIZATION_AUDIT.md`。

## 6. 完整性约束、触发器和检查机制概览

数据库层已实现：

- 每张核心表都有主键。
- 大量外键约束维护参照完整性。
- `username`、`token_hash`、学生/教师/管理员的 `user_id`、`(student_id, offering_id)` 等使用唯一约束。
- 角色、状态、性别、学分、学时、容量、成绩、绩点等使用 CHECK 约束。
- 多个字段设置默认值，如 `created_at`、`select_time`、`status`、`selected_count`。
- `trg_enrollment_insert` 和 `trg_enrollment_update` 自动维护 `course_offering.selected_count`。

应用层已实现：

- 选课开放学期、开放班次、选课时间窗口、容量、先修课、重复选课校验。
- 退课身份校验、退课状态校验、已录成绩禁止退课。
- 教师只能维护自己负责的开课班次成绩。
- 删除课程、教师、班次前进行一定业务检查。

尚未实现或适合作为完善点：

- 数据库层容量强约束。
- 数据库层时间冲突检查。
- 同一学期同一课程跨班重复选择限制。
- `max_capacity <= classroom.capacity`。
- 成绩更新和日志写入的原子事务。
- 用触发器自动写 `score_change_log`。
- 细粒度数据库用户和角色授权。

详细审计见 `CONSTRAINT_TRIGGER_TRANSACTION_AUDIT.md`。

## 7. 事务、锁和并发控制概览

`DBSession` 提供基本事务边界：一个上下文内成功则 commit，异常则 rollback。但多数 service 函数通过 `query_one()` 和 `execute()` 多次调用数据库，每次调用都会创建独立连接和独立事务。

当前已经较好处理的点：

- `create_student()` 和 `create_teacher()` 使用同一个 `DBSession` 同时创建账号和资料，体现事务原子性。
- `UNIQUE(student_id, offering_id)` 可以防止同一学生重复插入同一教学班。
- 触发器与对应的 enrollment 写操作处于同一数据库事务中。

主要并发风险：

- 选课容量检查和插入不在同一事务中，没有 `SELECT ... FOR UPDATE`，多个学生同时抢最后一个名额时可能都读到同一 `selected_count`，发生超选。
- 恢复选课 `dropped -> selected` 也存在同类并发风险。
- `update_score()` 中成绩更新和日志插入分两次 `execute()`，若第二步失败，可能出现成绩已改但日志缺失。
- `delete_course()`、`delete_offering()` 等先查再删，也可能受到并发插入影响。

报告中可以结合课堂笔记第 8 章的 ACID、封锁、两段锁和可串行化调度来说明后续设计：选课事务应使用行级 X 锁或原子条件更新，保证容量检查和插入具有隔离性。

## 8. 物理设计概览

当前数据库类型为 openGauss，部署在 Docker 容器中；Python 使用 `psycopg2-binary` 访问。物理设计特点：

- 主键使用自然键和代理键结合：学生号、教师号、课程号等业务标识使用 `VARCHAR` 主键；会话、开课班次、选课记录、日志使用 `BIGSERIAL`。
- 取值范围使用 `VARCHAR + CHECK` 表示枚举状态，兼顾可读性和迁移性。
- 只显式创建了 `user_session` 相关索引；其他主键和唯一约束会自动建立索引，但外键字段和高频查询字段缺少显式辅助索引。
- 高频查询包括：学生可选课程、学生已选课程、班次名单、成绩分布、成绩日志、管理员统计、课程/学生/教师模糊查询。

建议索引：

- `course_offering(semester_id, status)`，用于学生可选课程和管理端班次过滤。
- `course_offering(teacher_id, semester_id)`，用于教师成绩管理。
- `enrollment(student_id, status, offering_id)`，用于学生已选和先修查询。
- `enrollment(offering_id, status, student_id)`，用于班次名单和人数统计。
- `enrollment(offering_id, status, final_score)`，用于成绩分布。
- `course_prerequisite(prereq_course_id)`，用于反向查先修依赖。
- `score_change_log(enrollment_id)` 和 `score_change_log(changed_at DESC)`，用于成绩审计查询。

## 9. 运行、维护与数据库管理概览

已实现：

- Docker openGauss 本地运行。
- 初始化脚本可重建数据库并导入样本数据。
- 应用层有管理员角色和管理页面。
- `user_session` 支持登录会话撤销和过期。
- `score_change_log` 保存成绩修改历史。
- 关键约束由 DBMS 负责检查，异常返回给应用层。

不足和可写入报告的完善方案：

- 数据库备份恢复未形成脚本，可补充 openGauss `gs_dump`、`gsql` 导入、定期备份策略。
- 数据库层权限未细分，目前应用使用同一个数据库账号连接，报告中可设计 `app_admin`、`app_teacher`、`app_student` 或只读统计账号。
- 日志主要覆盖成绩修改，未覆盖登录审计、选课退课审计和管理员变更审计。
- 运行监控、慢查询分析、索引维护、数据归档尚未实现。
- 删除策略以限制删除为主，历史数据生命周期和软删除策略可进一步设计。

## 10. 最适合重点展示的课程知识点

1. 数据库设计流程：可按规划、需求分析、概念设计、逻辑设计、物理设计、运行维护组织报告。
2. ER 建模：课程、开课班次、学生、教师、学期、选课记录之间的基数关系完整。
3. 关系模型转换：`enrollment` 解决 M:N，`course_prerequisite` 解决课程自关联。
4. 规范化：课程与开课班次分离、用户账号与角色资料分离、选课联系属性下沉到中间表。
5. 完整性约束：主键、外键、唯一、CHECK、DEFAULT 都有项目证据。
6. 触发器：`selected_count` 自动维护适合展示 ECA 主动规则。
7. 事务与锁：当前实现不足很适合写“并发抢课问题”和改进方案，能体现第 8 章知识。

## 11. 当前最薄弱的部分

1. 关键选课流程缺少单事务和行级锁，容量并发一致性不足。
2. 上课时间没有结构化，无法进行时间冲突检查，也影响 1NF 分析。
3. 物理索引不足，除了 `user_session` 外，高频 JOIN 和过滤字段没有显式索引。
4. 数据库级权限管理不足，主要依赖应用层角色控制。
5. 成绩更新与日志写入不是同一事务，审计完整性有风险。

## 12. 最优先补充的 3 个数据库相关功能

1. 改造选课事务：在同一 `DBSession` 中 `SELECT course_offering ... FOR UPDATE`，完成容量检查、先修检查、插入/恢复选课，或使用原子条件更新防止超选。
2. 拆分上课时间：新增 `course_schedule` 表，支持时间冲突检查，并为报告补强 1NF 和完整性约束设计。
3. 增加索引和审计：为 `course_offering`、`enrollment`、`score_change_log` 等高频表建立组合索引；将成绩日志写入放入同一事务或改为触发器。
