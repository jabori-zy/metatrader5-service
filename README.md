# MT5 Docker V2

一个单用户、启动时安装 MT5 和 Windows uv 的 MetaTrader 5 容器镜像：

- 1 用户 = 1 容器 = 1 Wine prefix = 1 MT5 = 1 KasmVNC 会话
- Wine 和离线安装资源在镜像构建期准备
- MT5 和 Windows `uv` 都在容器首次启动时安装到 `/config/.wine`
- 当前 `docker-compose.yml` 不持久化 `/config`
- `docker-compose.yml` 默认挂载当前仓库到 `/workspace/metatrader5-service`，供后续手工验证 HTTP 链路
- 用户登录信息、业务配置等应由外部数据库或调度层管理

## 前提

- Ubuntu EC2
- `amd64/x86_64`
- 已安装 Docker Engine 和 Docker Compose Plugin
- 安全组允许访问 `3000/tcp`

## 快速开始

1. 复制环境变量文件：

```bash
cp .env.example .env
```

2. 构建镜像：

```bash
docker build --platform linux/amd64 -t metatrader5-docker:dev .
```

3. 启动容器：

```bash
docker compose up -d
```

4. 打开浏览器：

```text
http://<ec2-public-ip>:3000
```

使用 `.env` 中的 `CUSTOM_USER` 和 `PASSWORD` 登录 KasmVNC。

如需后续手工验证 HTTP 链路，请先在 `.env` 中补齐：

```bash
HTTP_PORT=8000
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=
```

## 运行模型

- 运行时 Wine prefix 固定在 `/config/.wine`
- 容器启动时如果未检测到 `terminal64.exe`，会先执行 MT5 首次安装
- MT5 安装完成后，会继续安装 Windows `uv`
- 容器删除后，`/config/.wine`、日志和运行时状态都会一起删除
- 启动脚本会直接运行：

```text
wine "C:\Program Files\MetaTrader 5\terminal64.exe" /portable
```

- 如果设置了 `MT5_CMD_OPTIONS`，会追加到启动命令后面
- 运行期日志会同时输出到容器标准输出和 `/config/logs/mt5.log`
- 当前阶段只验证 `uv` 在 Wine 中可启动，HTTP 服务启动流程暂时禁用
- 当前 `docker-compose.yml` 已暴露 `HTTP_PORT` 并挂载服务源码，但 HTTP 仍需手工触发，不会自动启动
- 未来如需接入用户配置，建议由外部调度层按用户拉起容器，并通过环境变量或 secrets 注入配置引用

## 多用户部署方式

- 不要在单个容器里运行多个 Wine 环境
- 正确方式是在同一台 Docker 主机上运行多个此类容器
- 每个容器承载一个用户实例
- 由于基础环境已预装到镜像层，多容器会共享镜像层；每个容器仍会在首次启动时各自完成 MT5 安装
- 由于基础环境已预装到镜像层，多容器会共享镜像层；每个容器仍会在首次启动时各自完成 `/config/.wine` 初始化、MT5 安装和 Python 安装

## 常用命令

查看日志：

```bash
docker compose logs -f
```

进入容器：

```bash
docker compose exec mt5 bash
```

检查 MT5 进程：

```bash
docker compose exec mt5 pgrep -fa terminal64.exe
```

检查 MT5 是否已安装：

```bash
docker compose exec mt5 test -f '/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe'
```

检查 Windows uv：

```bash
docker compose exec mt5 bash -lc 'export WINEPREFIX=/config/.wine; wine "/config/.wine/drive_c/Program Files/uv/uv.exe" --version'
```

手工安装 Python：

```bash
docker compose exec mt5 bash -lc 'export WINEPREFIX=/config/.wine; cd /workspace/metatrader5-service/service; wine "/config/.wine/drive_c/Program Files/uv/uv.exe" python install 3.9.13'
```

手工同步服务依赖：

```bash
docker compose exec mt5 bash -lc 'export WINEPREFIX=/config/.wine; cd /workspace/metatrader5-service/service; wine "/config/.wine/drive_c/Program Files/uv/uv.exe" sync --frozen --no-install-project --python-platform windows'
```

检查离线资源：

```bash
docker compose exec mt5 bash -lc 'find /opt/installers /opt/wine-offline -maxdepth 3 -type f | sort'
```

## 仓库结构

```text
.
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── root/defaults/autostart
└── scripts
    ├── build
    │   ├── download-offline-assets.sh
    │   ├── install-mt5.sh
    │   ├── install-uv.sh
    │   └── preinstall-runtime.sh
    ├── lib
    │   └── common.sh
    └── runtime
        ├── bootstrap-prefix.sh
        ├── healthcheck.sh
        └── start-mt5.sh
```

## 注意事项

- 构建期只准备 Wine 和离线安装资源；Wine prefix、MT5 和 Windows uv 安装都发生在首次启动
- `mt5setup.exe` 仍然是官方引导安装器，首次启动安装 MT5 时依然可能联网下载 MT5 主体
- Windows `uv` 通过 GitHub Releases 的预编译二进制压缩包提供，当前阶段只验证 `uv --version`
- HTTP 相关脚本暂不接入容器启动链路；待 `uv` 管理 Python/venv 验证通过后再恢复
- 运行时不持久化本地数据，因此容器重建后不会保留运行期产生的文件
- `docker-compose.yml` 只是本地单实例 demo；生产环境应由外部编排系统按用户拉起多个容器
- KasmVNC 基础认证只适合开发/测试环境，不建议直接裸露到公网
