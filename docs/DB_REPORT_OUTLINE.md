# 数据库原理2期末报告结构建议

本提纲按课堂笔记 `chapter7.md` 中的数据库系统设计流程组织，并在完整性、触发器、事务、锁、安全等章节呼应 `chapter8.md`。每章都给出可引用的项目证据，便于后续扩展成正式报告。

## 第1章 绪论与系统规划

课程知识点：

- 数据库系统规划阶段：必要性、可行性、信息范围、资源和系统目标。
- 数据库应用系统由数据库系统和应用软件两部分组成。

可写内容：

- 项目背景：面向高校课程选课、成绩管理和基础信息维护。
- 系统目标：统一管理学生、教师、课程、学期、开课班次、选课记录、成绩和日志。
- 技术选型：Python + Streamlit + openGauss + Docker。
- 当前部署：本地 Docker openGauss，应用通过 psycopg2 连接。

项目证据：

- `README.md` 的功能概览和部署说明。
- `requirements.txt` 中 `streamlit`、`psycopg2-binary`。
- `config.py` 的 openGauss 连接配置。
- `opengauss_setup/docker/docker-compose.yml` 和 `opengauss_setup/docker/init_db.sh`。

## 第2章 需求分析

课程知识点：

- 需求分析阶段输出数据需求、处理需求和数据字典。
- 外部实体、数据流、处理过程和数据存储。

可写内容：

- 用户角色：学生、教师、管理员。
- 学生处理需求：登录、查询可选课程、选课、退课、查看成绩单。
- 教师处理需求：查看负责班次、录入成绩、查看成绩分布和修改日志。
- 管理员处理需求：学期、课程、开课班次、学生、教师、成绩的维护。
- 数据需求：组织结构、用户身份、教学安排、选课成绩、审计日志。
- 业务规则：容量、重复选课、选课窗口、先修课、退课限制、成绩权限。

项目证据：

- `app.py` 中 `_NAV` 定义三类角色页面。
- `pages/_guards.py` 的 `require_role()`。
- `services/selection_service.py` 的 `enroll()`、`drop()`。
- `services/score_service.py` 的 `can_manage_offering_score()`、`update_score()`。
- `README.md` 的功能表。

## 第3章 概念结构设计

课程知识点：

- 概念设计独立于 DBMS。
- ER 模型中实体、属性、联系和基数。
- 局部 ER 集成为全局 ER，消除命名、属性和结构冲突。

可写内容：

- 识别实体：学生、教师、管理员、用户账号、院系、专业、课程、学期、教室、开课班次、选课记录、先修关系、成绩日志。
- 重点说明“课程”和“开课班次”的分离。
- 学生与开课班次是 M:N，通过选课记录实体转换。
- 课程与课程之间存在自关联，用于先修课。
- 用户账号与学生/教师/管理员资料为 1:1。

项目证据：

- `opengauss_setup/sql/init.sql` 中 `CREATE TABLE course`、`course_offering`、`enrollment`、`course_prerequisite`。
- `ER_RELATIONAL_MODEL_DRAFT.md` 中 Mermaid ER 图草案。

## 第4章 逻辑结构设计

课程知识点：

- ER 模型向关系模型转换。
- 实体转换为关系，1:N 联系通过外键实现，M:N 联系转换为中间关系。
- 主键、外键、候选键和参照完整性。

可写内容：

- 列出所有主要关系模式。
- 说明每张表主键、外键和唯一约束。
- 说明 `enrollment` 是学生和开课班次 M:N 的关系表。
- 说明 `course_prerequisite` 是课程自关联 M:N 的关系表。
- 说明 `user_account` 与资料表分离支持统一登录。

项目证据：

- `opengauss_setup/sql/init.sql` 第 19-208 行的表结构。
- `ER_RELATIONAL_MODEL_DRAFT.md` 的关系模式表。

## 第5章 规范化设计与范式分析

课程知识点：

- 1NF：属性原子性。
- 2NF：非主属性完全函数依赖于候选键。
- 3NF：消除非主属性对候选键的传递依赖。
- BCNF：每个非平凡函数依赖的决定因素都是候选键。

可写内容：

- 核心表大多以单属性主键组织，2NF 基础较好。
- `course` 与 `course_offering` 分离体现规范化，避免课程基本信息在每个教学班中重复。
- `enrollment` 承载学生与教学班联系的属性，避免把成绩写入学生表或课程表。
- `course_prerequisite` 只有复合键，没有非主属性，适合作为 BCNF 示例。
- 指出 `schedule_text` 不够原子化，建议拆 `course_schedule`。
- 指出 `selected_count` 和 `gpa_point` 是反规范化或派生字段，需要触发器或事务维护。
- 对 BCNF 判断保持谨慎，例如 `classroom` 的 `(building, room_no)` 是否为候选键需要业务语义确认。

项目证据：

- `NORMALIZATION_AUDIT.md` 的逐表分析。
- `opengauss_setup/sql/init.sql` 中 `course_offering.schedule_text`、`selected_count`、`enrollment.gpa_point`。

## 第6章 数据库完整性约束与触发器设计

课程知识点：

