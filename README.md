# Clash Verge 策略组方案

设计、校验和保存 Clash Verge / Mihomo 的双订阅策略组及分流规则。本项目按需维护，无定期业务任务。远程仓库见 [GitHub](https://github.com/dark00mike/clash-verge)。

## 目录

| 路径 | 用途 |
| --- | --- |
| `version/` | 策略组与分流方案，承担项目配置目录的职责。修改好的方案放在这里。 |
| `profiles/` | 方案通过 `proxy-providers` 读取的本地订阅配置。 |
| `data/subscriptions/` | 本地订阅原件备份，分别以 `飞鸟云.yaml` 和 `喵子.yaml` 保存。 |
| `docs/` | [当前状态](docs/project-status.md)和[讨论记录](docs/discussion-log.md)。 |
| `outputs/reports/` | 每轮任务的离线 HTML 汇报。 |
| `reference/` | 外部资料与参考笔记。空目录可在克隆后用 `mkdir -p reference` 补齐。 |
| `skills/` | 项目自带的 [project-manager 技能](skills/project-manager/SKILL.md)。 |
| `src/` | 存放可复用的校验与辅助脚本，当前入口为 [verify_antigravity_routing.py](src/verify_antigravity_routing.py)。 |
| `geoip.metadb` | 本地 GeoIP 数据，供 Mihomo 配置校验使用。 |

## 策略组方案

- [双订阅分流 v3](version/双订阅分流-v3.yaml)是校验脚本的当前默认方案：在 v2 基础上针对 Antigravity SSE 长连接 `unexpected EOF` 与地区拦截做了稳态加固（默认粘性主备 `Antigravity 美国稳态主备`、排除 Cloudflare 中转 `🇺🇸 美国 🄲` 出自动/主备池、直测 `daily-cloudcode-pa.googleapis.com`、开启 15s TCP keep-alive、并在保护 `youtubei.googleapis.com` 的前提下以 `googleapis.com` 全量兜底）。
- [双订阅分流 v2](version/双订阅分流-v2.yaml)保留对照（双订阅美国 `url-test` + `sniffer` 方案）。
- [双订阅分流 v1](version/双订阅分流.yaml)保留对照，部分进程路径规则使用本机路径。
- 日常方案修改通过 Git 提交保存，正式冻结使用 Git 标签。

## 本机校验

从项目根目录运行。脚本需要 Python 3、PyYAML、`/usr/bin/verge-mihomo`，完整校验还会使用本机 Antigravity 和网络连接。

```bash
python3 src/verify_antigravity_routing.py
python3 src/verify_antigravity_routing.py version/双订阅分流-v3.yaml
```

两份方案均通过 Mihomo 数据目录下的 `profiles/` 读取订阅。克隆后，从 Clash Verge 导出对应订阅，按方案中的 provider 路径放回。若本机有备份，`data/subscriptions/飞鸟云.yaml` 对应 `profiles/RTDoapXPR1dR.yaml`，`data/subscriptions/喵子.yaml` 对应 `profiles/RQFkMMru5OhB.yaml`。可从本机 Mihomo 数据目录补齐该版本使用的 GeoIP 文件。订阅原件和 GeoIP 数据只保存在本机，未线上备份。

## 项目维护

AI 协作入口见 [AGENTS.md](AGENTS.md)。如需手动清理 `.tmp/disposable/`，在项目根目录运行以下命令。 [维护规则](skills/project-manager/references/maintenance.md)

```bash
python3 -X utf8 skills/project-manager/scripts/clean_temp.py --root "$PWD"
```
