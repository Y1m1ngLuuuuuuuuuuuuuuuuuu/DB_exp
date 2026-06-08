# openGauss 模式设计与查询优化建议

生成时间：2026-05-11  
基线快照：`snapshot/opengauss-before-optimization-20260511` / `cd8d6ea`  
范围：基于当前 openGauss 迁移版代码和 `opengauss_setup/sql/init.sql` 做设计评审，不直接修改业务代码。

更新说明：2026-06-08 已执行 3NF 方向重构，新增 `course_schedule`，删除 `course_offering.selected_count`、`course_offering.schedule_text` 和 `enrollment.gpa_point`。本文中关于这些字段的建议可视为旧版设计评审记录；当前结构以 `opengauss_setup/sql/init.sql` 和 `docs/THIRD_NORMAL_FORM_REFACTOR.md` 为准。


## 当前结论项目当前表结构已经能支撑选课系统的核心流程，主键、唯一约束、外键和 `CHECK` 约束也比较完整。下一步优化的重点不是继续拆表，而是补充访问路径、明确冗余字段语义、把关键写流程放进事务，并改写几条会随着数据量增长变慢的查询。

建议优先级：

1. 给外键、状态过滤、排序字段补二级索引。
2. 将选课、退课、成绩录入的多步写操作放进同一个事务。

3. 明确 `course_offering.selected_count` 的语义，并让触发器覆盖所有会改变人数的状态迁移。
4. 改写 `NOT IN`、多次统计查询、成绩分布查询等热点 SQL。
5. 再考虑更大的模式设计升级，例如课程时间表规范化、重修规则建模、码表化状态字段。
## 一、模式设计优化

### 1. 为外键列补索引

openGauss 会为主键和唯一约束创建索引，但不会自动为所有外键列创建匹配索引。当前大量查询都通过外键关联表，如果后续数据增加，缺少索引会让 JOIN、删除前检查、日志查询变慢。

建议新增：

```sql
CREATE INDEX idx_major_dept ON major (dept_id);

CREATE INDEX idx_student_major ON student (major_id);
CREATE INDEX idx_teacher_dept ON teacher (dept_id);
CREATE INDEX idx_course_dept ON course (dept_id);
CREATE INDEX idx_offering_course ON course_offering (course_id);
CREATE INDEX idx_offering_semester ON course_offering (semester_id);

CREATE INDEX idx_offering_teacher ON course_offering (teacher_id);
CREATE INDEX idx_offering_classroom ON course_offering (classroom_id);
CREATE INDEX idx_enrollment_offering ON enrollment (offering_id);
CREATE INDEX idx_prereq_prereq_course ON course_prerequisite (prereq_course_id);

CREATE INDEX idx_score_log_enrollment ON score_change_log (enrollment_id);
CREATE INDEX idx_score_log_changed_by ON score_change_log (changed_by_user_id);
```
说明：`student.user_id`、`teacher.user_id`、`admin_profile.user_id`、`user_account.username` 已经有唯一约束，不需要重复建普通索引。


### 2. 为业务高频筛选建立组合索引

单列外键索引能改善 JOIN，但很多业务查询还有固定筛选条件和排序。组合索引更贴合页面访问模式。

建议新增：

```sql
CREATE INDEX idx_student_status_id ON student (status, student_id);
CREATE INDEX idx_teacher_status_id ON teacher (status, teacher_id);
CREATE INDEX idx_course_status_id ON course (status, course_id);

CREATE INDEX idx_semester_status_start ON semester (status, start_date DESC);

CREATE INDEX idx_offering_semester_status_course
    ON course_offering (semester_id, status, course_id, offering_id);

CREATE INDEX idx_offering_teacher_semester
    ON course_offering (teacher_id, semester_id, offering_id);

CREATE INDEX idx_enrollment_student_status_offering
    ON enrollment (student_id, status, offering_id);

CREATE INDEX idx_enrollment_offering_status_student
    ON enrollment (offering_id, status, student_id);

CREATE INDEX idx_enrollment_student_status_score
    ON enrollment (student_id, status, final_score);

CREATE INDEX idx_score_log_changed_at
    ON score_change_log (changed_at DESC);
```

对应热点：

