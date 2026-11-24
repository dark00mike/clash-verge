# 讨论记录

按时间追加。结论变更时注明被取代的条目。

## 20261124-0920-layout · 按 projman 整理策略组项目

- 时间为 2026-11-24 09:20（Asia/Shanghai）。
- 用户要求按 projman 完善目录，并明确修改好的版本方案放入 `version/`。该目录承担项目配置目录的职责。
- `version/双订阅分流.yaml` 和 `version/双订阅分流-v2.yaml` 保留原有方案内容。验证脚本默认读取 v2，显式配置路径继续按原有规则解析。
- 原先 `version/` 下的 `飞鸟云.yaml` 和 `喵子.yaml` 移到 `data/subscriptions/`。两者与 `profiles/` 中对应的运行文件逐字节一致。Git 忽略这两个目录中的订阅原件及 GeoIP 本地数据。
- 补齐 README、AGENTS、当前状态、讨论记录、汇报及参考目录，保留项目技能。以用户提供的 GitHub 仓库作为 `origin`，默认分支为 `main`，提交身份沿用本机其他项目使用的 GitHub 隐私邮箱。
- 两份方案通过 `verge-mihomo -t`；方案引用的本地订阅文件存在，验证脚本通过语法和路径检查。全链路联网验证留待需要时执行。
- [本轮 HTML 汇报](../outputs/reports/20261124-0920-layout.html)

## 20261124-0930-move-verify-to-src · 将验证脚本迁入 `src/`

- 时间为 2026-11-24 09:30（Asia/Shanghai）。
- 用户决定将根目录下的 `verify_antigravity_routing.py` 移入 `src/`。本决定取代 `20261124-0920-layout` 中验证脚本位于根目录的布局约定，其余目录约定保持不变。
- 实际改动：创建 `src/` 并迁移 `verify_antigravity_routing.py` -> `src/verify_antigravity_routing.py`；将脚本中 `WORKSPACE` 调整为向上取项目根目录并同步顶部 `Usage` 示例；更新 `README.md` 目录表与本机校验命令。
- 验证：脚本通过 Python AST 语法检查与模块导入路径检查（`WORKSPACE` 正确指向项目根目录，`profiles/` 与默认方案 `version/双订阅分流-v2.yaml` 可访问）；以 `WORKSPACE` 为数据目录运行 `verge-mihomo -t`，`version/双订阅分流-v2.yaml` 与 `version/双订阅分流.yaml` 均通过。本次为目录迁移，未重跑全链路联网探测。
- 下一步：后续可复用脚本继续收拢在 `src/`，策略组方案继续保存在 `version/`。
- [本轮 HTML 汇报](../outputs/reports/20261124-0930-move-verify-to-src.html)
