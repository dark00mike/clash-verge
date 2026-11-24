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

## 20261124-0952-v3-antigravity-stable · 基于 SSE 断流与地区拦截分析迭代 `双订阅分流-v3`

- 时间为 2026-11-24 09:52（Asia/Shanghai）。
- 用户补充了来自 `database` 排查的根因结论（400 地区拦截 + SSE 长连接 `unexpected EOF` 双会话同秒断流），决定基于该结论设计并上传 v3 方案。本决定取代 `20261124-0920-layout` / `20261124-0930-move-verify-to-src` 中“默认方案为 v2”的约定，默认方案升级为 `version/双订阅分流-v3.yaml`（v2 与 v1 保留对照）。
- 实测依据（09:46 全部 15 个美国节点直测）：喵子 `🇺🇸 美国 🄳`（DMIT 洛杉矶直连）139–146ms 全天稳定；`🇺🇸 美国 🄼` 虽然 `gstatic` 644ms 可通但 `daily-cloudcode-pa` 超时；`🇺🇸 美国 🄲`（Cloudflare 中转）超时且易在长连接静默期断流；飞鸟云白天有 9 个美国节点恢复可用（如 `美国02`/`03`/`05`/`09`，149–170ms，实测均落地洛杉矶 Akamai/Linode），凌晨曾全超时。
- 实际改动：
  - 新增 `version/双订阅分流-v3.yaml`：显式开启 TCP 保活 `keep-alive-idle: 15` / `keep-alive-interval: 15`；将喵子美国节点按无重叠分区拆分为 `antigravity-miaoz-direct` / `antigravity-miaoz-transit` / `antigravity-miaoz-cf`，配合 `antigravity-feiniaoyun` 全部改为直测 `https://daily-cloudcode-pa.googleapis.com`（`expected-status: 200/401/403/404`）；`Antigravity` 默认策略改为粘性 `Antigravity 美国稳态主备`（`fallback`：`🇺🇸 美国 🄳` → 飞鸟云美国 → `🇺🇸 美国 🄼`，把 `🇺🇸 美国 🄲` 移出自动与主备池）；规则层在保护 `DOMAIN,youtubei.googleapis.com,📺 YouTube` 前提下新增 `DOMAIN-SUFFIX,googleapis.com,Antigravity` 全量兜底。
  - 升级 `src/verify_antigravity_routing.py`：默认指向 `version/双订阅分流-v3.yaml`，新增 TCP keep-alive 核验、CF 隔离校验、单条持久 TLS keep-alive 连续 6 次请求防 EOF 检测及 `youtubei.googleapis.com` 防误伤校验。
  - 同步更新 `README.md`、`docs/project-status.md` 与本轮 HTML 汇报。
- 验证：`verge-mihomo -t` 独立校验与本机 Clash Verge 全合并模拟（含 TUN、`Merge.yaml`、`Script.js`）均 3ms 通过；`python3 -B src/verify_antigravity_routing.py version/双订阅分流-v3.yaml` 8 个阶段全部 46 项 100% 通过（主备默认锁定 `🇺🇸 美国 🄳` 出口 `179.255.150.157` US/Los Angeles DMIT，持久 TLS 连接 6/6 无 EOF，自动组切换到 `美国12` 出口 `172.233.149.182` US，`youtubei.googleapis.com` 保持走 `📺 YouTube`）。
- 附本机客户端配套建议（YAML 之外）：关闭两份远程订阅的后台 `allow_auto_update` 避免任务中途触发核心重载，长任务期间避免手动切节点（或关闭 `auto_close_connection`），并可按需测试纯 TUN 或将 TUN 栈由 `gvisor` 切为 `mixed`。
- [本轮 HTML 汇报](../outputs/reports/20261124-0952-v3-antigravity-stable.html)
