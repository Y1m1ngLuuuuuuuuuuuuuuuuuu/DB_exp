# 选课系统学习路线

## 1. 学习目标

这份文档的目的是帮助我快速熟悉当前选课系统的整体框架，而不是一上来就陷入所有代码细节。

阅读这个项目时，最好的方法不是“从头到尾把所有文件都读一遍”，而是：

1. 先理解系统整体结构
2. 再理解主业务流程
3. 最后再补后台管理和基础设施细节

这样更容易建立完整认知，也更适合后续继续开发和修改。

## 2. 总体阅读原则

建议遵循下面三个原则：

### 2.1 先看入口，再看细节

先明确系统怎么启动、页面怎么分流、角色怎么切换，再去看具体功能实现。

### 2.2 先看主流程，再看后台管理

系统最核心的流程是：

- 登录
- 学生选课
- 教师录分
- 学生成绩查询

管理员模块虽然也重要，但不是理解系统的第一优先级。

### 2.3 先理解数据库，再理解业务代码

这个系统本质上是数据库驱动的应用。

如果先把数据库关系看清楚，再看 Python 代码，会轻松很多。

## 3. 最推荐的阅读顺序

### 第一步：先看项目总说明

先阅读：

- [README.md](/Users/lu/Code/Python/DB_exp/Big/README.md)

这一阶段的目标是先回答下面几个问题：

- 这个系统是做什么的
- 技术栈是什么
- 项目目录怎么组织
- 现在有哪些功能
- 怎么启动项目

阅读重点：

- 技术栈
- 目录结构
- 样本数据说明
- 启动步骤

如果这一部分没有先看清楚，后面看代码时会容易迷路。

## 4. 第二步：看系统总入口

接下来阅读：

- [app.py](/Users/lu/Code/Python/DB_exp/Big/app.py)

这是整个系统的总入口。

这一阶段要重点理解：

1. Streamlit 应用是怎么启动的
2. `session_state` 初始化了哪些字段
3. 未登录用户为什么只能看到登录页
4. 已登录用户如何按角色加载不同页面

阅读重点：

- `st.set_page_config(...)`
- `_SESSION_DEFAULTS`
- `logout()`
- `_NAV`
- 动态加载页面模块的逻辑

看完这个文件后，应该能回答：

- 学生为什么只能看到学生页面
- 教师为什么只能看到成绩管理
- 管理员为什么能看到更多菜单

## 5. 第三步：看登录认证

接下来阅读：

- [pages/login.py](/Users/lu/Code/Python/DB_exp/Big/pages/login.py)
- [services/auth_service.py](/Users/lu/Code/Python/DB_exp/Big/services/auth_service.py)

这是系统的认证入口。

这一阶段要重点理解：

1. 用户输入用户名和密码后发生了什么
2. 密码怎么校验
3. 为什么登录后能识别用户是学生、教师还是管理员
4. 为什么登录后会得到 `student_id` 或 `teacher_id`

阅读重点：

- `login()`
- `hash_password()`
- `get_student_id()`
- `get_teacher_id()`
- `st.session_state` 中哪些字段在登录后被写入

这一部分看懂后，整个权限系统的基础就建立起来了。

## 6. 第四步：看数据库结构

接下来阅读：

- [sql/init.sql](/Users/lu/Code/Python/DB_exp/Big/sql/init.sql)

这一部分非常重要。

这里不是要求把每条 SQL 都背下来，而是先建立“数据库地图”。

建议先重点关注这些表：

1. `user_account`
2. `student`
3. `teacher`
4. `course`
5. `course_offering`
6. `enrollment`
7. `score_change_log`

这一阶段要重点理解：

- 系统有哪些核心表
- 表之间怎么关联
- 为什么 `course` 和 `course_offering` 要分开
- 为什么成绩放在 `enrollment` 里
- 为什么需要 `score_change_log`

最核心的理解是：

学生不是直接选“课程”，而是选“开课班次”。

也就是：

- `course` 是课程定义
- `course_offering` 是某学期某教师开设的班次
- `enrollment` 是学生和班次之间的选课记录

