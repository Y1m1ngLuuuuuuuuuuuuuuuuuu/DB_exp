# ER 图说明

## 1. 图文件

- Mermaid 源码：`report/diagrams/er_conceptual.mmd`
- Mermaid 源码：`report/diagrams/er_logical.mmd`
- PNG 图片：`report/figures/er_conceptual.png`
- PNG 图片：`report/figures/er_logical.png`

## 2. 概念结构 ER 图

概念图展示系统主要实体和基数关系：

- 院系与专业、教师、课程为 1:N。
- 统一账号与学生、教师、管理员资料为 1:0..1。
- 课程与开课班次为 1:N。
- 学期、教师、教室与开课班次均为 1:N。
- 开课班次与上课时间片为 1:N。
- 学生与开课班次通过 `enrollment` 转换 M:N。
- 课程先修关系通过 `course_prerequisite` 表达课程自关联。
- 成绩修改日志由 `score_change_log` 记录。

Mermaid ER 图中字段名后缀 `_pk`、`_fk`、`_uk` 分别表示主键、外键和唯一约束。

## 3. 逻辑关系模型图

逻辑图强调真实关系模式、主键、外键、中间表和结构化时间表。学生与教学班没有直接画成 M:N，而是通过 `ENROLLMENT` 连接；课程与先修课也通过 `COURSE_PREREQUISITE` 表达。

## 4. ER 到关系模型转换说明

学生选择教学班这一 M:N 联系被转换为：

- `student 1:N enrollment`
- `course_offering 1:N enrollment`

由于该联系本身具有选课时间、状态和成绩等属性，因此设计独立的 `enrollment` 表是合理的。课程先修关系是课程实体的自关联，多对多关系被转换为 `course_prerequisite(course_id, prereq_course_id)`。

## 5. 特别说明

当前数据库已经显式实现 `course_schedule`，用于结构化上课时间。图中没有把旧字段 `schedule_text`、`selected_count`、`gpa_point` 画入基础表，因为这些字段已经从当前结构中删除。
