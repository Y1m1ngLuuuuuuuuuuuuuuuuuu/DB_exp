# 范式与函数依赖审计

## 1. 总体结论

当前核心表总体达到 3NF。项目已经删除三个主要反范式风险字段：

- `course_offering.schedule_text`：列表型上课时间文本，已拆为 `course_schedule`。
- `course_offering.selected_count`：由 `enrollment` 聚合得到，已改为查询时计算。
- `enrollment.gpa_point`：由 `final_score` 和规则得到，已改为查询时计算。

## 2. 主要函数依赖

- `dept_id -> dept_name, office_phone, office_location`
- `major_id -> major_name, dept_id`
- `user_id -> username, password_hash, role, status`
- `username -> user_id, password_hash, role, status`
- `student_id -> user_id, student_name, major_id, class_name, status`
- `course_id -> course_name, course_type, credit, total_hours, dept_id, status`
- `offering_id -> course_id, semester_id, teacher_id, classroom_id, max_capacity, status`
- `enrollment_id -> student_id, offering_id, select_time, status, final_score`
- `(student_id, offering_id) -> enrollment_id, select_time, status, final_score`

## 3. 1NF

当前核心字段均为原子值。上课时间不再以 `schedule_text` 保存多个片段，而是由 `course_schedule(weekday, start_section, end_section)` 多行表达，满足 1NF。

## 4. 2NF

多数表使用单列主键，不存在典型部分依赖。`course_prerequisite(course_id, prereq_course_id)` 是复合键表，但没有额外非主属性。`enrollment` 的候选键 `(student_id, offering_id)` 决定选课时间、状态和成绩，这些属性依赖完整选课事实，满足 2NF。

## 5. 3NF

当前设计避免在学生表冗余专业名、在课程表冗余院系名、在教学班表冗余课程名或教师名。删除 `selected_count` 和 `gpa_point` 后，核心表没有明显非主属性传递依赖。`student.class_name` 目前作为展示文本保留；若行政班有独立属性，应拆分为 `Class` 表。

## 6. BCNF

不能直接断言所有表满足 BCNF。需要进一步确认的业务依赖包括：

- `classroom(building, room_no)` 是否唯一确定教室；
- 同一课程、学期、教师、时间片组合是否唯一确定教学班；
- 未来绩点规则版本是否会影响成绩依赖。

因此报告中应写为“核心表总体达到 3NF，部分表可结合业务语义继续补强 BCNF”。

## 7. 改进建议

优先改进方向包括：为 `classroom(building, room_no)` 增加唯一约束；按业务需要拆分行政班实体；建立绩点规则版本表；为同课跨班重复选择设计触发器或事务检查。
