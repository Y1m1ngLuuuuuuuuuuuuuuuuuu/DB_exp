# 学生选课成绩管理系统

基于 Python + Streamlit + PyMySQL + Docker MySQL 的 Web 选课系统，实现学生选课、成绩管理和基础信息维护等核心功能。

---

## 功能概览

系统支持三种登录角色，各自拥有独立的功能页面。

### 学生端

| 功能 | 说明 |
|------|------|
| 登录 | 用户名 + 密码验证，登录后自动跳转学生页面 |
| 我的选课 | 查看当前学期可选课程，点击选课；查看已选课程，可退课 |
| 我的成绩单 | 查看全部已修课程的成绩、学分、任课教师；统计平均分与加权绩点 |

选课限制：容量已满禁止选课；先修课程未通过（成绩 < 60）禁止选后续课；已有成绩的课程不允许退课；选课只在学期开放的时间窗口内有效。

### 教师端

| 功能 | 说明 |
|------|------|
| 成绩管理 | 查看自己负责的开课班次，批量录入或修改学生成绩；查看成绩分布图；查看该班次的历史修改日志 |

教师只能操作自己名下的班次，不能修改其他教师的成绩。

### 管理员端

| 功能 | 说明 |
|------|------|
| 管理员首页 | 系统概览：在籍学生数、在职教师数、开放课程数、本期选课数；各班次选课情况表；各院系学生人数柱状图 |
| 学期管理 | 新增学期，设置学期名称、起止日期、选课开放时间和状态（未开放 / 选课中 / 已结束） |
| 开课安排 | 为课程分配任课教师、教室和学期，设置容量上限和上课时间；支持编辑和删除班次（有学生在选时禁止删除） |
| 课程维护 | 新增、修改、删除课程（有开课安排时禁止删除）；维护课程号、名称、类型、学分、学时、所属院系 |
| 成绩管理 | 全局查看所有班次成绩，批量录入修改；查看成绩分布图和修改日志 |
| 学生维护 | 新增、修改、删除学生；同步维护登录账号 |
| 教师维护 | 新增、修改、删除教师（有开课记录时禁止删除）；同步维护登录账号 |

---

## 数据库设计

共 13 张表，分为四个层次。

### 组织结构（3 张）

| 表名 | 说明 |
|------|------|
| `department` | 院系：编号、名称、联系电话、办公地点 |
| `major` | 专业：编号、名称，归属某院系 |
| `classroom` | 教室：楼栋、房间号、容量 |

### 用户与身份（4 张）

| 表名 | 说明 |
|------|------|
| `user_account` | 统一账号表，存储登录名、SHA-256 密码、角色（admin/student/teacher）和账号状态 |
| `student` | 学生详细信息：学号、姓名、性别、入学年、所属专业、班级、邮箱 |
| `teacher` | 教师详细信息：教师号、姓名、性别、所属院系、职称、邮箱 |
| `admin_profile` | 管理员详细信息 |

### 教学安排（3 张）

| 表名 | 说明 |
|------|------|
| `semester` | 学期：名称、起止日期、选课开放时间、状态 |
| `course` | 课程定义：课程号、名称、类型（必修/选修/公共）、学分、学时、开课院系 |
| `course_offering` | 开课班次：某学期某教师开设的具体课次，包含教室、容量上限、上课时间；`selected_count` 由触发器自动维护 |

### 选课与成绩（3 张）

| 表名 | 说明 |
|------|------|
| `course_prerequisite` | 先修关系：记录课程之间的先后依赖 |
| `enrollment` | 选课记录：学生与开课班次的多对多关系，存储选课状态和最终成绩、绩点 |
| `score_change_log` | 成绩修改日志：每次成绩变更均记录修改前后的值、操作人和原因 |

---

## 项目文件说明

