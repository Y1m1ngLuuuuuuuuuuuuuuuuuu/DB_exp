# FINAL COMPLETION AUDIT

审计时间：2026-06-11

本文件用于核对最终报告中“已实现”和“后续扩展”的边界。所有已实现结论均以当前项目 SQL、后端代码或测试脚本为证据。

## 1. 当前真实存在的触发器

证据文件：`opengauss_setup/sql/migrate_triggers_constraints_20260608.sql`

| 触发器 | 作用表 | 状态 |
| --- | --- | --- |
| `trg_student_role_check` | `student` | 已实现 |
| `trg_teacher_role_check` | `teacher` | 已实现 |
| `trg_admin_role_check` | `admin_profile` | 已实现 |
| `trg_offering_capacity_check` | `course_offering` | 已实现 |
| `trg_classroom_capacity_update_check` | `classroom` | 已实现 |
| `trg_prerequisite_no_cycle` | `course_prerequisite` | 已实现 |
| `trg_enrollment_guard` | `enrollment` | 已实现 |
| `trg_score_change_log` | `enrollment` | 已实现 |
| `trg_grade_scale_no_overlap` | `grade_scale` | 已实现 |

## 2. 当前真实存在的触发器函数

| 函数 | 证据文件 | 作用 | 状态 |
| --- | --- | --- | --- |
| `check_user_role_fn(BIGINT, VARCHAR)` | `migrate_triggers_constraints_20260608.sql` | 检查账号角色是否匹配档案表类型 | 已实现 |
| `trg_profile_role_check_fn()` | `migrate_triggers_constraints_20260608.sql` | 角色档案触发器通用入口 | 已实现 |
| `trg_offering_capacity_check_fn()` | `migrate_triggers_constraints_20260608.sql` | 检查教学班容量不超过教室容量，且不低于当前已选人数 | 已实现 |
| `trg_classroom_capacity_update_check_fn()` | `migrate_triggers_constraints_20260608.sql` | 防止降低教室容量导致已有教学班超限 | 已实现 |
| `trg_prerequisite_no_cycle_fn()` | `migrate_triggers_constraints_20260608.sql` | 防止先修自指和先修环路 | 已实现 |
| `trg_enrollment_guard_fn()` | `migrate_triggers_constraints_20260608.sql` | 选课容量、同课跨班、时间冲突、先修课、退课限制等检查 | 已实现 |
| `trg_score_change_log_fn()` | `migrate_triggers_constraints_20260608.sql` | 成绩变化后写入 `score_change_log` | 已实现 |
| `trg_grade_scale_no_overlap_fn()` | `migrate_grade_policy_20260611.sql` | 防止同一绩点规则版本下分数区间重叠 | 已实现 |

## 3. 当前真实存在的存储函数

| 函数 | 证据文件 | 状态 |
| --- | --- | --- |
| `select_course_tx(VARCHAR, BIGINT)` | `migrate_triggers_constraints_20260608.sql` | 已实现 |
| `calculate_gpa(DECIMAL, BIGINT)` | `migrate_grade_policy_20260611.sql` | 已实现 |

说明：`select_course_tx()` 在调用方事务中执行，并使用 `FOR UPDATE` 锁定目标教学班；`calculate_gpa()` 根据学期绑定的绩点规则版本和成绩区间返回绩点，不恢复 `enrollment.gpa_point` 基础字段。

## 4. 当前真实存在的视图

| 视图 | 证据文件 | 用途 | 状态 |
| --- | --- | --- | --- |
| `v_offering_selected_count` | `migrate_triggers_constraints_20260608.sql` | 统计教学班已选人数和剩余容量 | 已实现 |
| `v_course_offering_detail` | `migrate_triggers_constraints_20260608.sql` | 展示课程、教师、学期、教室、容量、已选人数、结构化时间片汇总 | 已实现 |
| `v_student_timetable` | `migrate_triggers_constraints_20260608.sql` | 展示学生当前已选课程时间表 | 已实现 |
| `v_enrollment_grade_detail` | `migrate_grade_policy_20260611.sql` | 展示成绩、绩点规则版本、等级和课程绩点 | 已实现 |
| `v_student_gpa_summary` | `migrate_grade_policy_20260611.sql` | 统计学生分学期加权绩点 | 已实现 |

