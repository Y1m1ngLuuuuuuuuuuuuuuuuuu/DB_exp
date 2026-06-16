# Streamlit UI Redesign Audit

审计时间：2026-06-11

## 1. 当前入口文件

- 入口文件：`app.py`
- 技术栈：Streamlit + Python services + openGauss
- 页面加载方式：登录后根据 `st.session_state.role` 在 `app.py` 中选择页面模块，并通过 `importlib.import_module(...).render()` 渲染。

## 2. 当前页面结构

| 角色 | 当前页面模块 | 作用 |
| --- | --- | --- |
| 未登录 | `pages/login.py` | 用户登录、创建 session token、写入 cookie |
| 学生 | `pages/student_select.py` | 可选课程、已选课程、选课、退课 |
| 学生 | `pages/student_report.py` | 成绩单、平均成绩、加权绩点 |
| 教师 | `pages/score_manage.py` | 教学班学生名单、成绩录入、成绩修改日志 |
| 管理员 | `pages/admin_dashboard.py` | 管理统计首页 |
| 管理员 | `pages/semester_manage.py` | 学期管理 |
| 管理员 | `pages/offering_manage.py` | 开课班次管理 |
| 管理员 | `pages/course_manage.py` | 课程与开课安排维护 |
| 管理员 | `pages/student_manage.py` | 学生维护 |
| 管理员 | `pages/teacher_manage.py` | 教师维护 |

## 3. 当前角色导航方式

`app.py` 中的 `_NAV` 字典按角色维护页面名称和模块路径。侧边栏使用 `st.radio()` 显示导航，退出登录按钮调用 `logout()`。

## 4. 当前 session_state

`app.py` 初始化以下登录状态：

- `logged_in`
- `user_id`
- `username`
- `role`
- `student_id`
- `teacher_id`
- `session_token`
- `clear_login_cookie`

`utils/session_state.py` 中 `apply_login_state()` 会在登录成功后写入用户、角色、学生号或教师号。

## 5. 当前登录流程

1. `pages/login.py` 调用 `services.auth_service.login(username, password)`；
2. 登录成功后调用 `create_session(user_id)` 生成 session；
3. `apply_login_state()` 写入 Streamlit session；
4. `set_auth_cookie(token)` 写入浏览器 cookie；
5. `app.py` 在刷新时通过 `get_auth_cookie()` 和 `get_user_by_session_token()` 恢复登录。

## 6. 当前学生、教师、管理员页面

- 学生端：功能完整但页面以 expander 和默认 metric 为主，缺少 dashboard、课表分组和统一状态样式。
- 教师端：成绩录入功能可用，依赖 `score_service.update_score()` 保证成绩审计触发器正常执行；页面缺少教学任务概览。
- 管理员端：基础管理页面功能可用，表格和表单风格不统一；审计日志主要在成绩管理中查看。

## 7. 当前最明显的 UI 问题

1. 视觉风格依赖 Streamlit 默认组件，页面之间缺少统一设计语言；
2. 登录页较朴素，缺少清晰的产品标题、说明和卡片式结构；
3. 侧边栏导航信息密度低，角色身份和退出操作缺少层级；
4. 学生端缺少首页 dashboard，选课和已选课程卡片信息层次不够清楚；
5. 教师端缺少教学概览，成绩录入前的信息摘要不足；
6. 管理员端统计项较少，审计日志入口不够突出；
7. 数据库错误虽然已经有部分友好转换，但页面展示仍有不统一的 `保存失败：...` 样式；
8. 空状态和提示状态分散使用 `st.info()`、`st.warning()`，缺少统一视觉表达。

## 8. 可重构为组件的部分

- 全局 CSS 注入：`ui/theme.py`
- 页面标题：`render_app_header()`
- 指标卡片：`render_metric_card()`
- 状态徽标：`render_status_badge()`
- 空状态：`render_empty_state()`
- 友好错误提示：`render_error_message()`
- 侧边栏导航：`render_sidebar_navigation()`
- 简洁表格、分组容器、辅助说明：`ui/components.py`

## 9. 不能随意修改的边界

1. 不修改数据库 schema；
2. 不删除 SQL 迁移、触发器、视图、事务函数或测试脚本；
3. 学生选课必须继续调用 `services.selection_service.enroll()`；
4. 学生退课必须继续调用 `services.selection_service.drop()`；
5. 教师成绩录入必须继续调用 `services.score_service.update_score()`，以保证 `score_change_log` 触发器能获得 `app.current_user_id`；
6. 不读取或展示 `secrets/DEMO_ACCOUNT_CREDENTIALS.md` 中的明文密码；
7. 不破坏 `session_state` 和 cookie 恢复登录逻辑；
8. 不把教师评价模块写成已实现功能。

## 10. 本轮计划修改文件

| 文件 | 修改目的 |
| --- | --- |
| `.streamlit/config.toml` | 设置浅色主题、Apple-inspired 主色和页面布局 |
| `ui/theme.py` | 全局 CSS、状态颜色、数据库错误友好化 |
| `ui/components.py` | 标题、指标卡、状态 badge、空状态等 UI 组件 |
| `ui/navigation.py` | 角色导航组件 |
| `app.py` | 接入全局 CSS 和新版侧边栏导航 |
| `pages/login.py` | 重设计登录页 |
| `pages/student_dashboard.py` | 新增学生首页 |
| `pages/teacher_dashboard.py` | 新增教师首页 |
| `pages/student_select.py` | 优化选课、已选课程和课表展示 |
| `pages/student_report.py` | 优化成绩单和 GPA 展示 |
| `pages/score_manage.py` | 优化教师成绩管理和审计日志展示 |
| `pages/admin_dashboard.py` | 优化管理员 dashboard 和审计摘要 |
| 其他管理页 | 轻量接入统一标题和空状态样式 |
| `report/STREAMLIT_UI_REDESIGN_SUMMARY.md` | 记录本轮重构结果、验证结果和人工检查项 |
