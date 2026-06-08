# 约束、触发器、事务与锁机制审计

本文档用于期末报告中“完整性约束与触发器设计”“事务管理、锁机制与并发控制”两章。分析依据为 `opengauss_setup/sql/init.sql`、`db/connection.py` 和 `services/*.py`。

> 2026-06-08 更新：为提高 3NF 程度，当前基础表已删除 `course_offering.selected_count` 和 `enrollment.gpa_point`，并新增 `course_schedule`。旧文中关于 `selected_count` 触发器维护的内容可作为“旧版实现与重构前问题”材料；当前实现中已选人数由查询聚合得到，时间冲突由 `services/selection_service.py` 基于 `course_schedule` 检查，选课流程已使用 `DBSession` 和 `SELECT ... FOR UPDATE` 锁定目标开课班次。

## 1. 数据库层完整性约束

### 1.1 主键约束

当前所有核心表均设置主键，保证实体完整性。

| 表 | 主键 |
|---|---|
| `department` | `dept_id` |
| `major` | `major_id` |
| `user_account` | `user_id` |
| `user_session` | `session_id` |
| `student` | `student_id` |
| `teacher` | `teacher_id` |
| `admin_profile` | `admin_id` |
| `semester` | `semester_id` |
| `course` | `course_id` |
| `classroom` | `classroom_id` |
| `course_offering` | `offering_id` |
| `course_prerequisite` | `(course_id, prereq_course_id)` |
| `enrollment` | `enrollment_id` |
| `score_change_log` | `log_id` |

报告写法：

> 主键约束用于保证元组的唯一性和实体完整性。例如 `student.student_id` 唯一标识学生，`course_offering.offering_id` 唯一标识某一学期某教师开设的教学班，`enrollment.enrollment_id` 唯一标识一次选课事实。

### 1.2 外键约束

参照完整性主要由外键维护。

| 表 | 外键 | 作用 |
|---|---|---|
| `major` | `dept_id -> department(dept_id)` | 专业必须属于已有院系。 |
| `student` | `user_id -> user_account(user_id)` | 学生资料关联登录账号。 |
| `student` | `major_id -> major(major_id)` | 学生专业必须存在。 |
| `teacher` | `user_id -> user_account(user_id)` | 教师资料关联登录账号。 |
| `teacher` | `dept_id -> department(dept_id)` | 教师院系必须存在。 |
| `admin_profile` | `user_id -> user_account(user_id)` | 管理员资料关联登录账号。 |
| `user_session` | `user_id -> user_account(user_id) ON DELETE CASCADE` | 删除账号时自动删除会话。 |
| `course` | `dept_id -> department(dept_id)` | 课程开课院系必须存在。 |
| `course_offering` | `course_id -> course(course_id)` | 教学班必须对应已有课程。 |
| `course_offering` | `semester_id -> semester(semester_id)` | 教学班必须归属已有学期。 |
| `course_offering` | `teacher_id -> teacher(teacher_id)` | 教学班必须由已有教师承担。 |
| `course_offering` | `classroom_id -> classroom(classroom_id)` | 教学班教室必须存在。 |
| `course_prerequisite` | `course_id/prereq_course_id -> course(course_id)` | 先修关系两端都必须是已有课程。 |
| `enrollment` | `student_id -> student(student_id)` | 选课记录必须属于已有学生。 |
| `enrollment` | `offering_id -> course_offering(offering_id)` | 选课记录必须属于已有教学班。 |
| `score_change_log` | `enrollment_id -> enrollment(enrollment_id)` | 成绩日志必须对应已有选课记录。 |
| `score_change_log` | `changed_by_user_id -> user_account(user_id)` | 日志操作人必须是已有账号。 |

当前除 `user_session` 外，大多数外键未设置级联删除，默认行为会限制删除被引用数据。这适合选课系统保护历史记录。

### 1.3 UNIQUE 约束

| 约束 | 作用 |
|---|---|
| `uq_username` | 登录用户名唯一。 |
| `uq_user_session_token` | 会话 token 哈希唯一。 |
| `uq_student_user` | 一个账号最多对应一个学生资料。 |
| `uq_teacher_user` | 一个账号最多对应一个教师资料。 |
| `uq_admin_user` | 一个账号最多对应一个管理员资料。 |
| `uq_student_offering` | 一个学生不能重复选择同一个教学班。 |

重点：