这些视图不属于基础表，不恢复 `selected_count`、`schedule_text` 或 `gpa_point` 基础字段。

## 5. 当前真实存在的 SQL 测试脚本与执行结果

| 脚本 | 覆盖内容 | 2026-06-11 执行状态 |
| --- | --- | --- |
| `opengauss_setup/sql/test_triggers_constraints.sql` | 角色错配、先修自指、先修环路、容量超选、时间冲突、同课跨班、重复选课、成绩审计、退课限制、视图 smoke test | 已运行通过 |
| `opengauss_setup/sql/test_grade_policy.sql` | 默认绩点规则、区间重叠失败、`calculate_gpa()`、绩点详情视图和绩点汇总视图 | 已运行通过 |
| `scripts/concurrency_enrollment_test.py` | 两个独立连接同时抢容量为 1 的教学班 | 已运行通过 |
| `report/build_report.sh` | Mermaid 图生成与 XeLaTeX 两轮编译 | 已运行通过 |

验证结果摘要：

```text
Grade policy test: PASS calculate_gpa 95 -> 4.00; PASS calculate_gpa 59 -> 0.00.
Trigger SQL test: Trigger and constraint tests finished with rollback.
Concurrency test: success_count = 1, failed_count = 1, selected_count_in_db = 1.
LaTeX build: Output written on report/main.pdf (53 pages).
```

## 6. 后端事务与锁证据

| 机制 | 代码证据 | 状态 |
| --- | --- | --- |
| 选课事务 | `services/selection_service.py` 使用 `DBSession()` 调用 `SELECT select_course_tx(%s,%s)` | 已实现 |
| 退课事务与行锁 | `services/selection_service.py` 退课查询使用 `FOR UPDATE` | 已实现 |
| 成绩更新事务与行锁 | `services/score_service.py` 查询选课记录使用 `FOR UPDATE` | 已实现 |
| 成绩审计变量 | `services/score_service.py` 使用 `set_config('app.current_user_id', ..., true)` 和 `set_config('app.score_change_reason', ..., true)` | 已实现 |
| 绩点查询 | `services/score_service.py`、`services/course_service.py` 查询 `v_enrollment_grade_detail` | 已实现 |

## 7. 数据库规则实现状态

| 规则 | 数据库实现对象 | 测试证据 | 状态 |
| --- | --- | --- | --- |
| 角色与 profile 一致性 | `trg_student_role_check`、`trg_teacher_role_check`、`trg_admin_role_check` | SQL 测试 PASS | 已实现 |
| 先修课程自指与环路 | `chk_prereq_not_self`、`trg_prerequisite_no_cycle` | SQL 测试 PASS | 已实现 |
| 教学班容量不超过教室容量 | `trg_offering_capacity_check`、`trg_classroom_capacity_update_check` | 既有数据修正 + SQL 测试 | 已实现 |
| 选课容量检查 | `trg_enrollment_guard` + `FOR UPDATE` | SQL 测试 PASS，并发脚本 PASS | 已实现 |
| 同课跨班限制 | `trg_enrollment_guard` 查询同学期同课程其他教学班 | SQL 测试 PASS | 已实现 |
| 时间冲突检查 | `trg_enrollment_guard` + `course_schedule` | SQL 测试 PASS | 已实现 |
| 先修课程通过检查 | `trg_enrollment_guard` + `course_prerequisite` | SQL 逻辑已实现 | 已实现 |
| 重复选同一教学班 | `UNIQUE(student_id, offering_id)` + `select_course_tx()` | SQL 测试 PASS | 已实现 |
| 成绩变更自动审计 | `trg_score_change_log` + `score_change_log` | SQL 测试 PASS | 已实现 |
| 绩点规则版本化 | `grade_policy`、`grade_scale`、`calculate_gpa()`、绩点视图 | SQL 测试 PASS | 已实现 |

## 8. 账号凭据与数据库权限

| 机制 | 证据 | 状态 |
| --- | --- | --- |
| 业务编号登录账号 | `opengauss_setup/sql/init.sql`、`docs/ACCOUNT_POLICY.md` | 已实现 |
| 随机演示初始密码 | `scripts/generate_large_demo_dataset.py`、`secrets/DEMO_ACCOUNT_CREDENTIALS.md` | 已生成，本地忽略 |
| 公开凭据示例 | `docs/DEMO_ACCOUNT_CREDENTIALS.example.md` | 已生成，不含真实密码 |
| 最小权限角色脚本 | `opengauss_setup/sql/grant_roles_20260608.sql` | 已执行通过 |
| 演示 DB 账号绑定 | `opengauss_setup/sql/local/grant_demo_db_accounts_20260611.sql` | 已执行通过，本地忽略 |

