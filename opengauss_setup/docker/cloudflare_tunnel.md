# Cloudflare Tunnel 接入

项目默认仍然让 Streamlit 监听本机 `8501`：

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

如果你的 Cloudflare Tunnel 跑在 Docker 里，origin 建议指向：

```text
http://host.docker.internal:8501
```

如果你的 Cloudflare Tunnel 跑在本机命令行，origin 指向：

```text
http://localhost:8501
```

当前机器上已有一个停止状态的 `cloudflare-tunnel` Docker 容器。项目迁移不需要修改 tunnel token；只要 tunnel 的公网域名规则转发到上面的 origin 即可。
