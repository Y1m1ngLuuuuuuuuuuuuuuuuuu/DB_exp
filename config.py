# config.py —— 全局配置
# 修改此文件以适配你的本地 Docker MySQL 环境

# ── 数据库连接 ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     3306,
    "user":     "root",
    "password": "123",
    "database": "course_system",
    "charset":  "utf8mb4",
}

# ── 应用基础配置 ─────────────────────────────────────────────
APP_TITLE   = "选课管理系统"
APP_ICON    = "📚"

# 密码哈希算法（与 init.sql 中 SHA2(..., 256) 保持一致）
PASSWORD_HASH_ALGO = "sha256"