当前课程演示仍主要通过应用账号连接 openGauss；数据库账号绑定脚本用于展示正式环境中如何把真实数据库账号绑定到最小权限角色。生产环境仍需接入正式账号、密钥管理和审计策略。

## 9. 样例数据与教室容量一致性

当前 `init.sql` 中 `M201` 的 `capacity` 为 50，`MA101` 对应 `M201` 的 `max_capacity` 为 50，不存在已知冲突。

`migrate_triggers_constraints_20260608.sql` 仍保留既有数据修正语句：

```sql
UPDATE course_offering co
SET max_capacity = c.capacity
FROM classroom c
WHERE co.classroom_id = c.classroom_id
  AND co.max_capacity > c.capacity;
```

最近一次迁移验证输出 `UPDATE 0`，说明当前数据无需修正，但脚本具备防御性。

## 10. 大规模演示数据状态

证据文件：

- `scripts/generate_large_demo_dataset.py`
- `opengauss_setup/sql/local/seed_large_demo_dataset_20260611.sql`
- `opengauss_setup/sql/validate_large_demo_dataset.sql`
- `report/LARGE_DEMO_DATASET_SUMMARY.md`
- `report/LARGE_DEMO_DATASET_VALIDATION.md`

当前本地 openGauss 演示数据规模：

| 对象 | 数量 |
| --- | ---: |
| 学院 | 4 |
| 专业 | 11 |
| 学生 | 100 |
| 教师 | 30 |
| 管理员 | 3 |
| 课程 | 50 |
| 学期 | 4 |
| 教室 | 20 |
| 教学班 | 175 |
| 上课时间片 | 214 |
| 选课记录 | 1480 |
| completed 记录 | 1000 |
| selected 记录 | 425 |
| dropped 记录 | 55 |
| 成绩审计日志 | 80 |

`validate_large_demo_dataset.sql` 已在本地容器执行，容量超限、教室容量超限、重复选课、同课跨班、时间冲突、先修课不满足、成绩状态异常、账号角色错配、先修自指或环路、审计日志无效引用等违规项均为 0。

`secrets/DEMO_ACCOUNT_CREDENTIALS.md` 已生成，包含 3 个管理员、30 个教师和 100 个学生的本地演示初始密码。该文件不进入报告正文，也由 `.gitignore` 排除。

## 11. 报告中可写为“已实现”的内容

- 触发器与触发器函数；
- 选课事务函数 `select_course_tx()`；
- `SELECT ... FOR UPDATE` 行级锁；
- 角色一致性、容量、同课跨班、时间冲突、先修课、退课限制、成绩审计；
- 课程容量、课程详情、学生课表和绩点统计视图；
- 绩点规则版本化；
- 演示账号凭据生成和本地保管；
- 数据库级最小权限角色与演示账号绑定脚本；
- 大规模演示数据生成脚本、只读验证脚本和本地验证结果；
- SQL 回滚型测试脚本和验证结果；
- 多连接并发抢课脚本和验证结果。

## 12. 仍应写成后续改进的内容

- 生产环境真实数据库账号、密钥管理系统和审计策略仍需进一步落地；
- 更大规模并发压测仍需补充；
- 备份恢复、运行监控和物化视图刷新策略仍是后续工作；
- 教师评价打分模块仅作为后续扩展设计，未实现基础表、触发器或页面功能；
- 行政班实体拆分仍是后续优化方向。

## 13. 是否存在报告过度声明

报告中过度声明的处理情况：

- 第 2 章不再把同课跨班限制写成未完成；
- 第 10 章不再把同课跨班限制列为不足；
- 第 5、8、9、10 章已把绩点规则版本化从“后续优化”改为“已通过规则表和视图实现”；
- 附录已加入同课跨班测试、并发测试、权限脚本和绩点规则摘录；
- 教师评价统一表述为后续扩展，不写成已实现。

该审计未发现编译版 LaTeX 报告中仍存在与当前 SQL/代码证据冲突的“已实现”声明。