```
.
├── app.py                    # Streamlit 入口：页面配置、session 初始化、角色路由和侧边栏导航
├── config.py                 # 数据库连接参数和应用基础配置
├── requirements.txt          # Python 依赖列表
│
├── sql/
│   └── init.sql              # 建库建表脚本，含触发器和样本数据，首次部署时执行一次
│
├── db/
│   ├── __init__.py           # 统一导出数据库工具函数
│   └── connection.py         # 数据库连接管理
│                             #   get_connection()    获取 PyMySQL 连接（DictCursor）
│                             #   DBSession           上下文管理器，自动提交/回滚
│                             #   query(sql, args)    SELECT → list[dict]
│                             #   query_one(sql, args)SELECT → dict | None
│                             #   execute(sql, args)  INSERT/UPDATE/DELETE → (rows, last_id)
│                             #   execute_many(...)   批量执行
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py       # 登录认证：SHA-256 密码校验、更新最近登录时间、获取学生/教师 ID
│   ├── student_service.py    # 学生 CRUD：查询、新增（含账号）、修改、删除
│   ├── teacher_service.py    # 教师 CRUD：查询、新增（含账号）、修改、删除（有班次时拒绝）
│   ├── course_service.py     # 课程与开课班次：
│   │                         #   学期 CRUD（list/create/update）
│   │                         #   课程 CRUD（list/create/update/delete）
│   │                         #   开课班次 CRUD（list/create/update/delete）
│   │                         #   学生可选课程查询、已选课程查询
│   ├── selection_service.py  # 选课业务：选课（含容量/时间/先修检查）、退课、恢复选课
│   └── score_service.py      # 成绩管理：绩点计算、成绩录入与更新、分布统计、修改日志查询
│
└── pages/
    ├── __init__.py
    ├── _guards.py            # 权限守卫：require_role(*roles)，未登录或角色不符时终止渲染
    ├── login.py              # 登录页：表单 + 认证 + session 写入
    ├── admin_dashboard.py    # 管理员首页：四格统计指标 + 班次选课表 + 院系学生分布图
    ├── semester_manage.py    # 学期管理：学期列表、新增、编辑（日期、状态）
    ├── offering_manage.py    # 开课安排：班次列表、新增班次（课程+教师+教室+时间）、编辑、删除
    ├── course_manage.py      # 课程维护：课程列表、新增、修改、删除
    ├── score_manage.py       # 成绩管理：批量录入（data_editor）+ 成绩分布图 + 修改日志
    ├── student_manage.py     # 学生维护：搜索列表、新增、修改、删除
    ├── teacher_manage.py     # 教师维护：搜索列表、新增、修改、删除
    ├── student_select.py     # 学生选课：可选课程列表（含选课按钮）+ 已选课程列表（含退课按钮）
    └── student_report.py     # 学生成绩单：统计指标（已修门数/累计学分/平均分/加权绩点）+ 成绩表
```

---

## 测试账号

所有账号初始密码均为 `123456`。

| 用户名 | 角色 | 姓名 | 备注 |
|--------|------|------|------|
| `admin` | 管理员 | 系统管理员 | 全局权限 |
| `t_zhang` | 教师 | 张明 | 计算机学院·副教授 |
| `t_li` | 教师 | 李晓华 | 数学学院·讲师 |
| `t_wang` | 教师 | 王志强 | 计算机学院·讲师 |
| `t_sun` | 教师 | 孙敏 | 数学学院·副教授 |
| `s_001` | 学生 | 王小明 | 计科2401班 |
| `s_004` | 学生 | 赵雨桐 | 计科2402班 |
| `s_006` | 学生 | 林可欣 | 软工2401班 |
| `s_009` | 学生 | 许嘉宁 | 数学2401班 |
| `s_012` | 学生 | 冯博文 | 数学2402班 |

---

## 部署与启动

### 前置要求

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行
- [Anaconda / Miniconda](https://www.anaconda.com/) 已安装
- Python 3.10 或以上

---

### 第一步：启动 MySQL 容器

```bash
docker run -d \
  --name course-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=123 \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

等待约 10 秒让 MySQL 完成初始化，可用以下命令确认容器状态：

```bash
docker ps
```

看到 `course-mysql` 的 STATUS 为 `Up` 即可继续。

---

### 第二步：初始化数据库

```bash
docker exec -i course-mysql mysql -uroot -p123 < sql/init.sql
```

此命令会创建 `course_system` 数据库、所有表、触发器，并导入样本数据。**只需执行一次。**

---

### 第三步：创建并激活 Python 环境

```bash
conda create -n db_st python=3.11 -y
conda activate db_st
pip install -r requirements.txt
```

---

### 第四步：启动应用

```bash
streamlit run app.py
```

浏览器会自动打开，或手动访问：

```
http://localhost:8501
```

---

### 日常重启（容器已存在时）

如果容器已经创建过，重启电脑后只需：

```bash
# 重启容器
docker start course-mysql

# 激活环境并启动应用
conda activate db_st
streamlit run app.py
```

---

### 修改数据库连接参数

如果你的 MySQL 密码或端口与默认值不同，编辑 `config.py`：

```python
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     3306,        # MySQL 映射到本机的端口
    "user":     "root",
    "password": "123",       # 与 docker run -e MYSQL_ROOT_PASSWORD 一致
    "database": "course_system",
    "charset":  "utf8mb4",
}
```

---

### 重置数据库

如需清空所有数据并重新初始化：

```bash
docker exec -i course-mysql mysql -uroot -p123 -e "DROP DATABASE IF EXISTS course_system;"
docker exec -i course-mysql mysql -uroot -p123 < sql/init.sql
```