- `uq_student_offering` 是防止重复选课的数据库级约束。
- 它只能限制同一 `offering_id`，不能限制同一学生同一学期选择同一课程的不同教学班。

### 1.4 NOT NULL 和 DEFAULT

典型 NOT NULL：

- 各表主键字段。
- 账号表 `username/password_hash/role/status/created_at`。
- 学期 `start_date/end_date/status`。
- 课程 `course_name/course_type/credit/total_hours/status`。
- 开课班次 `course_id/semester_id/teacher_id/max_capacity/selected_count/status`。
- 选课记录 `student_id/offering_id/select_time/status`。

典型 DEFAULT：

- `user_account.status DEFAULT 'active'`。
- `user_account.created_at DEFAULT CURRENT_TIMESTAMP`。
- `user_session.created_at DEFAULT CURRENT_TIMESTAMP`。
- `student.status DEFAULT 'enrolled'`。
- `teacher.status DEFAULT 'active'`。
- `semester.status DEFAULT 'planned'`。
- `course.course_type DEFAULT 'required'`。
- `course.status DEFAULT 'active'`。
- `course_offering.max_capacity DEFAULT 60`。
- `course_offering.selected_count DEFAULT 0`。
- `course_offering.status DEFAULT 'open'`。
- `enrollment.select_time DEFAULT CURRENT_TIMESTAMP`。
- `enrollment.status DEFAULT 'selected'`。
- `score_change_log.changed_at DEFAULT CURRENT_TIMESTAMP`。

### 1.5 CHECK 约束

| 表 | CHECK | 作用 |
|---|---|---|
| `user_account` | `role IN ('admin','student','teacher')` | 限定角色域。 |
| `user_account` | `status IN ('active','disabled')` | 限定账号状态。 |
| `student` | `gender IS NULL OR gender IN ('M','F','O')` | 限定性别值。 |
| `student` | `status IN ('enrolled','suspended','graduated','dropped')` | 限定学生状态。 |
| `teacher` | `gender IS NULL OR gender IN ('M','F','O')` | 限定性别值。 |
| `teacher` | `status IN ('active','retired','leave')` | 限定教师状态。 |
| `semester` | `status IN ('planned','open','closed')` | 限定学期状态。 |
| `course` | `course_type IN ('required','elective','public')` | 限定课程类型。 |
| `course` | `status IN ('active','inactive')` | 限定课程状态。 |
| `course` | `credit > 0` | 学分必须合法。 |
| `course` | `total_hours > 0` | 学时必须合法。 |
| `classroom` | `capacity > 0` | 教室容量必须为正。 |
| `course_offering` | `status IN ('open','closed','cancelled')` | 限定班次状态。 |
| `course_offering` | `max_capacity > 0` | 班次容量必须为正。 |
| `course_offering` | `selected_count >= 0` | 已选人数不能为负。 |
| `enrollment` | `status IN ('selected','dropped','completed')` | 限定选课状态。 |
| `enrollment` | `final_score IS NULL OR final_score BETWEEN 0 AND 100` | 成绩范围合法。 |
| `enrollment` | `gpa_point IS NULL OR gpa_point BETWEEN 0 AND 5` | 绩点范围合法。 |

尚未实现但可补充的 CHECK：

- `semester.start_date <= semester.end_date`。
- `semester.selection_start <= semester.selection_end`。
- `course_offering.selected_count <= course_offering.max_capacity`。
- `course_prerequisite.course_id <> course_prerequisite.prereq_course_id`。

注意：

- `course_offering.max_capacity <= classroom.capacity` 需要跨表检查，普通 CHECK 不能完成，应通过触发器或应用层事务实现。

## 2. 触发器分析

### 2.1 已实现触发器

当前 SQL 实现了两个触发器函数和两个触发器：

1. `trg_enrollment_insert_fn()`：
   - 事件：`AFTER INSERT ON enrollment`。
   - 条件：`NEW.status = 'selected'`。
   - 动作：将对应 `course_offering.selected_count` 加 1。

2. `trg_enrollment_update_fn()`：
   - 事件：`AFTER UPDATE ON enrollment`。
   - 条件 1：`OLD.status = 'selected' AND NEW.status = 'dropped'`。
   - 动作 1：将对应 `selected_count` 减 1，并用 `GREATEST(..., 0)` 防止负数。
   - 条件 2：`OLD.status = 'dropped' AND NEW.status = 'selected'`。
   - 动作 2：将对应 `selected_count` 加 1。

