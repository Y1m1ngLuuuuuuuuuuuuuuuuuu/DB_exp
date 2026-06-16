# Streamlit UI Redesign Summary

完成时间：2026-06-11

## 1. 修改文件

### 新增文件

- `.streamlit/config.toml`
- `ui/__init__.py`
- `ui/theme.py`
- `ui/components.py`
- `ui/cards.py`
- `ui/layout.py`
- `ui/navigation.py`
- `pages/student_dashboard.py`
- `pages/teacher_dashboard.py`
- `pages/audit_log.py`
- `report/STREAMLIT_UI_REDESIGN_AUDIT.md`
- `report/STREAMLIT_UI_REDESIGN_SUMMARY.md`
- `report/figures/ui_login.png`
- `report/figures/ui_student_dashboard.png`
- `report/figures/ui_teacher_dashboard.png`
- `report/figures/ui_admin_dashboard.png`

### 主要修改文件

- `app.py`
- `config.py`
- `pages/login.py`
- `pages/student_select.py`
- `pages/student_report.py`
- `pages/score_manage.py`
- `pages/admin_dashboard.py`
- `pages/audit_log.py`
- `pages/semester_manage.py`
- `pages/offering_manage.py`
- `pages/course_manage.py`
- `pages/student_manage.py`
- `pages/teacher_manage.py`
- `services/course_service.py`
- `services/score_service.py`

## 2. 新增 UI 组件

- `inject_global_css()`：统一 Apple-inspired 浅色主题、卡片、按钮、表格、侧边栏和空状态样式。
- `render_app_header()`：页面顶部大标题和说明。
- `render_metric_card()`：指标卡片。
- `render_status_badge()`：状态徽标。
- `render_empty_state()`：统一空状态。
- `render_error_message()`：友好错误提示。
- `render_friendly_error()`：兼容调用名，统一转换数据库错误。
- `render_filter_bar()`：统一筛选区域标题和容器。
- `render_course_card()`：课程和教学班卡片。
- `render_sidebar_navigation()`：按角色渲染简洁导航。
- `render_sidebar()`：兼容调用名，保留角色导航行为。

## 3. 页面视觉风格

本轮采用 Apple-inspired clean design，但不使用 Apple 商标、Logo 或官网素材。视觉约束包括：

- 背景：`#F5F5F7`
- 主色：`#0071E3`
- 卡片：白色、22px 左右圆角、轻阴影
- 字体：sans serif
- 表格：简洁、留白、弱边框
- 提示：低饱和成功/警告/错误颜色
- 顶栏：隐藏 Streamlit 默认 `Deploy`、主菜单和状态控件，减少默认调试页面感

同时隐藏了 Streamlit 自动 multipage 导航，避免 `pages/` 下内部模块暴露给普通用户；系统继续使用 `app.py` 中基于角色的自定义导航。

## 4. 学生端优化

- 新增 `学生首页` dashboard：
  - 当前已选课程数；
  - 本学期课程数；
  - 已完成课程；
  - 加权绩点；
  - 今日课程；
  - 成绩概览。
- 重构 `课程选课`：
  - 增加学期、课程名、课程类型、是否有余量筛选；
  - 使用课程卡片展示教师、时间、教室、学分、容量；
  - 选课失败通过友好中文提示展示；
  - 新增课表标签页，读取 `v_student_timetable`。
- 重构 `成绩与绩点`：
  - 使用指标卡展示已修门数、累计学分、平均成绩和加权绩点；
  - 保持 GPA 来自数据库视图，不在前端恢复 `gpa_point` 基础字段。

## 5. 教师端优化

- 新增 `教师首页` dashboard：
  - 本学期教学班数量；
  - 学生人数；
  - 待录入成绩；
  - 已完成录入；
  - 我的教学班；
  - 最近成绩修改。
- 重构 `成绩管理`：
  - 增加教学班指标摘要；
  - 成绩保存前增加确认勾选；
  - 保持调用 `score_service.update_score()`，不绕过成绩审计触发器；
  - 审计日志以更清晰的表格展示。

## 6. 管理员端优化

- 重构 `管理员首页`：
  - 在籍学生、在职教师、开放课程、教学班、当前选课、成绩日志；
  - 各班次选课情况；
  - 各院系在籍学生人数；
  - 最近成绩修改日志。
