# openGauss 设置目录

这个目录用于放 openGauss 版本相关的配置、初始化脚本和运行说明。当前项目根目录已经切换为 openGauss 连接。

## 目录结构

- `docker/docker-compose.yml`: 本地 openGauss 容器配置
- `docker/start_opengauss.sh`: 启动容器并初始化数据库
- `docker/init_db.sh`: 重置并导入 `course_system`
- `docker/cloudflare_tunnel.md`: Cloudflare Tunnel origin 设置说明
- `config/config_opengauss.py`: 项目连接配置样例
- `sql/init.sql`: openGauss 版建表、约束、索引和样本数据
- `sql/migrate_3nf_20260608.sql`: 旧库迁移到 3NF 结构的审阅后执行脚本

## 常用命令

```bash
./opengauss_setup/docker/start_opengauss.sh
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```
