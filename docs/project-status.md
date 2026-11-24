# 当前项目状态

- 项目目标为设计和保存 Clash Verge 策略组及分流方案，按需维护。
- 最近更新为 2026-11-24 09:30（Asia/Shanghai）。对应讨论 `20261124-0930-move-verify-to-src`。
- 修改好的方案存放在 `version/`。`version/双订阅分流-v2.yaml` 是验证脚本的默认方案，`version/双订阅分流.yaml` 作为对照。
- 可复用校验脚本已收拢至 `src/verify_antigravity_routing.py`，运行入口为 `python3 src/verify_antigravity_routing.py`。
- 本地运行订阅位于 `profiles/`，备份位于 `data/subscriptions/`。订阅和根目录 `geoip.metadb` 未线上备份。
- 已通过迁移后脚本的 Python 语法、根目录 `WORKSPACE` 解析、本地订阅路径可达性以及两份方案的 `verge-mihomo -t` 配置校验；联网节点连通性与路由命中按需在方案迭代时通过脚本验证。
- 远程地址和目录说明见 [README](../README.md)。本轮依据见 [讨论记录](discussion-log.md)和 [HTML 汇报](../outputs/reports/20261124-0930-move-verify-to-src.html)。