- 学生端可选课程、已选课程。
- 教师端按教师查询班次。
- 成绩管理按 `offering_id` 拉学生名单。
- 成绩单按学生和完成状态过滤。
- 成绩修改日志按时间倒序取最近记录。

### 3. 明确 `selected_count` 的业务语义

当前 `selected_count` 是冗余计数字段，由触发器维护。它的优点是查询班次余量很快；风险是语义不够明确。

当前触发器行为：

- `INSERT enrollment` 且状态为 `selected` 时加 1。
- `selected -> dropped` 时减 1。
- `dropped -> selected` 时加 1。
- `selected -> completed` 不变。
- `completed` 初始插入不加 1。

这会产生一个问题：历史已完成课程的 `selected_count` 可能不能代表实际修读人数。如果 `selected_count` 只表示“当前已选占用名额”，那 `selected -> completed` 是否要减 1 需要明确；如果它表示“班次总修读人数”，那初始插入 `completed` 也应该计数。

建议二选一：

方案 A：保留为容量占用人数。

```sql
-- 只统计仍占用选课容量的 selected 状态。
-- completed/dropped 不占用容量。
```

方案 B：改名或重新定义为班次人数。

```sql
-- selected/completed 都算班次人数，dropped 不算。
-- 触发器需要覆盖 selected <-> completed、completed 插入、DELETE 等场景。
```

如果项目后续数据量不大，也可以去掉冗余字段，在需要时用聚合查询实时计算：

```sql
SELECT offering_id, COUNT(*) AS selected_count
FROM enrollment
WHERE status IN ('selected', 'completed')
GROUP BY offering_id;
```

### 4. 选课容量校验需要事务保护

当前 `enroll()` 的流程是多次独立查询：查是否已选、查容量和开放时间、查先修课、最后插入或恢复选课。每个 `query_one()` 和 `execute()` 都是独立连接和独立事务。并发情况下，两个学生可能同时读到同一个剩余名额，然后都插入成功。

建议把选课流程改为单个 `DBSession()`，并对班次行加锁：

```sql
SELECT co.max_capacity, co.selected_count, co.status,
       s.selection_start, s.selection_end, s.status AS semester_status
FROM course_offering co
JOIN semester s ON co.semester_id = s.semester_id
WHERE co.offering_id = %s
FOR UPDATE;
```

然后在同一个事务里完成：

- 查已有选课记录。
- 查开放窗口和容量。
- 查先修课。
- 插入或恢复 `enrollment`。

这样可以保证容量判断和写入之间没有竞态。

### 5. 成绩录入和日志写入应在同一事务

当前 `update_score()` 先更新 `enrollment`，再插入 `score_change_log`，两步分别调用 `execute()`。如果第一步成功、第二步失败，会出现成绩已变但日志缺失。

建议用一个 `DBSession()` 包住：

```python
with DBSession() as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE enrollment ...")
        cur.execute("INSERT INTO score_change_log ...")
```

同类问题也存在于：

- `delete_student()`：删除学生和账号。
- `delete_teacher()`：删除教师和账号。
- `delete_course()`：删除先修关系和课程。

这些应作为原子业务操作。

### 6. 重修和同学期重复选课规则需要建模

当前唯一约束是：

```sql
CONSTRAINT uq_student_offering UNIQUE (student_id, offering_id)
```

它只能防止同一学生重复选择同一个班次，但不能防止学生在同一学期选择同一门课的多个班次。如果业务规则是不允许同学期重复选同一门课，需要额外约束。

由于 `course_id` 和 `semester_id` 在 `course_offering` 表中，无法直接在 `enrollment` 上建立跨表唯一约束。可选方案：

- 在应用层查询并阻止同学期同课程重复选课。
- 在 `enrollment` 冗余 `course_id`、`semester_id`，再建立 `UNIQUE(student_id, semester_id, course_id)`。
- 用触发器在插入前检查同学期同课程是否已有有效记录。

课程项目里建议先用应用层检查；如果要强调数据库设计能力，可以使用触发器。

### 7. 课程时间安排应考虑规范化

当前 `course_offering.schedule_text` 是自由文本，例如“周一 1-2 节 / 周三 3-4 节”。这方便展示，但无法做冲突检测，也无法按星期、节次、教室查询。

