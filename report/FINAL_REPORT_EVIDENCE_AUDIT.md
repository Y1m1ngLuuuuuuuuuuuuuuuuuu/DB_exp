# 最终报告实现证据审计

生成时间：2026-06-08

本文件用于支撑期末报告最终一致性检查。报告中写为“已实现”的数据库机制，必须能在下表中找到 SQL、后端代码或测试脚本证据。

## 1. 已实现机制与证据

| 报告机制 | 实现对象 | 证据文件 | 测试或验证 | 结论 |
|---|---|---|---|---|
| 学生档案角色一致性 | `trg_student_role_check`、`check_user_role_fn` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 teacher-as-student 失败用例 | 有证据，已实现 |
| 教师档案角色一致性 | `trg_teacher_role_check`、`check_user_role_fn` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 student-as-teacher 失败用例 | 有证据，已实现 |
| 管理员档案角色一致性 | `trg_admin_role_check`、`check_user_role_fn` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | SQL 触发器存在；未单独列管理员错配测试 | 有 SQL 证据，已实现 |
| 先修课程自指与环路检查 | `chk_prereq_not_self`、`trg_prerequisite_no_cycle` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 self prerequisite 和 prerequisite cycle 失败用例 | 有证据，已实现 |
| 教学班容量不超过教室容量 | `trg_offering_capacity_check`、`trg_classroom_capacity_update_check` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | 迁移脚本含历史数据修正；`init.sql` 容量审计无冲突 | 有证据，已实现 |
| 选课容量检查 | `trg_enrollment_guard` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 capacity full 失败用例 | 有证据，已实现 |
| 时间冲突检查 | `trg_enrollment_guard`、`course_schedule` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 timetable conflict 失败用例 | 有证据，已实现 |
| 先修课程通过检查 | `trg_enrollment_guard`、`course_prerequisite`、`enrollment` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | SQL 中要求 `completed` 且 `final_score >= 60`；测试覆盖先修关系合法性 | 有 SQL 证据，已实现 |
| 已完成或已有成绩不能退课 | `trg_enrollment_guard` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 completed enrollment drop 失败用例 | 有证据，已实现 |
| 成绩修改自动审计 | `trg_score_change_log`、`score_change_log` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 score audit trigger inserted log row | 有证据，已实现 |
| 成绩修改操作者传递 | `set_config('app.current_user_id', ...)` | `services/score_service.py`、`opengauss_setup/sql/test_triggers_constraints.sql` | 测试中缺少操作者会失败，设置操作者后写入日志 | 有证据，已实现 |
| 数据库层选课入口 | `select_course_tx` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `services/selection_service.py` 调用 `SELECT select_course_tx(%s,%s)` | 有证据，已实现 |
| 行级锁防止超选 | `SELECT ... FOR UPDATE` 锁定 `course_offering` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`、`services/selection_service.py` | SQL 测试验证容量满失败；未做多连接压力测试 | 有实现证据，压力测试待补 |
| 重复选课防护 | `UNIQUE(student_id, offering_id)`、`select_course_tx` | `opengauss_setup/sql/init.sql`、`migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 中 duplicate key 失败用例 | 有证据，已实现 |
| 已选人数统计视图 | `v_offering_selected_count` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 视图 smoke test | 有证据，已实现 |
| 教学班详情视图 | `v_course_offering_detail` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 视图 smoke test；服务层课程查询使用 | 有证据，已实现 |
| 学生课表视图 | `v_student_timetable` | `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql` | `test_triggers_constraints.sql` 视图 smoke test | 有证据，已实现 |
| 后端事务封装 | `DBSession` | `db/connection.py` | `selection_service.py`、`score_service.py` 使用 `with DBSession()` | 有证据，已实现 |

## 2. 关键文件存在性

- `opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`：存在，包含 `CREATE OR REPLACE FUNCTION`、`CREATE TRIGGER`、`CREATE OR REPLACE VIEW`、`SELECT ... FOR UPDATE`、成绩日志写入、容量检查、时间冲突检查、先修课程检查、角色一致性检查和教室容量一致性检查。
- `opengauss_setup/sql/test_triggers_constraints.sql`：存在，并已在本地 openGauss 容器执行通过；脚本最后执行 `ROLLBACK`。
- `opengauss_setup/sql/add_user_session.sql`：存在，用于会话表补充脚本。
- `report/chapters/appendix_sql_tests.tex`：存在，并由 `report/main.tex` 引入。

## 3. 样例数据与容量触发器一致性

已检查 `opengauss_setup/sql/init.sql` 中初始教室容量与教学班容量，没有发现 `course_offering.max_capacity > classroom.capacity` 的样例数据冲突。

`migrate_triggers_constraints_20260608.sql` 中仍保留历史数据修正语句：

```sql
UPDATE course_offering co
SET max_capacity = c.capacity
FROM classroom c
WHERE co.classroom_id = c.classroom_id
  AND co.max_capacity > c.capacity;
```

因此报告中“迁移脚本先修正历史样例数据，再启用触发器”的表述有证据。

## 4. 摘要、正文、结论、附录一致性

- 摘要、第 6 章、第 7 章、第 9 章、第 10 章均将触发器、事务和视图写为已实现，证据来自迁移脚本、后端服务和测试脚本。
- 第 5 章仍坚持 3NF 主线，没有把 `selected_count`、`schedule_text`、`gpa_point` 写回基础表。
- 第 8 章把 `selected_count` 与 `schedule_text` 写为视图字段或查询结果，未写成基础表字段。
- 附录提供关键 SQL 摘录，不是完整 SQL 文件全文。

## 5. 需要保持为后续改进的内容

下列机制没有完整落地，报告中应保持为“后续改进”或“不足”：

- 数据库级最小权限授权尚未实现；
- 同一学生同一学期选择同一课程不同教学班的限制尚未固化；
- 多连接高并发压力测试尚未完成；
- 物化视图、备份恢复、监控和迁移版本表仍是后续工作；
- 绩点规则表、行政班实体和培养方案规则表尚未实现。
