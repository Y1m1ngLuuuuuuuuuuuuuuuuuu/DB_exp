
## 1. 数据库层约束

当前 `init.sql` 实现了主键、外键、UNIQUE、CHECK、DEFAULT 和部分级联删除。

主要约束包括：

- `user_account.username` 唯一，`role` 和 `status` 通过 CHECK 限制。
- `student.user_id`、`teacher.user_id`、`admin_profile.user_id` 唯一。
- `enrollment(student_id, offering_id)` 唯一，防止同一学生重复选择同一教学班。
- `course_schedule(offering_id, weekday, start_section, end_section)` 唯一，防止同一班次重复时间片。
- `final_score` 限制在 0 到 100。
- `course_schedule.weekday` 限制在 1 到 7，节次要求结束不早于开始。

## 2. 触发器

当前 3NF 版本没有实现数据库触发器。旧版用于维护 `selected_count` 的触发器已不适用于当前结构，因为 `selected_count` 已删除。报告中不能写“触发器已实现”，只能写“触发器设计方案”。

可设计的触发器包括：

- `BEFORE INSERT OR UPDATE ON enrollment` 检查容量和时间冲突；
- 成绩更新触发器自动写入 `score_change_log`；
- 课程先修关系触发器防止自循环或环路。

## 3. 应用层校验

当前复杂业务规则主要在服务层实现：

- `selection_service.enroll()` 检查重复、容量、学期状态、选课窗口、先修课、时间冲突。
- `selection_service.drop()` 检查本人记录、状态、成绩是否已录入、退课窗口。
- `score_service.can_manage_offering_score()` 检查教师只能管理本人教学班。
- `course_service.create_offering()` 与 `update_offering()` 解析并维护 `course_schedule`。

## 4. 事务与锁

`db/connection.py` 中的 `DBSession` 提供自动提交和回滚。当前 `selection_service.enroll()` 已使用 `DBSession` 并对目标 `course_offering` 行执行 `SELECT ... FOR UPDATE`，使同一教学班的容量检查和写入串行化。

同时，`enrollment` 的唯一约束可以防止同一学生多窗口重复选择同一教学班。当前没有使用乐观锁版本号，也没有保存计数字段做原子更新。

## 5. 剩余风险

- 成绩更新和日志插入还可以合并到同一事务。
- 成绩录入与退课并发时，可进一步对同一 `enrollment` 行加锁。
- 管理员降低容量时，应检查不低于当前已选人数。
- 同课跨班重复选择和教室容量限制仍需触发器或事务检查。