如果要增强系统完整性，建议新增：

```sql
CREATE TABLE course_offering_slot (
    slot_id      BIGSERIAL PRIMARY KEY,
    offering_id  BIGINT NOT NULL REFERENCES course_offering(offering_id),
    weekday      SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
    start_period SMALLINT NOT NULL CHECK (start_period > 0),
    end_period   SMALLINT NOT NULL CHECK (end_period >= start_period),
    weeks_text   VARCHAR(50)
);
```

然后可以进一步检查：

- 同一教师同一时间不能有两个班次。
- 同一教室同一时间不能有两个班次。
- 同一学生不能选择时间冲突的课程。

### 8. 教室容量和开课容量需要一致性规则

当前 `course_offering.max_capacity` 只检查大于 0，没有和 `classroom.capacity` 关联。因为 `CHECK` 约束不能直接查另一张表，需要在应用层或触发器里保证：

```text
course_offering.max_capacity <= classroom.capacity
```

如果允许线上课或无教室班次，则需要定义 `classroom_id IS NULL` 时的规则。

### 9. 状态字段：当前 CHECK 足够，码表是增强项

当前用 `VARCHAR + CHECK` 模拟枚举，例如 `role`、`status`、`course_type`。这种方式可迁移性更好，也便于 openGauss 运行。

如果后续要做后台可配置状态、展示中文名、排序权重，可以改为码表：

```sql
CREATE TABLE code_course_type (
    code VARCHAR(20) PRIMARY KEY,
    label VARCHAR(30) NOT NULL,
    sort_no INTEGER NOT NULL
);
```

课程项目不一定要上码表；当前 `CHECK` 方案已经比较清爽。

### 10. 密码字段建议升级

当前 `password_hash` 是裸 SHA-256。虽然不是数据库性能问题，但属于用户表设计风险。

建议后续改为：

- `password_hash VARCHAR(255)`。
- 使用 `bcrypt`、`argon2` 或 PBKDF2。
- 增加 `password_updated_at`。

如果只是课程演示，可以保留 SHA-256，但文档中最好说明是简化实现。

## 二、查询语句优化

### 1. `list_offerings_for_student()` 改写 `NOT IN`

当前查询：

```sql
AND co.offering_id NOT IN (
    SELECT offering_id FROM enrollment
    WHERE student_id = %s AND status = 'selected'
)
```

建议改为 `NOT EXISTS`：

```sql
AND NOT EXISTS (
    SELECT 1
    FROM enrollment e
    WHERE e.student_id = %s
      AND e.status = 'selected'
      AND e.offering_id = co.offering_id
)
```

原因：

- 避免 `NOT IN` 遇到 `NULL` 时的三值逻辑风险。
- 更容易配合 `idx_enrollment_student_status_offering` 做反连接。
- 可读性更接近业务语义。

对应索引：

```sql
CREATE INDEX idx_enrollment_student_status_offering
    ON enrollment (student_id, status, offering_id);
```

### 2. `get_active_semester()` 减少一次往返

当前逻辑先查开放学期，没有再查最近学期。可以合并为一次查询：

```sql
SELECT *
FROM semester
ORDER BY
    CASE WHEN status = 'open' THEN 0 ELSE 1 END,
    start_date DESC
LIMIT 1;
```

这样无论有没有开放学期都只访问一次数据库。

### 3. 管理员首页统计合并为一次查询

当前首页四个指标分别发四条 SQL。数据量不大时没问题，但可以用一个查询减少连接往返：

```sql
SELECT
    (SELECT COUNT(*) FROM student WHERE status = 'enrolled') AS enrolled_students,
    (SELECT COUNT(*) FROM teacher WHERE status = 'active') AS active_teachers,
    (SELECT COUNT(*) FROM course WHERE status = 'active') AS active_courses,
    (
        SELECT COUNT(*)
        FROM enrollment e
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN semester s ON co.semester_id = s.semester_id
        WHERE s.status = 'open' AND e.status = 'selected'
    ) AS current_selected_count;
```

对应索引：

