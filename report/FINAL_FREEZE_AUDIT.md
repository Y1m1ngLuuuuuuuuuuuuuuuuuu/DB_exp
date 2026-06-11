# FINAL FREEZE AUDIT

审计时间：2026-06-11

本文件记录项目冻结前最后一轮收口结果。冻结范围限定为账号凭据、数据库级权限绑定和绩点规则版本化，不继续扩展教师评价、行政班实体、前端页面或其他新业务功能。

## 1. 本轮修改前的剩余问题

根据 `report/FINAL_COMPLETION_AUDIT.md` 的上一版结论，冻结前仍需收口：

1. 数据库级最小权限脚本已有角色设计，但尚未提供演示数据库登录账号与角色绑定脚本；
2. `enrollment.gpa_point` 已从基础表中删除，但绩点规则版本化仍是后续优化方向；
3. 演示业务账号仍需要从临时用户名规则收敛到业务身份编号规则；
4. 明文演示凭据需要从 SQL 和报告中隔离，只允许保存在本地忽略目录。

## 2. 本轮完成的账号凭据优化

| 项目 | 完成情况 | 证据 |
| --- | --- | --- |
| 登录账号命名规则 | 学生使用 `student.student_id`，教师使用 `teacher.teacher_id`，管理员使用 `admin_profile.admin_id` | `opengauss_setup/sql/init.sql`、`docs/ACCOUNT_POLICY.md` |
| 随机初始密码 | 由脚本为每个演示账号生成独立随机密码 | `scripts/generate_demo_credentials.py` |
| 哈希存储 | SQL 只保存 SHA-256 `password_hash`，不保存明文密码 | `init.sql`、`services/auth_service.py` |
| 本地凭据文件 | 明文初始密码只写入 `secrets/DEMO_ACCOUNT_CREDENTIALS.md` | 文件已生成，目录被 `.gitignore` 排除 |
| 公开示例文件 | 只提交格式示例，不含真实密码 | `docs/DEMO_ACCOUNT_CREDENTIALS.example.md` |

本轮执行 `python scripts/generate_demo_credentials.py` 后，脚本已同步更新 `init.sql` 中的账号哈希，并生成本地账号同步脚本 `opengauss_setup/sql/local/seed_demo_accounts_20260611.sql`。

## 3. 本轮完成的数据库级权限账号绑定

| 项目 | 完成情况 | 证据 |
| --- | --- | --- |
| 分层数据库角色 | `db_student_role`、`db_teacher_role`、`db_admin_role`、`db_app_role` | `opengauss_setup/sql/grant_roles_20260608.sql` |
| 角色创建方式 | openGauss 中使用 `NOLOGIN PASSWORD DISABLE` 创建权限分组角色 | `grant_roles_20260608.sql` |
| 演示数据库登录账号 | `db_app_demo_user`、`db_student_demo_user`、`db_teacher_demo_user`、`db_admin_demo_user` | `opengauss_setup/sql/local/grant_demo_db_accounts_20260611.sql` |
| 账号与角色绑定 | 演示账号分别授予对应数据库角色 | 本轮 SQL 执行通过 |
| 安全文档 | 说明应用层角色控制与数据库级最小权限的关系 | `docs/DB_PRIVILEGE_BINDING.md` |

说明：本地绑定脚本包含数据库账号密码，因此放在 `opengauss_setup/sql/local/` 并被 `.gitignore` 排除。生产环境仍应使用正式账号、密钥管理系统和审计策略替代本地演示密码。

## 4. 本轮完成的绩点规则版本化

| 项目 | 完成情况 | 证据 |
| --- | --- | --- |
| 绩点规则表 | 新增 `grade_policy` | `migrate_grade_policy_20260611.sql` |
| 分数区间表 | 新增 `grade_scale` | `migrate_grade_policy_20260611.sql` |
| 学期绑定规则 | `semester.grade_policy_id` 外键引用 `grade_policy` | `migrate_grade_policy_20260611.sql` |
| 区间重叠防护 | `trg_grade_scale_no_overlap` | `migrate_grade_policy_20260611.sql` |
| 绩点计算函数 | `calculate_gpa(DECIMAL, BIGINT)` | `migrate_grade_policy_20260611.sql` |
| 课程成绩绩点视图 | `v_enrollment_grade_detail` | `migrate_grade_policy_20260611.sql` |
| 学期加权绩点视图 | `v_student_gpa_summary` | `migrate_grade_policy_20260611.sql` |
| 后端查询同步 | 成绩和选课查询读取绩点视图 | `services/score_service.py`、`services/course_service.py` |
| 回滚型测试 | `test_grade_policy.sql` 已运行通过 | 本轮 SQL 输出 |

该设计保持 3NF 主线：不恢复 `enrollment.gpa_point`，绩点作为规则表和视图计算结果获得。历史学期可以继续绑定原有规则版本，新学期可以绑定新的规则版本。

## 5. 本轮验证结果

| 验证项 | 结果 |
| --- | --- |
| Python 静态编译 | 通过 |
| 演示账号本地生成脚本 | 已运行 |
| 本地账号同步 SQL | 已执行通过 |
| 触发器和约束迁移 | 已执行通过 |
| 绩点规则迁移 | 已执行通过 |
| 最小权限角色脚本 | 已执行通过 |
| 演示数据库账号绑定脚本 | 已执行通过 |
| `test_grade_policy.sql` | 已运行通过 |
| `test_triggers_constraints.sql` | 已运行通过 |
| `scripts/concurrency_enrollment_test.py` | 已运行通过，结果为 `success_count = 1`、`failed_count = 1`、`selected_count_in_db = 1` |
| Mermaid 逻辑 ER 图 | 已重新生成 `report/figures/er_logical.png` |
| LaTeX 报告 | 已通过 `report/build_report.sh` 编译，输出 `report/main.pdf` |

## 6. 仍保留为后续扩展的内容

1. 教师评价打分模块仅保留为后续扩展设计，未进入主线 ER 图和数据库实现；
2. 行政班实体拆分仍是后续优化方向；
3. 生产环境真实数据库账号、密钥管理系统和审计策略仍需落地；
4. 更大规模并发压测、备份恢复、运行监控和物化视图刷新策略仍需继续完善。

## 7. 是否存在报告过度声明

本轮已核对 `report/main.tex`、第 5 章、第 8 章、第 9 章、第 10 章和附录。报告中关于触发器、事务锁、视图、同课跨班、绩点规则版本化、账号凭据策略和数据库权限脚本的“已实现”表述均能在 SQL、后端代码或测试脚本中找到证据。教师评价、生产级密钥管理、行政班实体拆分、物化视图和大规模压测仍写为后续工作。

## 8. Freeze 前仍需人工确认的事项

1. `secrets/DEMO_ACCOUNT_CREDENTIALS.md` 和 `opengauss_setup/sql/local/` 已被忽略，不应提交到公开仓库；
2. 公开仓库只应提交 `docs/DEMO_ACCOUNT_CREDENTIALS.example.md`，其中不得包含真实密码；
3. 如果教师需要复现实验环境，应运行 `scripts/generate_demo_credentials.py` 生成本地凭据；
4. 正式部署时应替换本地演示数据库账号密码，并接入生产密钥管理。