- 新增 `审计日志` 独立页面：
  - 支持按学期、教师、课程、学生和日期范围筛选；
  - 展示原成绩、新成绩、修改人、修改时间和修改原因；
  - 继续读取 `score_change_log`，不暴露 SQL 原始异常。
- 轻量优化基础管理页：
  - 学期、开课安排、课程、学生、教师页面统一标题；
  - 统一空状态样式；
  - 保留原有表单和服务调用，降低业务回归风险。

## 7. 登录页优化

- 居中登录卡片；
- 系统名称为“学生选课成绩管理系统”；
- 副标题为 `Course Selection & Academic Records`；
- 登录失败提示改为友好中文；
- 演示账号说明只展示账号规则，不读取也不展示 `secrets/DEMO_ACCOUNT_CREDENTIALS.md` 中的真实密码。

## 8. 是否修改后端

没有修改数据库 schema，没有删除或绕过触发器、视图、事务函数和测试脚本。

后端仅有一处查询体验优化：

- `services/course_service.py` 中 `list_offerings_for_student()` 不再向学生展示同一学期已选课程的其他教学班。数据库层的同课跨班触发器仍然保留兜底。
- `services/score_service.py` 中 `get_score_change_log()` 增加审计日志筛选参数，用于管理员审计日志页面；该修改只扩展只读查询，不改变数据库结构。

## 9. 是否修改数据库

未修改数据库 schema，未恢复以下字段：

- `course_offering.selected_count`
- `course_offering.schedule_text`
- `enrollment.gpa_point`

## 10. 测试与验证

### Python 静态检查

已通过：

```text
.venv/bin/python -m compileall . -q -x '(^./\\.venv|^./__pycache__|^./report|^./logs|^./opengauss_setup/docker/data)'
```

本轮收口后再次执行同类 `compileall`，通过。

### 只读服务层检查

已执行 `get_score_change_log(limit=5)` 和带课程/学生关键词的筛选查询，均可正常返回，未出现 SQL 参数错误。

### Streamlit 启动

已启动：

```text
.venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

访问地址：

```text
http://127.0.0.1:8501
```

### Browser smoke test

已完成：

- 登录页渲染；
- 管理员登录并进入管理员首页；
- 教师登录并进入教师首页；
- 学生登录并进入学生首页；
- 学生进入课程选课页，确认课程筛选、课程卡片和选课按钮渲染；
- 教师进入成绩管理页，确认成绩录入表、确认勾选和审计日志入口渲染。

本轮新增验证：

- 登录页 DOM 中包含系统标题、副标题、账号/密码输入和登录按钮；
- 新增 `审计日志` 已加入管理员导航；
- `pages/audit_log.py` 已通过 Python 编译和只读服务层查询检查。

本地内置浏览器自动输入受到剪贴板/会话 cookie 写入限制，未在本轮通过自动化再次完成管理员登录跳转；真实 Streamlit 服务保持运行，可手动登录验证。

未自动执行会改写数据的 UI 操作：

- 未通过 UI 实际点击选课提交；
- 未通过 UI 实际保存成绩。

原因：避免污染当前演示数据。选课和成绩写入路径已经由数据库 SQL 测试、事务函数和并发测试覆盖。

### 浏览器控制台

未发现应用运行时错误。存在 Streamlit/Vega 图表渲染 warning，属于图表库对空/离散数据的提示，不影响页面加载和主要交互。

## 11. 截图路径

- `report/figures/ui_login.png`
- `report/figures/ui_student_dashboard.png`
- `report/figures/ui_teacher_dashboard.png`
- `report/figures/ui_admin_dashboard.png`

## 12. 仍需人工检查

- 在真实演示前，用当前本地凭据手动确认至少一次选课成功和退课成功；
- 用教师账号手动录入一条测试成绩，并确认 `score_change_log` 出现审计记录；
- 用管理员账号进入 `审计日志` 页面，确认筛选器和表格在真实演示数据下符合预期；
- 检查不同屏幕宽度下部分长表格是否需要横向滚动；
- 如果要对外展示，可补充更多截图，例如课程选课页、成绩录入页和管理员审计页。