这个认知一旦建立，后面大部分代码都会顺很多。

## 7. 第五步：看学生主流程

这一部分是系统最核心的业务流程。

建议按这个顺序阅读：

- [pages/student_select.py](/Users/lu/Code/Python/DB_exp/Big/pages/student_select.py)
- [services/selection_service.py](/Users/lu/Code/Python/DB_exp/Big/services/selection_service.py)
- [services/course_service.py](/Users/lu/Code/Python/DB_exp/Big/services/course_service.py)

### 7.1 先看学生选课页面

在 `pages/student_select.py` 中，重点理解：

- 页面为什么只允许学生访问
- 当前学期是怎么取到的
- 可选课程和已选课程是怎么分两个标签页展示的
- 点击“选课”或“退课”按钮后，调用了哪个服务函数

重点函数：

- `render()`

### 7.2 再看选课业务逻辑

在 `services/selection_service.py` 中，重点理解：

- 选课时做了哪些校验
- 为什么要检查容量、时间窗口、先修课
- 退课时为什么要检查是否为当前学生本人
- 为什么有成绩后不能退课

重点函数：

- `enroll()`
- `drop()`
- `_has_passed_prerequisites()`

### 7.3 再看课程与班次查询逻辑

在 `services/course_service.py` 中，重点理解：

- 当前开放学期怎么查询
- 学生可选班次怎么查出来
- 已选班次怎么查出来

重点函数：

- `get_active_semester()`
- `list_offerings_for_student()`
- `list_enrolled_offerings()`

看完这一部分后，应该能够说清楚：

- 学生是如何看到当前学期可选课程的
- 系统是如何防止重复选课的
- 系统是如何判断能不能退课的

## 8. 第六步：看成绩流程

这一部分是第二条主业务链。

建议按下面顺序阅读：

- [pages/score_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/score_manage.py)
- [services/score_service.py](/Users/lu/Code/Python/DB_exp/Big/services/score_service.py)
- [pages/student_report.py](/Users/lu/Code/Python/DB_exp/Big/pages/student_report.py)

### 8.1 成绩管理页

在 `pages/score_manage.py` 中，重点理解：

- 为什么教师和管理员都能进入这个页面
- 学期和班次是怎么选择的
- 为什么一次只看到一个班次的学生
- 为什么成绩是通过 `data_editor` 批量录入的

重点函数：

- `render()`

### 8.2 成绩服务层

在 `services/score_service.py` 中，重点理解：

- 怎么限制教师只能维护自己的班次
- 成绩为什么必须在 `0-100`
- 绩点是怎么计算的
- 为什么修改成绩时会写日志

重点函数：

- `can_manage_offering_score()`
- `update_score()`
- `calc_gpa()`
- `get_score_distribution()`
- `get_student_transcript()`

### 8.3 学生成绩单

在 `pages/student_report.py` 中，重点理解：

- 学生成绩单从哪里查
- 为什么只看 `completed` 状态
- 为什么可以统计累计学分、平均分、加权绩点

重点函数：

- `render()`

看完这一部分后，应该能回答：

- 教师怎么录分
- 成绩为什么会进入成绩单
- 为什么成绩修改会留下记录

## 9. 第七步：看管理员模块

管理员模块内容比较多，但建议放在主流程之后看。

建议阅读顺序：

- [pages/admin_dashboard.py](/Users/lu/Code/Python/DB_exp/Big/pages/admin_dashboard.py)
- [pages/course_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/course_manage.py)
- [pages/student_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/student_manage.py)
- [pages/teacher_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/teacher_manage.py)
- [pages/semester_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/semester_manage.py)
- [pages/offering_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/offering_manage.py)
- [services/student_service.py](/Users/lu/Code/Python/DB_exp/Big/services/student_service.py)
- [services/teacher_service.py](/Users/lu/Code/Python/DB_exp/Big/services/teacher_service.py)

### 9.1 管理员首页

重点看：

