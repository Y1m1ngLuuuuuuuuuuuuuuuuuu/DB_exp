# UI Screenshot TODO

自动化截图过程中，登录页、学生首页、教师首页和管理员首页已经具备真实截图。课程选课、课表、成绩录入和审计日志等页面需要在本地浏览器中使用演示账号进入后人工截图，避免因自动化登录限制导致截取失败或误操作业务数据。

## 截图前准备

1. 启动 openGauss：
   ```bash
   cd /Users/lu/Code/Python/DB_exp/Big
   ./opengauss_setup/docker/start_opengauss.sh
   ```
2. 启动 Streamlit：
   ```bash
   cd /Users/lu/Code/Python/DB_exp/Big
   .venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1
   ```
3. 打开：
   ```text
   http://127.0.0.1:8501
   ```
4. 从本地 `secrets/DEMO_ACCOUNT_CREDENTIALS.md` 查看演示账号密码。不要把该文件内容录入报告或视频画面。

## 待截图页面

| 文件名 | 登录角色 | 操作路径 | 截图重点 |
| --- | --- | --- | --- |
| `report/figures/ui/03_student_course_selection.png` | 学生 | 登录学生账号 -> 课程选课 | 筛选条、课程卡片、容量、选课按钮 |
| `report/figures/ui/04_student_timetable.png` | 学生 | 课程选课 -> 课表标签页或学生首页课表区域 | 星期、节次、课程、教师、教室 |
| `report/figures/ui/05_student_grades.png` | 学生 | 成绩与绩点 | 成绩、学分、状态、绩点 |
| `report/figures/ui/07_teacher_score_entry.png` | 教师 | 登录教师账号 -> 成绩管理 | 教学班、学生名单、成绩录入、确认保存 |
| `report/figures/ui/09_admin_course_management.png` | 管理员 | 登录管理员账号 -> 开课安排或课程维护 | 课程、教师、学期、教室、容量 |
| `report/figures/ui/10_admin_score_audit.png` | 管理员 | 登录管理员账号 -> 审计日志 | old_score、new_score、changed_by、changed_at、reason |

## 截图要求

- 截图不要包含明文密码。
- 截图不要展示 `secrets/` 目录。
- 成绩录入和选课操作如需演示，应使用测试数据或确认可以回滚。
- 截图完成后更新 `report/UI_SCREENSHOT_INDEX.md`，并在 LaTeX 中增加对应 figure。