```sql
CREATE INDEX idx_student_status_id ON student (status, student_id);
CREATE INDEX idx_teacher_status_id ON teacher (status, teacher_id);
CREATE INDEX idx_course_status_id ON course (status, course_id);
CREATE INDEX idx_enrollment_offering_status_student
    ON enrollment (offering_id, status, student_id);
```

### 4. 成绩分布交给数据库聚合

当前 `get_score_distribution()` 把所有分数取回 Python 再分桶。建议改为数据库聚合：

```sql
SELECT
    CASE
        WHEN final_score >= 90 THEN '90-100'
        WHEN final_score >= 80 THEN '80-89'
        WHEN final_score >= 70 THEN '70-79'
        WHEN final_score >= 60 THEN '60-69'
        ELSE '不及格'
    END AS score_range,
    COUNT(*) AS count
FROM enrollment
WHERE offering_id = %s
  AND final_score IS NOT NULL
  AND status = 'completed'
GROUP BY score_range;
```

收益：

- 减少 Python 侧循环。
- 只传输聚合结果。
- 数据量变大后更稳定。

对应索引：

```sql
CREATE INDEX idx_enrollment_offering_status_score
    ON enrollment (offering_id, status, final_score);
```

### 5. 先修课程检查可以合并查询

当前 `_has_passed_prerequisites()` 先查目标课程，再查先修总数，再查缺失数。可以压缩为一次缺失检查：

```sql
SELECT COUNT(*) AS missing_count
FROM course_prerequisite cp
JOIN course_offering target ON target.course_id = cp.course_id
WHERE target.offering_id = %s
  AND NOT EXISTS (
      SELECT 1
      FROM enrollment e
      JOIN course_offering passed ON e.offering_id = passed.offering_id
      WHERE e.student_id = %s
        AND passed.course_id = cp.prereq_course_id
        AND e.status = 'completed'
        AND e.final_score >= 60
  );
```

如果 `missing_count = 0`，说明满足先修课。这样可以去掉一次“是否有先修课”的额外查询。

对应索引：

```sql
CREATE INDEX idx_offering_course ON course_offering (course_id);
CREATE INDEX idx_enrollment_student_status_score
    ON enrollment (student_id, status, final_score);
```

### 6. 成绩修改日志应利用过滤条件提前缩小集合

当前 `get_score_change_log()` 在多表 JOIN 后再按 `offering_id` 过滤。可以先确定目标 `enrollment_id` 集合，再关联日志：

```sql
SELECT scl.log_id, scl.changed_at, scl.old_score, scl.new_score, scl.reason,
       u.username AS changed_by,
       s.student_id, s.student_name,
       c.course_name, co.offering_id
FROM score_change_log scl
JOIN enrollment e ON scl.enrollment_id = e.enrollment_id
JOIN course_offering co ON e.offering_id = co.offering_id
JOIN student s ON e.student_id = s.student_id
JOIN course c ON co.course_id = c.course_id
JOIN user_account u ON scl.changed_by_user_id = u.user_id
WHERE (%s IS NULL OR co.offering_id = %s)
ORDER BY scl.changed_at DESC
LIMIT %s;
```

如果 `offering_id` 经常存在，也可以在 Python 里分成两条 SQL：有班次过滤时使用专门 SQL，无过滤时使用全局日志 SQL。这样查询计划更稳定。

对应索引：

```sql
CREATE INDEX idx_score_log_enrollment ON score_change_log (enrollment_id);
CREATE INDEX idx_score_log_changed_at ON score_change_log (changed_at DESC);
CREATE INDEX idx_enrollment_offering_status_student
    ON enrollment (offering_id, status, student_id);
```

### 7. 删除前检查用 `EXISTS`

当前删除课程、教师、班次前使用 `COUNT(*)` 判断是否有关联记录。只需要判断存在性时，`EXISTS` 可以更早停止。

示例：

```sql
SELECT EXISTS (
    SELECT 1
    FROM course_offering
    WHERE course_id = %s
) AS has_offering;
```

用于替换：

- `delete_course()` 中的开课记录检查。
- `delete_teacher()` 中的教师开课记录检查。
- `delete_offering()` 中的选课记录检查。

### 8. 模糊搜索要注意前置通配符

当前学生、教师、课程搜索使用：