- 全局统计怎么查
- 各院系学生人数怎么画图
- 各班次选课情况怎么统计

### 9.2 课程与开课安排维护

重点看：

- 课程和开课班次为什么分开维护
- 新增课程和新增班次分别落到哪张表
- 删除课程为什么必须先删相关班次

### 9.3 学生与教师维护

重点看：

- 新增学生/教师时为什么同时要创建账号
- 为什么现在用事务来避免孤儿账号

这一部分更偏 CRUD，理解难度比主业务链低，但文件较多。

## 10. 第八步：看基础设施代码

最后再看这些基础文件：

- [db/connection.py](/Users/lu/Code/Python/DB_exp/Big/db/connection.py)
- [config.py](/Users/lu/Code/Python/DB_exp/Big/config.py)
- [pages/_guards.py](/Users/lu/Code/Python/DB_exp/Big/pages/_guards.py)

### 10.1 数据库连接层

在 `db/connection.py` 中，重点理解：

- 数据库连接是怎么创建的
- 查询和更新是怎么封装的
- `DBSession` 为什么能保证提交/回滚

重点函数和类：

- `get_connection()`
- `DBSession`
- `query()`
- `query_one()`
- `execute()`

### 10.2 配置文件

在 `config.py` 中，重点理解：

- 数据库连接参数在哪里配置
- 应用标题和图标在哪里配置

### 10.3 页面权限守卫

在 `pages/_guards.py` 中，重点理解：

- 页面为什么能限制不同角色访问
- 为什么没有权限时会直接中止页面渲染

重点函数：

- `require_role()`

## 11. 当前系统最重要的三个核心认知

在阅读过程中，一定要优先抓住下面三个核心点。

### 11.1 学生选的不是课程，而是开课班次

也就是说：

- 课程是定义
- 开课班次是可选对象
- 选课记录连接的是学生和开课班次

这是整个业务模型的核心。

### 11.2 登录后的角色分流由 `app.py + session_state` 控制

系统不是每个页面各自独立判断，而是通过：

- 登录写入 `session_state`
- 入口页按角色分配导航
- 页面内部再做权限守卫

这样实现统一控制。

### 11.3 成绩最终落在 `enrollment` 表中

系统里没有单独的“成绩主表”。

原因是：

- 成绩本质上属于某次选课记录
- 学生成绩必须和班次、状态、绩点一起保存

所以：

- 当前成绩存在 `enrollment`
- 修改历史存在 `score_change_log`

## 12. 一条最简学习路径

如果时间有限，可以只走下面这条路线：

1. [README.md](/Users/lu/Code/Python/DB_exp/Big/README.md)
2. [app.py](/Users/lu/Code/Python/DB_exp/Big/app.py)
3. [pages/login.py](/Users/lu/Code/Python/DB_exp/Big/pages/login.py)
4. [services/auth_service.py](/Users/lu/Code/Python/DB_exp/Big/services/auth_service.py)
5. [sql/init.sql](/Users/lu/Code/Python/DB_exp/Big/sql/init.sql)
6. [pages/student_select.py](/Users/lu/Code/Python/DB_exp/Big/pages/student_select.py)
7. [services/selection_service.py](/Users/lu/Code/Python/DB_exp/Big/services/selection_service.py)
8. [pages/score_manage.py](/Users/lu/Code/Python/DB_exp/Big/pages/score_manage.py)
9. [services/score_service.py](/Users/lu/Code/Python/DB_exp/Big/services/score_service.py)

如果这九步能看懂，你对整个系统的主干就已经掌握了。

## 13. 结论

这个项目最合理的学习方式不是“把所有代码都一口气看完”，而是按下面顺序推进：

`README -> 入口 -> 登录 -> 数据库 -> 学生主流程 -> 成绩流程 -> 管理员模块 -> 基础设施`

只要按这个顺序阅读，就能比较自然地从：

- 系统整体结构
- 角色权限逻辑
- 数据库设计
- 主业务流程
- 后台管理功能

一步一步建立完整理解。

这也是最适合后续继续修改和扩展这个系统的学习路线。