- 数据库完整性：正确性和相容性。
- 域完整性、实体完整性、参照完整性、用户定义完整性。
- SQL 主键、外键、NOT NULL、UNIQUE、CHECK、DEFAULT。
- 触发器作为主动规则，体现事件、条件、动作。

可写内容：

- 主键保证实体完整性。
- 外键保证院系、专业、课程、教师、开课班次、选课记录之间的参照完整性。
- CHECK 保证角色、状态、性别、学分、学时、容量、成绩和绩点范围。
- `UNIQUE(student_id, offering_id)` 防止同一学生重复选择同一教学班。
- `trg_enrollment_insert` 和 `trg_enrollment_update` 维护 `selected_count`。
- 应用层规则和数据库层规则的分工。
- 未实现的触发器建议：容量检查、时间冲突检查、成绩变动自动日志。

项目证据：

- `opengauss_setup/sql/init.sql` 中约束定义和触发器函数。
- `services/selection_service.py` 的选退课校验。
- `services/score_service.py` 的成绩校验和日志写入。
- `CONSTRAINT_TRIGGER_TRANSACTION_AUDIT.md`。

## 第7章 事务管理、锁机制与并发控制

课程知识点：

- 事务 ACID：原子性、一致性、隔离性、持久性。
- 并发问题：丢失更新、脏读、不可重复读、幻读。
- 封锁：共享锁、排他锁、封锁粒度。
- 两段锁和可串行化调度。

可写内容：

- `DBSession` 提供基本 commit/rollback。
- 学生/教师新增使用单事务插入账号和资料，体现原子性。
- 当前选课容量检查与插入不在同一事务，缺少 `SELECT ... FOR UPDATE`，存在并发超选风险。
- 唯一约束可防止重复同一教学班，但不能解决容量并发。
- 成绩更新和日志写入分两步执行，建议放入同一事务。
- 设计改进：对 `course_offering` 行加排他锁，或使用原子条件更新；严格遵循两段锁思想。

项目证据：

- `db/connection.py` 的 `DBSession`。
- `services/student_service.py`、`services/teacher_service.py` 的新增事务。
- `services/selection_service.py` 的多次独立 `query_one/execute`。
- `services/score_service.py` 的 `update_score()`。
- `CONSTRAINT_TRIGGER_TRANSACTION_AUDIT.md`。

## 第8章 物理结构设计与性能优化

课程知识点：

- 物理设计确定存储结构和存取方法。
- 索引是重要的存取路径设计。
- 物理设计需要结合高频查询和 DBMS 特性。

可写内容：

- openGauss 数据类型选择：`BIGSERIAL`、`VARCHAR`、`DECIMAL`、`DATE`、`TIMESTAMP`、`TEXT`。
- 主键和唯一约束隐式建立索引。
- 当前显式索引主要集中在 `user_session`。
- 高频查询需要补充组合索引。
- 查询优化：学生可选课程、班次名单、成绩分布、成绩日志、管理员统计。
- `selected_count` 是为减少统计开销而保留的冗余字段。
- 备份恢复建议：定期逻辑备份，初始化脚本与样本数据分离。

项目证据：

- `opengauss_setup/sql/init.sql` 的数据类型和 `CREATE INDEX`。
- `services/course_service.py`、`services/score_service.py` 的 JOIN 查询。
- `opengauss_setup/schema_query_optimization.md`。

## 第9章 系统运行、维护与安全管理

课程知识点：

- 运行维护任务：安全性、完整性、性能监测、功能扩展、错误修正。
- 数据库恢复：转储、日志、检查点、UNDO/REDO。
- 数据库安全：身份鉴别、权限控制、访问控制。

可写内容：

- Docker openGauss 初始化和运行流程。
- 应用层角色权限与页面访问控制。
- 登录会话通过 token 哈希存储，退出登录撤销会话。
- 成绩修改日志支持审计。
- 当前未实现数据库级细粒度授权，后续可设计只读用户、业务写用户和 DBA 用户。
- 当前缺少备份恢复脚本，后续可设计定期 `gs_dump` 备份和恢复演练。
- 运行维护还可增加慢查询监控、日志归档和数据生命周期管理。

项目证据：

- `opengauss_setup/docker/start_opengauss.sh`、`init_db.sh`。
- `services/auth_service.py`。
- `score_change_log` 表和 `services/score_service.py`。

## 第10章 总结与不足

课程知识点：

- 对数据库设计流程的回顾。
- 对规范化、完整性、事务、物理优化的综合评价。

可写内容：

- 当前系统已经具备完整的选课核心数据模型。
- 规范化方面，课程、开课班次、选课记录分离较好。
- 完整性方面，主键、外键、CHECK、UNIQUE 和触发器有较完整证据。
- 不足集中在并发控制、时间冲突、索引和数据库权限。
- 后续改进优先级：选课事务锁、结构化课程时间、索引与审计增强。

项目证据：

- 汇总引用前九章证据。
- 可附录 Mermaid ER 图、关系模式表、约束清单和事务伪代码。

## 可作为附录的内容

- 附录 A：Mermaid ER 图。
- 附录 B：主要关系模式、主键和外键表。
- 附录 C：范式分析表。
- 附录 D：约束、触发器和事务改进伪代码。
- 附录 E：关键 SQL 和关键 service 函数摘录。
