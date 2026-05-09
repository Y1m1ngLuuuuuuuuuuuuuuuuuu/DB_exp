# openGauss 设置目录

这个目录用于放 openGauss 版本相关的配置和迁移文件。当前项目根目录已经切换为 openGauss 连接；原 MySQL 版本快照保存在 `mysql_current_version_20260509/`。

## 目录结构

- `docker/docker-compose.yml`: 本地 openGauss 容器配置
- `docker/start_opengauss.sh`: 启动容器并初始化数据库
- `docker/init_db.sh`: 重置并导入 `course_system`
- `docker/cloudflare_tunnel.md`: Cloudflare Tunnel origin 设置说明
- `config/config_opengauss.py`: 项目连接配置样例
- `sql/init.sql`: openGauss 版建表、触发器、样本数据

## 常用命令

```bash
./opengauss_setup/docker/start_opengauss.sh
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```
