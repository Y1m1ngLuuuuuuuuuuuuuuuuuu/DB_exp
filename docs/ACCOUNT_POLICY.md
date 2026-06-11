# Account Policy

## 账号命名规则

本项目的演示账号使用业务身份编号作为登录名：

- 学生使用 `student.student_id` 登录，例如 `20240001`。
- 教师使用 `teacher.teacher_id` 登录，例如 `T001`。
- 管理员使用 `admin_profile.admin_id` 登录，例如 `A001`。

这样可以避免 `s_001`、`t_zhang`、`admin` 这类临时演示账号名与真实业务身份脱节。

## 密码与哈希

- 最终演示数据的初始密码由 `scripts/generate_large_demo_dataset.py` 生成；轻量样例账号也可由 `scripts/generate_demo_credentials.py` 单独刷新。
- 密码只包含大小写字母和数字，且至少包含一个大写字母、一个小写字母和一个数字。
- 后端认证逻辑位于 `services/auth_service.py`，使用 SHA-256 生成 64 位十六进制 `password_hash`。
- 数据库 `user_account` 表只保存 `password_hash`，不保存明文密码。

## 本地凭据文件

真实明文初始密码只保存在本地文件：

```text
secrets/DEMO_ACCOUNT_CREDENTIALS.md
```

该目录已加入 `.gitignore`，不应提交到公开仓库，也不应写入 LaTeX 报告正文。公开仓库只保留 `docs/DEMO_ACCOUNT_CREDENTIALS.example.md` 作为格式示例。

## 大规模演示账号

最终演示数据包含：

- 3 个管理员账号：`A001` 到 `A003`。
- 30 个教师账号：`T001` 到 `T030`。
- 100 个学生账号：`20240001` 到 `20240100`。

运行 `python3 scripts/generate_large_demo_dataset.py` 会同步生成本地 seed SQL 和 `secrets/DEMO_ACCOUNT_CREDENTIALS.md`。SQL 中只包含 SHA-256 哈希，明文初始密码仅保存在本地凭据文件中。

## 生产环境建议

生产环境不应长期使用演示初始密码。建议增加首次登录强制改密、密码重置流程、登录失败次数限制和更强的密码哈希算法，例如带盐的自适应哈希。
