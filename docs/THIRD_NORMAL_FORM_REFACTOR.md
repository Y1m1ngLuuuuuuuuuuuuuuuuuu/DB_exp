# 3NF 规范化重构说明

本文档记录 2026-06-08 对选课系统数据库设计进行的 3NF 规范化调整。目标是在不大规模重写页面交互的前提下，消除基础表中的多值字段和可由其他字段推导出的冗余字段。

## 1. 调整目标

原设计中主要存在三个规范化风险：

- `course_offering.schedule_text` 用一个字符串保存多个上课时间片，例如“周一 1-2 节 / 周三 3-4 节”。该字段混合了星期、开始节次、结束节次和多个时间片，严格分析下不利于 1NF。
- `course_offering.selected_count` 可由 `enrollment` 中 `status='selected'` 的记录数聚合得到，是跨表派生数据。
- `enrollment.gpa_point` 可由 `final_score` 和固定绩点规则计算得到，存在 `final_score -> gpa_point` 的函数依赖风险。

本次重构将这些值从基础表中移除，并改为结构化存储或查询时计算。

## 2. 数据库结构调整

### 2.1 开课班次与上课时间分离

`course_offering` 现在只保存开课事实本身：

`CourseOffering(offering_id, course_id, semester_id, teacher_id, classroom_id, max_capacity, status)`

新增 `course_schedule` 表保存一个教学班的多个上课时间片：

`CourseSchedule(schedule_id, offering_id, weekday, start_section, end_section)`

主要约束包括：

- 主键：`schedule_id`
- 外键：`offering_id -> course_offering.offering_id`
- 唯一约束：`(offering_id, weekday, start_section, end_section)`
- 检查约束：`weekday BETWEEN 1 AND 7`
- 检查约束：`start_section > 0 AND end_section >= start_section`

这样每条上课时间记录都是原子值，支持按星期、节次查询，也支持时间冲突检测。

### 2.2 删除已选人数冗余字段

`course_offering.selected_count` 已删除。当前已选人数使用如下逻辑计算：

```sql
SELECT COUNT(*)
FROM enrollment
WHERE offering_id = ?
  AND status = 'selected';
```

页面仍然显示“已选/上限”，但 `selected_count` 是服务层 SQL 查询的别名，不再是表字段。

### 2.3 删除绩点冗余字段

`enrollment.gpa_point` 已删除。当前成绩单和选课页展示绩点时，通过 `final_score` 的 CASE 表达式动态计算：

```sql
CASE
    WHEN final_score IS NULL THEN NULL
    WHEN final_score >= 90 THEN 4.0
    WHEN final_score >= 85 THEN 3.7
    WHEN final_score >= 82 THEN 3.3
    WHEN final_score >= 78 THEN 3.0
    WHEN final_score >= 75 THEN 2.7
    WHEN final_score >= 72 THEN 2.3
    WHEN final_score >= 68 THEN 2.0
    WHEN final_score >= 64 THEN 1.5
    WHEN final_score >= 60 THEN 1.0
    ELSE 0.0
END
```

这样 `enrollment` 只保存学生选课事实和最终成绩，不再保存可由成绩直接推导的绩点。

## 3. 代码适配

### 3.1 `services/course_service.py`

该文件新增了上课时间解析和 SQL 聚合逻辑：

- `parse_schedule_text()`：将页面输入的“周一 1-2 节 / 周三 3-4 节”解析为结构化时间片。
- `_schedule_text_sql()`：查询时把 `course_schedule` 聚合回页面展示文本。
- `_selected_count_sql()`：查询时统计当前已选人数。
- `_gpa_point_sql()`：查询已选课程时动态计算绩点。

创建或更新开课班次时，代码会先写入 `course_offering`，再写入对应的 `course_schedule`，并由 `DBSession` 保证同一事务内提交或回滚。

### 3.2 `services/selection_service.py`

该文件的容量检查改为基于 `enrollment` 聚合计算当前已选人数，不再读取 `course_offering.selected_count`。

同时，`enroll()` 已改为单事务流程：先锁定学生已有选课记录，再用 `SELECT ... FOR UPDATE` 锁定目标 `course_offering` 行，随后在同一事务内完成容量、先修课、时间冲突检查和插入或恢复选课。

该文件新增 `_has_time_conflict()`，通过 `course_schedule` 判断目标班次与学生已选班次是否存在同一天、节次区间重叠：