课程知识点对应：

- 触发器体现 SQL 主动规则，符合课堂笔记中的 ECA 结构：事件、条件、动作。
- 触发时间为 `AFTER`，触发粒度为 `FOR EACH ROW`。

报告写法：

> 系统将“已选人数维护”设计为数据库触发器，而不是完全依赖应用层手工更新。这样无论选课记录由哪个应用入口插入或更新，只要修改 `enrollment` 表，数据库都能自动维护 `course_offering.selected_count`，体现了完整性规则由 DBMS 统一管理的思想。

### 2.2 触发器覆盖不足

当前触发器未覆盖：

- `INSERT enrollment` 且状态为 `completed` 时是否应计入人数。当前不计入。
- `selected -> completed` 是否应改变 `selected_count`。当前不改变。
- `DELETE enrollment` 时是否应减少 `selected_count`。当前没有 DELETE 触发器。
- 容量上限检查。当前触发器只加减人数，不阻止超容量。
- 时间冲突检查。
- 先修课检查。
- 成绩修改日志自动写入。

这些不是一定错误，但需要在报告中明确 `selected_count` 的业务语义：

- 如果 `selected_count` 表示“当前占用容量的已选人数”，则 `selected` 计数、`dropped` 不计数、`completed` 是否计数需要根据业务解释。
- 当前样本数据中历史 `completed` 记录不会增加 `selected_count`，这更接近“当前开放班次占用名额”的语义。

### 2.3 可加入报告的触发器设计建议

容量检查触发器：

