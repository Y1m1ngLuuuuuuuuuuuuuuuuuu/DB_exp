# Database Privilege Binding

## 数据库角色设计

`opengauss_setup/sql/grant_roles_20260608.sql` 定义了四类数据库角色：

- `db_student_role`：面向学生侧查询，只授予必要视图的 `SELECT` 权限。
- `db_teacher_role`：面向教师侧查询成绩和教学任务，成绩写入仍应通过应用层事务和审计触发器。
- `db_admin_role`：面向数据库级维护，具备基础表和函数的维护权限。
- `db_app_role`：面向应用服务账号，允许通过受控函数、视图和必要基础表完成业务操作。

在 openGauss 中，权限分组角色使用 `NOLOGIN PASSWORD DISABLE` 创建，避免这些角色本身成为可登录账号；真正可登录的是本地演示绑定脚本中创建的少量数据库用户。

## 演示数据库登录账号绑定

真实数据库登录账号不应为每个学生单独创建。本项目采用“数据库角色分层 + 应用层业务身份”的方式：

- 应用运行时通常使用一个应用数据库账号连接 openGauss；
- 业务用户身份由 `user_account.role`、页面守卫和服务层权限检查控制；
- 数据库级角色用于限制账号能够直接访问的表、视图和函数。

本地演示绑定脚本由 `scripts/generate_demo_credentials.py` 生成：

```text
opengauss_setup/sql/local/grant_demo_db_accounts_20260611.sql
```

该脚本创建或绑定以下演示数据库登录账号：

- `db_app_demo_user` -> `db_app_role`
- `db_student_demo_user` -> `db_student_role`
- `db_teacher_demo_user` -> `db_teacher_role`
- `db_admin_demo_user` -> `db_admin_role`

由于该脚本包含数据库登录账号的随机密码，已放在 `opengauss_setup/sql/local/` 并加入 `.gitignore`。

## 为什么不为每个学生创建数据库账号

学生、教师和管理员是业务用户，不等同于数据库登录账号。若为每个学生创建数据库账号，会带来大量账号生命周期管理、密码重置、权限同步和审计复杂度。课程项目中更合理的做法是由应用层完成业务身份认证，由数据库层使用少量服务账号和角色控制最小权限。

## 演示环境与生产环境

当前课程演示环境主要通过配置文件中的应用账号连接数据库；`grant_roles_20260608.sql` 和本地生成的绑定脚本用于展示正式部署时的数据库最小权限方案。生产环境应将真实数据库账号绑定到这些角色，并把密码放入密钥管理系统或安全的环境变量中，而不是写入仓库。
