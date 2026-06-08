# 触发器与事务实现后的事实清单

生成时间：2026-06-08

本文件依据当前项目 SQL、后端代码和本地 openGauss 容器验证结果整理，供 LaTeX 报告同步使用。报告中凡写作“已实现”的机制，应能在本文件列出的 SQL、代码或测试脚本中找到证据。

## 1. 当前真实存在的触发器

已在本地 openGauss 的 `course_system` 数据库中查询确认，触发器定义来源于 `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`。

| 触发器 | 作用表 | 主要作用 |
|---|---|---|
| `trg_student_role_check` | `student` | 学生档案必须引用 `role='student'` 的账户。 |
| `trg_teacher_role_check` | `teacher` | 教师档案必须引用 `role='teacher'` 的账户。 |
| `trg_admin_role_check` | `admin_profile` | 管理员档案必须引用 `role='admin'` 的账户。 |
| `trg_offering_capacity_check` | `course_offering` | 教学班容量不能超过教室容量，且不能低于当前已选人数。 |
| `trg_classroom_capacity_update_check` | `classroom` | 降低教室容量时不能小于已有教学班容量。 |
| `trg_prerequisite_no_cycle` | `course_prerequisite` | 防止先修课程自指和递归环路。 |
| `trg_enrollment_guard` | `enrollment` | 检查选课容量、时间冲突、先修课、学生状态、班次状态、选课窗口和退课限制。 |
| `trg_score_change_log` | `enrollment` | `final_score` 变化后自动写入 `score_change_log`。 |

## 2. 当前真实存在的触发器函数与存储函数

| 函数 | 类型 | 主要作用 |
|---|---|---|
| `check_user_role_fn(BIGINT, VARCHAR)` | 普通函数 | 检查 `user_account.role` 是否匹配预期角色。 |
| `trg_profile_role_check_fn()` | 触发器函数 | 供学生、教师、管理员档案触发器复用。 |
| `trg_offering_capacity_check_fn()` | 触发器函数 | 检查教学班容量与教室容量、已选人数的一致性。 |
| `trg_classroom_capacity_update_check_fn()` | 触发器函数 | 防止教室容量被降低到已有教学班容量以下。 |
| `trg_prerequisite_no_cycle_fn()` | 触发器函数 | 使用递归查询检测先修课程环路。 |
| `trg_enrollment_guard_fn()` | 触发器函数 | 执行选课、退课相关数据库层完整性检查。 |
| `trg_score_change_log_fn()` | 触发器函数 | 成绩变更后自动插入审计日志。 |
| `select_course_tx(VARCHAR, BIGINT)` | 存储函数 | 封装数据库层选课入口，在调用方事务中执行带锁检查和写入。 |

## 3. 当前真实存在的约束

基础表的主键、外键、`NOT NULL`、`DEFAULT`、状态类 `CHECK` 主要定义在 `opengauss_setup/sql/init.sql` 中。本轮新增或重点使用的业务约束定义在 `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`。

| 约束 | 表 | 类型 | 作用 |
|---|---|---|---|
| `uq_department_name` | `department` | `UNIQUE` | 学院名称唯一。 |
| `uq_major_dept_name` | `major` | `UNIQUE` | 同一学院下专业名称唯一。 |
| `uq_classroom_location` | `classroom` | `UNIQUE` | 同一楼栋同一房间号唯一。 |
| `chk_prereq_not_self` | `course_prerequisite` | `CHECK` | 课程不能把自己作为先修课。 |
| `chk_semester_date_range` | `semester` | `CHECK` | 学期和选课窗口时间范围合法。 |
| `chk_user_session_time_range` | `user_session` | `CHECK` | 会话过期、撤销时间合法。 |
| `chk_schedule_section_range` | `course_schedule` | `CHECK` | 节次限定为 1 到 12，结束节次不早于开始节次。 |
| `uq_student_offering` | `enrollment` | `UNIQUE` | 防止同一学生重复选择同一教学班。 |
| `uq_username` | `user_account` | `UNIQUE` | 登录用户名唯一。 |
| `uq_user_session_token` | `user_session` | `UNIQUE` | 会话 token 哈希唯一。 |

## 4. 当前真实存在的视图

三个视图均定义在 `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`。它们属于查询层封装，不是基础表，不破坏 3NF。

