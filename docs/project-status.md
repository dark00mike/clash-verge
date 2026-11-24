# 当前项目状态

- 项目目标为设计和保存 Clash Verge 策略组及分流方案，按需维护。
- 最近更新为 2026-11-24 09:52（Asia/Shanghai）。对应讨论 `20261124-0952-v3-antigravity-stable`。
- 修改好的方案存放在 `version/`。当前默认方案为 `version/双订阅分流-v3.yaml`（针对 Antigravity 400 地区拦截与 SSE 长连接 `unexpected EOF` 做了粘性主备、CF 隔离、CloudCode 直测、TCP 保活与 `googleapis.com` 全量兜底）；`version/双订阅分流-v2.yaml` 与 `version/双订阅分流.yaml` 保留对照。
- 可复用校验脚本位于 `src/verify_antigravity_routing.py`，运行入口为 `python3 src/verify_antigravity_routing.py`。
- 本地运行订阅位于 `profiles/`，备份位于 `data/subscriptions/`。订阅和根目录 `geoip.metadb` 未线上备份。
- v3 已通过 `verge-mihomo -t`（含本机 Clash Verge 完整合并模拟）及 `src/verify_antigravity_routing.py` 全部 8 阶段端到端联网验证（主备锁定 `🇺🇸 美国 🄳` 出口 `179.255.150.157` US/Los Angeles，单条持久 TLS 6/6 无 EOF，`youtubei.googleapis.com` 保持走 `📺 YouTube`，其余业务规则无回归）。
- 远程地址和目录说明见 [README](../README.md)。本轮依据见 [讨论记录](discussion-log.md)和 [HTML 汇报](../outputs/reports/20261124-0952-v3-antigravity-stable.html)。
