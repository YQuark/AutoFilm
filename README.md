[license]: /LICENSE
[license-badge]: https://img.shields.io/github/license/yquark/AutoFilm?style=flat-square&a=1
[prs]: https://github.com/yquark/AutoFilm
[prs-badge]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square
[issues]: https://github.com/yquark/AutoFilm/issues/new
[issues-badge]: https://img.shields.io/badge/Issues-welcome-brightgreen.svg?style=flat-square
[release]: https://github.com/yquark/AutoFilm/releases/latest
[release-badge]: https://img.shields.io/github/v/release/yquark/AutoFilm?style=flat-square
[docker]: https://hub.docker.com/r/yquark/autofilm
[docker-badge]: https://img.shields.io/docker/pulls/yquark/autofilm?color=%2348BB78&logo=docker&label=pulls

<div align="center">

# AutoFilm

**一个为 Emby、Jellyfin 服务器提供直链播放的小项目** 

[![license][license-badge]][license]
[![prs][prs-badge]][prs]
[![issues][issues-badge]][issues]
[![release][release-badge]][release]
[![docker][docker-badge]][docker]


[说明文档](#说明文档) •
[部署方式](#部署方式) •
[Strm文件优点](#Strm文件优点) •
[TODO LIST](#todo-list) •
[更新日志](#更新日志) •
[贡献者](#贡献者) •
[Star History](#star-history)

</div>

# 说明文档
详情见 [AutoFilm 说明文档](https://blog.akimio.top/posts/1031/)

# 部署方式
1. Docker 运行
    ```bash
    docker run -d --name autofilm -p 8000:8000 -e AUTOFILM_WEB_ENABLED=true -v ./config:/config -v ./media:/media -v ./logs:/logs yquark/autofilm
    ```
    或使用 Docker Compose：
    ```bash
    docker compose pull
    docker compose up -d
    ```
2. Python 环境运行（Python3.12）
    ```bash
    python app/main.py
    ```

## 手动触发任务
```bash
# 立即执行指定 ID 的任务（执行完退出）
python app/main.py --run AV

# 立即执行所有任务（执行完退出）
python app/main.py --run-all
```
> Docker 环境可通过 `docker exec` 执行：`docker exec autofilm python /app/main.py --run AV`

## Web UI / API
v2.0.0 新增轻量 Web UI 与 API。`docker-compose.yml` 默认启用 Web；直接运行 Docker 时可通过 `-e AUTOFILM_WEB_ENABLED=true` 启用。也可以在 `Settings` 中增加：
```yaml
web_enabled: True
web_host: 0.0.0.0
web_port: 8000
web_token: "change-me"
```

- Web UI: `http://localhost:8000/`
- 健康检查: `GET /health`
- 任务列表: `GET /api/tasks`
- 手动触发: `POST /api/tasks/{module}/{id}/run`
- 最近运行: `GET /api/tasks/{module}/{id}/runs/latest`

当 `web_token` 非空时，触发任务需要请求头：`Authorization: Bearer change-me`。

v2.1.0 起 Web UI 升级为运维控制台，支持任务仪表盘、运行历史、配置摘要、主题/密度/视图偏好，以及带备份和校验的 `config.yaml` 编辑。配置写操作强制要求 `web_token`，未设置时仅提供只读配置视图。

# Strm文件优点
- [x] 轻量化 Emby 服务器，降低 Emby 服务器的性能需求以及硬盘需求
- [x] 运行稳定
- [x] 相比直接访问 Webdav，Emby、Jellyfin 服务器可以提供更好的视频搜索功能以及自带刮削器，以及多设备同步播放进度
- [x] 提高访问速度，播放速度不受 Emby / Jellyfin 服务器带宽限制（需要使用 [MediaWarp](https://github.com/AkimioJR/MediaWarp)）

# TODO LIST
- [x] 从 config 文件中读取配置
- [x] 优化程序运行效率（异步处理）
- [x] 增加 Docker 镜像
- [x] 本地同步网盘
- [x] Alist 永久令牌
- [x] LibraryPoster（媒体库海报）-> 已移除（v1.6.0 代码精简）
- [x] 通知功能（Telegram / Bark / Webhook）
- [x] 配置文件热重载（修改 config.yaml 无需重启）
- [x] 增量扫描（跳过未变更文件，大幅减少重复运行时间）
- [x] 使用 API 触发任务（v2.0.0 轻量 API / Web UI）
- [ ] ~~对接 TMDB 实现分类、重命名、刮削等功能~~
    > 已经向 [MoviePilot](https://github.com/jxxghp/MoviePilot) 提交支持对 Alist 服务器文件的操作功能的 PR，目前已经合并进入主线分支，可以直接使用 MoviePilot 直接刮削

# 更新日志
- 2026.5.11：v2.1.0，全面升级 Web UI 为内置无构建运维控制台：新增任务仪表盘、运行历史、配置摘要、深浅色/密度/表格卡片视图自定义；新增配置编辑器，支持 Settings 表单编辑、完整 YAML 校验与保存、自动备份和备份恢复；配置写接口强制 Web Token，未配置 Token 时保持只读；新增配置摘要脱敏与备份目录忽略。
- 2026.5.11：v2.0.0，平台化大版本：新增统一任务注册与运行状态持久化，支持轻量 Web UI / API 查看任务、手动触发任务、查询最近运行结果；任务调度 ID 改为模块隔离，避免 Alist2Strm / Ani2Alist 同名任务冲突；修复 HTTP 分片下载 headers 共享导致 Range 串扰的风险；增强配置容错、other_ext 解析和 Docker entrypoint 的 YAML 解析；README Docker 镜像名统一为 yquark/autofilm。
- 2026.5.11：v1.6.0，新增通知模块（Telegram / Bark / Webhook 推送，任务开始/完成/失败/保护触发自动通知）；新增配置文件热重载（修改 config.yaml 无需重启容器，自动 diff 增删改定时任务）；新增增量扫描（持久化文件清单，后续运行跳过未变更文件，大幅减少重复扫描开销）；移除 LibraryPoster 模块及 photo/fonts/numpy/scikit-learn/pillow/pypinyin 依赖链；移除孤立模块 filetransfer/extensions.media/StringsUtils；移除 AlistUtils.sign/URLUtils.get_resolve_url 等死方法；清理 AlistPath 未使用字段和 demo __main__ 块；Docker 镜像精简（移除 fonts 目录及可选依赖安装）
- 2026.5.10：v1.5.3，目录遍历并行化（同级子目录并发扫描，大幅提升大库遍历速度）；新增 `--run` / `--run-all` 手动触发模式；容器启动时立即执行首次任务；代码审计修复（可变默认参数、Range header、Token 竞态、TOCTOU 等）；删除未使用的 themoviedb 模块；numpy/scikit-learn 改为可选依赖
- 2025.9.26：v1.5.0，支持 BDMV 蓝光原盘文件结构，引入 Alist2StrmMode 枚举以简化模式管理，优化 LibraryPoster 对多路径媒体库的处理
- 2025.7.14：v1.4.0，修复 Ani2Alist 模块时间解析问题，新增 LibraryPoster 美化媒体库封面模块
- 2025.5.29：v1.3.3，Alist2Strm 模块支持添加删除空目录的功能；提高 Alist V3.45 兼容性；添加 m2ts 视频文件后缀到视频扩展集合；修复视频扩展集合中".wmv"缺失前缀错误
- 2025.4.4：v1.3.2，添加 .mpg 视频文件后缀；优化重试装饰器；优化重试装饰器；新增遍历文件间隔时间，防止被风控；修正部分方法名、返回变量类型、文档表述错误
- 2025.3.15：v1.3.1，修复重试装饰器参数类型错误；在 AlistStorage 中添加 model_config 以忽略特定类型避免 Cython 编译后无法使用；修改 AlistClient 中的异常捕获以避免捕获其他异常；使用 Cython 对 Docker 容器内的 py 文件编译，提高性能
- 2025.3.12：v1.3.0，增加汉字转拼音相关工具；修复 AlistStorage 属性调用错误问题；修复 RSS 订阅更新对 storage.addition2dict 结构中 url_structure 的处理；修复无法仅 token 实例化 AlistClient 对象问题；优化 Ani2Alist 运行逻辑；优化 Ani2Alist 性能，减少 URL 解码次数；优化 Alist2Strm 支持判断本地文件是否过期或损坏而进行重新处理
- 2025.1.10：v1.2.6 使用 RequestUtils 作为全局统一的 HTTP 请求出口、更新 Docker 镜像底包、Alist2Strm 新增同步忽略功能
- 2024.11.8：v1.2.5，Alist2Strm 模块新增同步功能；优化 AlistClient，减少 token 申请；支持使用永久令牌；优化日志功能
- 2024.8.26：v1.2.4，完善 URL 中文字符编码问题；提高 Python3.11 兼容性；Alist2Strm 的 mode 选项
- 2024.7.17：v1.2.2，增加 Ani2Strm 模块
- 2024.7.8：v1.2.0，修改程序运行逻辑，使用 AsyncIOScheduler 实现后台定时任务
- 2024.6.3：v1.1.0，使用 alist 官方 api 替代 webdav 实现“扫库”；采用异步并发提高运行效率；配置文件有改动；支持非基础路径 Alist 用户以及无 Webdav 权限用户
- 2024.5.29：v1.0.2，优化运行逻辑；Docker 部署，自动打包 Docker 镜像
- 2024.2.1：v1.0.0，完全重构 AutoFilm ，不再兼容 v0.1 ；实现多线程，大幅度提升任务处理速度
- 2024.1.28：v0.1.1，初始版本持续迭代

# 贡献者
<a href="https://github.com/yquark/AutoFilm/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yquark/AutoFilm" />
</a>