```sql
LIKE '%keyword%'
```

普通 B-tree 索引不能有效支持前置 `%`。数据量小可以保留；如果数据变多，建议：

- 学号、教师号、课程号用精确或前缀搜索：`student_id LIKE '2024%'`。
- 姓名搜索保留模糊，但接受顺序扫描。
- 或者引入全文/倒排索引方案，但课程项目未必需要。

更贴近当前系统的改写：

```sql
WHERE (%s IS NULL)
   OR student_id = %s
   OR student_id LIKE %s
   OR student_name LIKE %s
```

参数可以分别传：`keyword`、`keyword`、`keyword || '%'`、`'%' || keyword || '%'`。

## 三、建议新增的索引脚本

可以新建 `opengauss_setup/sql/optimize_indexes.sql`，先只放索引，不直接改表结构：

```sql
CREATE INDEX IF NOT EXISTS idx_major_dept ON major (dept_id);
CREATE INDEX IF NOT EXISTS idx_student_major ON student (major_id);
CREATE INDEX IF NOT EXISTS idx_teacher_dept ON teacher (dept_id);
CREATE INDEX IF NOT EXISTS idx_course_dept ON course (dept_id);

CREATE INDEX IF NOT EXISTS idx_student_status_id ON student (status, student_id);
CREATE INDEX IF NOT EXISTS idx_teacher_status_id ON teacher (status, teacher_id);
CREATE INDEX IF NOT EXISTS idx_course_status_id ON course (status, course_id);
CREATE INDEX IF NOT EXISTS idx_semester_status_start ON semester (status, start_date DESC);

CREATE INDEX IF NOT EXISTS idx_offering_course ON course_offering (course_id);
CREATE INDEX IF NOT EXISTS idx_offering_semester_status_course
    ON course_offering (semester_id, status, course_id, offering_id);
CREATE INDEX IF NOT EXISTS idx_offering_teacher_semester
    ON course_offering (teacher_id, semester_id, offering_id);
CREATE INDEX IF NOT EXISTS idx_offering_classroom ON course_offering (classroom_id);

CREATE INDEX IF NOT EXISTS idx_prereq_prereq_course ON course_prerequisite (prereq_course_id);

CREATE INDEX IF NOT EXISTS idx_enrollment_student_status_offering
    ON enrollment (student_id, status, offering_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_offering_status_student
    ON enrollment (offering_id, status, student_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_student_status_score
    ON enrollment (student_id, status, final_score);
CREATE INDEX IF NOT EXISTS idx_enrollment_offering_status_score
    ON enrollment (offering_id, status, final_score);

CREATE INDEX IF NOT EXISTS idx_score_log_enrollment ON score_change_log (enrollment_id);
CREATE INDEX IF NOT EXISTS idx_score_log_changed_by ON score_change_log (changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_score_log_changed_at ON score_change_log (changed_at DESC);
```

## 四、推荐落地顺序

第一阶段：低风险性能优化。

- 新增 `optimize_indexes.sql`。
- 改写 `NOT IN` 为 `NOT EXISTS`。
- `get_active_semester()` 合并为一次查询。
- 成绩分布改为数据库聚合。
- 删除前检查改为 `EXISTS`。

第二阶段：一致性优化。

- `enroll()` 用单事务和 `FOR UPDATE`。
- `update_score()` 更新成绩和写日志放进同一事务。
- 学生、教师、课程删除逻辑放进同一事务。
- 明确并修正 `selected_count` 触发器语义。

第三阶段：模式增强。

- 加同学期同课程重复选课规则。
- 增加课程时间槽表，支持冲突检测。
- 增加教室容量约束逻辑。
- 密码 hash 升级。

## 五、验收方式

每次优化后建议执行：

```sql
EXPLAIN ANALYZE
SELECT ...
```

重点看：

- 是否使用了预期索引。
- 扫描行数是否明显减少。
- 是否出现不必要的全表扫描。
- 查询返回结果是否和优化前一致。

业务回归建议覆盖：

- `admin / 123456` 登录。
- 学生查看可选课程、已选课程。
- 学生选课、退课。
- 教师录入成绩，并生成日志。
- 管理员首页统计。
- 成绩分布图。