```sql
CREATE OR REPLACE FUNCTION trg_check_enrollment_capacity_fn()
RETURNS TRIGGER AS $$
DECLARE
    v_max INTEGER;
    v_selected INTEGER;
BEGIN
    IF NEW.status = 'selected' THEN
        SELECT max_capacity, selected_count
        INTO v_max, v_selected
        FROM course_offering
        WHERE offering_id = NEW.offering_id
        FOR UPDATE;

        IF v_selected >= v_max THEN
            RAISE EXCEPTION 'course offering is full';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

时间冲突触发器的前提：

- 先拆 `course_schedule(offering_id, weekday, start_section, end_section)`。
- 插入选课时查询该学生已选课程的时间片是否重叠。

成绩日志触发器：

- 监听 `enrollment.final_score` 更新。
- 当 `OLD.final_score IS DISTINCT FROM NEW.final_score` 时写入 `score_change_log`。
- 需要解决操作人 `changed_by_user_id` 的传入问题，可由应用设置会话变量，或继续应用层写日志但放入同一事务。

## 3. 应用层校验分析

### 3.1 选课校验

`services/selection_service.py` 的 `enroll()` 实现：

- 查询是否已有 `enrollment`。
- 若已选，拒绝重复选择同一教学班。
- 若已结课，拒绝重复选择同一班次。
- 若是已退课记录，允许在满足条件时恢复选课。
- 检查学期状态必须为 `open`。
- 检查教学班状态必须为 `open`。
- 检查当前时间在 `selection_start` 和 `selection_end` 之间。
- 检查 `selected_count < max_capacity`。
- 调用 `_has_passed_prerequisites()` 检查先修课是否通过。
- 插入 `enrollment` 或把 `dropped` 更新回 `selected`。

### 3.2 退课校验

`drop()` 实现：

- 选课记录必须存在。
- 只能退自己的课。
- 状态必须为 `selected`。
- `final_score IS NOT NULL` 时不能退课。
- 学期必须开放。
- 当前时间必须在选退课窗口内。
- 更新状态为 `dropped`。

### 3.3 成绩校验

`services/score_service.py` 的 `update_score()` 实现：

- 管理员可维护任意班次。
- 教师只能维护自己负责的班次。
- 退课记录不能录入成绩。
- 成绩不能为空，且必须在 0 到 100。
- 根据 `calc_gpa()` 计算绩点。
- 更新 `enrollment` 的成绩、绩点和状态。
- 插入 `score_change_log`。

### 3.4 删除校验

| 函数 | 规则 | 状态 |
|---|---|---|
| `delete_course()` | 课程已有开课安排时拒绝删除。 | 已实现，应用层。 |
| `delete_offering()` | 班次已有选课或成绩记录时拒绝删除。 | 已实现，应用层。 |
| `delete_teacher()` | 教师已有开课记录时拒绝删除。 | 已实现，应用层。 |
| `delete_student()` | 直接删除学生和账号，若有选课记录会被外键阻止。 | 部分实现，建议先查询并给出友好提示。 |

## 4. 尚未实现的关键检查机制

| 检查机制 | 当前状态 | 风险 | 建议 |
|---|---|---|---|
| 时间冲突检查 | 未实现 | 学生可选择同一时间上课的不同班次。 | 拆 `course_schedule` 并检查时间段重叠。 |
| 容量数据库级强约束 | 未实现 | 并发抢课可能超选。 | `SELECT ... FOR UPDATE` 或 BEFORE 触发器。 |
| 同课跨班重复限制 | 未实现 | 同一学生可选同一学期同一课程不同班次。 | 触发器或冗余字段加唯一约束。 |
| 先修环路检查 | 未实现 | 可能出现 A 先修 B、B 先修 A。 | 递归查询或管理端校验。 |
| 教室容量约束 | 未实现 | 教学班容量可能大于教室容量。 | 触发器或开课保存时应用层校验。 |
| 成绩日志事务原子性 | 部分实现 | 成绩已更新但日志写入失败。 | 使用同一 `DBSession` 或触发器。 |

## 5. 当前事务实现

### 5.1 DBSession

`db/connection.py` 中 `DBSession` 是事务上下文：

- 进入上下文时打开连接。
- 正常退出时 `commit()`。
- 发生异常时 `rollback()`。
- 最后关闭连接。

这体现了事务 ACID 中的原子性和持久性基础。

### 5.2 已正确使用单事务的地方

`create_student()`：

- 插入 `user_account`。
- 获取 `RETURNING user_id`。
- 插入 `student`。
- 两步在同一个 `DBSession` 中执行。
- 如果学生资料插入失败，账号插入也会回滚。

`create_teacher()` 同理。

这适合在报告中作为“事务原子性”的正面示例。

### 5.3 事务不足的地方

`enroll()`：

- 查询已有选课、查询容量和开放时间、查询先修课、插入选课分别通过 `query_one()` 和 `execute()` 完成。
- 每个调用都会打开新的 `DBSession`，形成独立事务。
- 缺少 `SELECT ... FOR UPDATE`。

风险：

- 两个学生同时读取 `selected_count = max_capacity - 1`。
- 两个事务都判断容量足够。
- 两个事务都插入成功。
- 触发器各自把 `selected_count` 加 1，最终超出容量。

`update_score()`：

- 第一步更新 `enrollment`。
- 第二步插入 `score_change_log`。
- 两步不是同一个事务。
- 如果第二步失败，审计日志缺失。

`delete_course()`：

- 先查是否存在开课安排，再删除先修关系和课程。
- 查询和删除之间可能发生并发插入开课安排。

## 6. 并发控制风险分析

### 6.1 多学生同时抢一门课

风险类型：

- 丢失更新或超选。
- 不满足隔离性。
- 并发调度结果不等价于任何合理串行调度。

当前保护：

- 唯一约束防止同一学生重复插入同一教学班。
- 触发器自动增加 `selected_count`。

不足：

- 容量检查不是锁保护下的检查。
- 没有原子条件更新。
- 没有显式事务隔离级别。

### 6.2 只剩 1 个名额时的并发选课

典型错误调度：

1. T1 读取 `selected_count=39, max_capacity=40`。
2. T2 读取 `selected_count=39, max_capacity=40`。
3. T1 插入选课，触发器加到 40。
4. T2 插入选课，触发器加到 41。
5. 最终超选。

适合报告写法：

> 当前实现能保证单用户流程正确，但在高并发抢课场景下，容量检查和写入操作不具备同一事务中的隔离性。根据课堂中封锁和两段锁理论，应在读取容量时对目标 `course_offering` 元组加排他锁，并在事务提交后释放，保证并发选课调度等价于某个串行调度。

### 6.3 学生多窗口同时提交选课

保护：

- `UNIQUE(student_id, offering_id)` 能防止同一教学班重复插入。

仍需补充：

- 如果两个窗口选择同一课程的不同教学班，当前不会阻止。
- 如果两个窗口恢复同一 dropped 记录，可能重复触发状态更新，需要在事务中重新读取状态。

### 6.4 管理员修改容量时学生正在选课

当前风险：

- `update_offering()` 可更新 `max_capacity`，但没有检查新容量是否小于当前 `selected_count`。
- UI 层可能限制输入不低于当前已选人数，但数据库层和 service 层未强制。
- 并发选课时容量可能在读取后被修改。

建议：

- `CHECK(max_capacity >= selected_count)`。
- 更新容量时对 `course_offering` 行加锁。
- 若降低容量，必须保证 `new_capacity >= selected_count`。

### 6.5 教师录入成绩时学生退课

当前保护：

- 退课检查 `final_score IS NOT NULL`。
- 成绩录入检查 `status != 'dropped'`。

并发风险：

- 教师读取状态为 selected 后，学生退课成功。
- 教师随后更新成绩，把退课记录改成 completed。

建议：

- 成绩更新时 `SELECT enrollment ... FOR UPDATE`。
- 退课时也锁定对应 `enrollment` 行。
- 成绩更新 SQL 增加条件：`WHERE enrollment_id=%s AND status != 'dropped'`，并检查受影响行数。

## 7. 推荐事务设计方案

### 7.1 选课事务方案

伪代码：

```python
def enroll(student_id, offering_id):
    with DBSession() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT co.max_capacity, co.selected_count, co.status,
                       s.selection_start, s.selection_end, s.status AS semester_status
                FROM course_offering co
                JOIN semester s ON co.semester_id = s.semester_id
                WHERE co.offering_id = %s
                FOR UPDATE
            """, (offering_id,))
            offering = cur.fetchone()

            # 在同一事务中检查开放状态、时间窗口、容量、已有选课、先修课
            # 插入 enrollment 或恢复 dropped
```

锁机制解释：

- `FOR UPDATE` 对目标教学班记录加行级排他锁。
- 其他并发选课事务必须等待该事务提交或回滚。
- 锁粒度为 `course_offering` 的单行，兼顾一致性和并发度。
- 该方案符合两段锁思想：先获得锁，完成检查和写入后在事务结束时释放锁。

### 7.2 原子条件更新方案

另一种方案：

```sql
UPDATE course_offering
SET selected_count = selected_count + 1
WHERE offering_id = ?
  AND status = 'open'
  AND selected_count < max_capacity;
```

然后检查更新行数：

- 若更新 1 行，说明抢到名额，再插入 `enrollment`。
- 若更新 0 行，说明已满或班次关闭。

注意：

- 如果继续保留 enrollment 触发器维护 `selected_count`，就不能再由应用层直接加人数，否则会重复加。需要二选一：
  - 保留触发器：用 `FOR UPDATE` 检查容量，不手动更新人数。
  - 改为原子更新：取消或调整人数触发器。

### 7.3 成绩更新事务方案

伪代码：

```python
with DBSession() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT final_score, status, offering_id
            FROM enrollment
            WHERE enrollment_id = %s
            FOR UPDATE
        """, (enrollment_id,))
        # 权限检查、状态检查、成绩范围检查
        cur.execute("""
            UPDATE enrollment
            SET final_score=%s, gpa_point=%s, status='completed'
            WHERE enrollment_id=%s
        """, ...)
        cur.execute("""
            INSERT INTO score_change_log (...)
            VALUES (...)
        """, ...)
```

好处：

- 成绩和日志具有原子性。
- 退课和成绩录入不能并发覆盖。

## 8. 可写入报告的课程知识点对应

| 课程知识点 | 项目体现 | 当前评价 |
|---|---|---|
| 实体完整性 | 所有表主键 | 已实现。 |
| 参照完整性 | 外键关联院系、专业、用户、课程、班次、选课记录 | 已实现。 |
| 用户定义完整性 | CHECK、UNIQUE、默认值、应用层业务规则 | 已部分实现。 |
| 触发器 ECA | enrollment 插入/更新维护 selected_count | 已实现，适合重点展示。 |
| 事务原子性 | DBSession；新增学生/教师账号资料同事务 | 部分实现。 |
| 并发隔离性 | 选课尚未使用锁 | 是主要不足。 |
| 封锁机制 | 可设计 `FOR UPDATE` 行级锁 | 可作为理论设计和后续改进。 |
| 两段锁 | 选课事务先加锁、检查、插入、提交释放 | 可作为报告设计方案。 |
| 安全性 | 应用层角色权限、会话撤销 | 已实现应用层，数据库层不足。 |
| 恢复与维护 | Docker 初始化；缺少备份恢复脚本 | 需要补充说明。 |
