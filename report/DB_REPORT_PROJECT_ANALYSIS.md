# 项目数据库设计分析

## 1. 数据库相关文件清单

| 文件或目录 | 作用 | 报告章节支撑 |
|---|---|---|
| `opengauss_setup/sql/init.sql` | 当前 openGauss 主建表脚本，包含 14 张主要表、主键、外键、唯一约束、CHECK、默认值、索引和样例数据 | 第3-8章 |
| `opengauss_setup/sql/migrate_3nf_20260608.sql` | 旧结构迁移到 3NF 结构的脚本，删除 `selected_count`、`schedule_text`、`gpa_point`，新增 `course_schedule` | 第5章、第8章 |
| `opengauss_setup/sql/add_user_session.sql` | 旧库补充 `user_session` 的脚本 | 第9章 |
| `opengauss_setup/docker/*.sh`、`docker-compose.yml` | Docker openGauss 启动、重建库和导入脚本 | 第8-9章 |
| `config.py` | openGauss 连接参数 | 第1章、第8章 |
| `db/connection.py` | psycopg2 连接、`DBSession` 事务封装、查询执行工具 | 第7章 |
| `services/course_service.py` | 学期、课程、教学班 CRUD；时间片解析；动态人数、时间文本、绩点查询 | 第2-8章 |
| `services/selection_service.py` | 选课、退课、容量、先修课、时间冲突、事务和 `FOR UPDATE` | 第6-7章 |
| `services/score_service.py` | 成绩录入、绩点动态计算、成绩日志、教师权限检查 | 第6-9章 |
| `services/auth_service.py`、`utils/auth_cookie.py` | 登录、会话、角色身份 | 第2章、第9章 |
| `pages/*.py` | 角色页面，体现应用层权限和交互入口 | 第2章、第9章 |
| `README.md` | 项目功能、数据库表和部署说明 | 第1章、第9章 |

项目没有 ORM 模型，也没有 Alembic 等 migration 框架。数据库模式以 SQL 脚本维护。

## 2. 当前真实实现摘要

当前数据库为 openGauss，核心表包括 `department`、`major`、`user_account`、`user_session`、`student`、`teacher`、`admin_profile`、`semester`、`course`、`classroom`、`course_offering`、`course_schedule`、`course_prerequisite`、`enrollment`、`score_change_log`。

当前已经完成 3NF 方向重构：

- `course_offering.schedule_text` 已删除，上课时间由 `course_schedule` 结构化保存。
- `course_offering.selected_count` 已删除，已选人数由 `enrollment` 聚合计算。
- `enrollment.gpa_point` 已删除，绩点由 `final_score` 动态计算。
- `selection_service.enroll()` 使用 `DBSession` 和 `SELECT ... FOR UPDATE` 锁定目标开课班次。

## 3. 实现与报告内容对应

- 第2章需求分析：可引用 `README.md`、`pages/*.py`、`services/*.py`。
- 第3章概念设计：可引用 `init.sql` 的表结构和 `report/diagrams/er_conceptual.mmd`。
- 第4章逻辑设计：可引用主键、外键、唯一约束和 `report/diagrams/er_logical.mmd`。
- 第5章规范化：重点引用 `course_schedule`、删除派生字段和 `docs/THIRD_NORMAL_FORM_REFACTOR.md`。
- 第6章完整性：引用 `init.sql` 中 PK/FK/UNIQUE/CHECK/DEFAULT，以及服务层检查。
- 第7章事务锁：引用 `db/connection.py` 和 `services/selection_service.py`。
- 第8章物理设计：引用索引定义、数据类型和 Docker openGauss。
- 第9章运行维护：引用 Docker 脚本、会话表、日志表和权限实现。

## 4. 不能虚构的部分

当前数据库没有实现触发器；数据库级角色权限也没有细分；成绩更新和成绩日志尚未合并到同一事务；同课跨班重复限制、教室容量强约束尚未完全实现。这些内容只能作为设计方案或后续改进。
