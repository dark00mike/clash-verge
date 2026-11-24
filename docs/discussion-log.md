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