```sql
target.start_section <= selected.end_section
AND selected.start_section <= target.end_section
```

如果存在重叠，则拒绝选课并提示“与已选课程时间冲突”。

### 3.3 `services/score_service.py`

成绩更新只写入 `final_score` 并把状态改为 `completed`。绩点不再入库，而是在成绩列表和成绩单查询时按 CASE 表达式计算。

### 3.4 `pages/admin_dashboard.py`

管理员首页中各班次已选人数改为查询时聚合，保持页面显示格式不变。

## 4. 范式判断

### 4.1 1NF

`course_schedule` 将星期、开始节次、结束节次拆成原子字段，并用多行表达一个班次的多个时间片。基础表中不再用一个字段保存列表型时间数据，因此主要课程安排表满足 1NF。

### 4.2 2NF

`course_prerequisite` 的复合主键 `(course_id, prereq_course_id)` 没有额外非主属性。其他核心表多使用单列主键，非主属性依赖完整主键，不存在明显部分函数依赖。

### 4.3 3NF

本次重构删除了两个典型派生字段：

- `selected_count` 由 `enrollment` 聚合得到，不再存储于 `course_offering`。
- `gpa_point` 由 `final_score` 和绩点规则得到，不再存储于 `enrollment`。

因此当前核心关系中未发现明确的“非主属性依赖于另一个非主属性”的 3NF 违反。仍需结合业务进一步确认的语义包括：

- `student.class_name` 是否只是文本标签，还是应拆为独立 `class` 实体；
- `classroom(building, room_no)` 是否应作为候选键；
- 绩点规则是否需要版本化，如果需要，可增加 `grade_rule` 表。

### 4.4 BCNF

当前核心表在已声明主键和唯一约束范围内基本满足 BCNF。对于未声明但可能存在的业务决定关系，例如 `(building, room_no) -> classroom_id`，需要根据业务规则进一步补充唯一约束后才能严格判断。

## 5. 事务与并发控制

本次重构之后，选课容量控制也完成了事务化改造：

- `DBSession` 保证选课检查和写入在同一事务内提交或回滚。
- `SELECT ... FOR UPDATE` 锁定目标 `course_offering` 行，使同一教学班的并发选课容量检查串行化。
- 当前已选人数由 `enrollment(offering_id, status)` 聚合得到，并配合 `idx_enrollment_offering_status` 降低统计成本。

仍可继续增强的数据库设计包括：

- 数据库级触发器：可设计 `BEFORE INSERT OR UPDATE ON enrollment` 触发器检查容量、时间冲突和退课条件，把关键业务规则下沉到数据库层。
- 规则版本化：如果绩点换算规则未来可能变化，可新增 `grade_rule` 或 `grade_policy` 表，并在成绩记录中保存规则版本。
- 成绩事务化：将成绩更新和成绩日志写入放入同一事务，避免成绩已改但日志缺失。

## 6. 本次暂不拆分行政班

`student.class_name` 当前仍保留为学生表中的文本字段。严格规范化时，如果行政班具有独立属性，例如班级编号、所属专业、年级、辅导员、班主任等，可以继续拆分为：

`Class(class_id, class_name, major_id, grade_year, ...)`

然后由 `student.class_id` 外键引用行政班表。

本次没有立即拆分，原因如下：

- 当前系统的核心业务是选课、退课、开课班次和成绩管理，行政班只用于学生列表展示和筛选，不直接参与选课容量、时间冲突、先修课和成绩规则。
- 拆分行政班会牵动学生新增、编辑、展示等页面，但对本次 3NF 重点问题的收益较小。
- 在期末报告中，可将其作为“进一步提高规范化程度的后续改进”，用于说明数据库设计可以随着业务语义继续演进。

## 7. 验证记录

- 已通过静态扫描确认业务代码不再直接引用被删除的列：`co.selected_count`、`co.schedule_text`、`e.gpa_point`。
- 已通过 Python 语法编译检查，服务层和页面层没有语法错误。
- 已使用新的 `opengauss_setup/sql/init.sql` 重建本地 Docker openGauss 数据库，确认旧列已不存在，`course_schedule` 导入 19 条时间片。
- 已通过项目服务层查询验证：课程列表可动态返回 `schedule_text`、`selected_count`，成绩单可动态返回 `gpa_point`。
- 已调用 `selection_service.enroll()` 验证事务路径可执行，重复选课和过期选课窗口均按预期拒绝。