| 视图 | 作用 |
|---|---|
| `v_offering_selected_count` | 从 `enrollment` 聚合统计教学班已选人数和剩余容量，替代基础表中的 `selected_count` 派生字段。 |
| `v_course_offering_detail` | 汇总课程、教师、学期、教室、容量、已选人数、剩余容量和展示用上课时间，供课程查询和管理页面使用。 |
| `v_student_timetable` | 展示学生当前 `selected` 课程的结构化课表。 |

## 5. 后端事务与锁

| 机制 | 实现状态 | 证据 |
|---|---|---|
| 选课事务 | 已实现 | `services/selection_service.py` 使用 `DBSession`，调用 `SELECT select_course_tx(%s,%s)`。 |
| 退课事务 | 已实现 | `services/selection_service.py` 使用 `DBSession`，对目标 `enrollment` 查询使用 `FOR UPDATE`。 |
| 成绩更新事务 | 已实现 | `services/score_service.py` 使用 `DBSession`，锁定目标 `enrollment` 后设置审计上下文并更新成绩。 |
| 行级锁 | 已实现 | `select_course_tx()` 和 `trg_enrollment_guard_fn()` 均锁定 `course_offering` 行；退课和成绩更新也使用 `FOR UPDATE` 锁定目标记录。 |
| 重复选课兜底 | 已实现 | `enrollment` 表有 `UNIQUE(student_id, offering_id)`。 |

## 6. 关键一致性机制状态

| 问题 | 是否由数据库层实现 | 说明 |
|---|---|---|
| 成绩更新自动写入 `score_change_log` | 是 | `trg_score_change_log` 在 `enrollment.final_score` 更新后触发；操作者由同一事务中的 `set_config('app.current_user_id', ...)` 传入。 |
| 选课容量检查 | 是 | `trg_enrollment_guard` 获得 `course_offering` 行锁后统计 `enrollment` 中 `status='selected'` 记录。 |
| 时间冲突检查 | 是 | `trg_enrollment_guard` 基于 `course_schedule` 的星期和节次区间检查同学期冲突。 |
| 先修课程通过检查 | 是 | `trg_enrollment_guard` 要求先修课存在 `completed` 且 `final_score >= 60` 的历史选课记录。 |
| 先修自指和环路检查 | 是 | `chk_prereq_not_self` 防自指，`trg_prerequisite_no_cycle` 用递归查询防环路。 |
| 角色与 profile 一致性 | 是 | `trg_student_role_check`、`trg_teacher_role_check`、`trg_admin_role_check` 强制 `user_account.role` 与档案表匹配。 |
| 教学班容量与教室容量一致性 | 是 | `trg_offering_capacity_check` 和 `trg_classroom_capacity_update_check` 维护跨表一致性。 |

## 7. 测试脚本状态

`opengauss_setup/sql/test_triggers_constraints.sql` 存在，并已在本地 openGauss 容器中执行通过。脚本使用事务和 `ROLLBACK`，不会污染样例数据。

本次验证覆盖：

- 角色档案错配；
- 先修课程自指；
- 先修课程环路；
- 容量超选；
- 时间冲突；
- 重复选课唯一约束；
- 成绩更新缺少操作者时拒绝；
- 成绩更新自动写入审计日志；
- 已完成选课禁止退课；
- 三个视图的 smoke test。

## 8. 仍然没有实现或无法充分验证的机制

- 数据库级角色授权尚未实现。当前学生、教师、管理员权限主要由应用层 `user_account.role`、页面守卫和服务层检查控制。
- 同一学生同一学期选择同一课程不同教学班的限制尚未固化为数据库触发器或唯一约束。
- 高并发压力测试尚未完成。本次 SQL 测试验证了触发器和事务逻辑，但没有模拟多连接同时抢最后一个名额的压力场景。
- 物化视图未实现。当前使用普通视图和索引补偿规范化后的查询成本。
- 备份、恢复、监控、迁移版本表等运维机制仍以设计建议为主。
- 当前样例学期 `2025-2026-2` 的选课窗口为 2026-02-10 至 2026-02-20；在 2026-06-08 的系统日期下，真实选课会被选课窗口规则拒绝。测试脚本使用专门测试学期验证选课规则。
