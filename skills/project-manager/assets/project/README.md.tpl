# {{NAME}}

{{PURPOSE}}

## 接手入口

先读 [AI 协作规则](AGENTS.md)、[当前状态](docs/project-status.md) 和 [最近讨论](docs/discussion-log.md)。
[管理 Skill](skills/project-manager/SKILL.md) 已随项目保存，项目专用技能继续放 skills，以项目副本为版本依据。

## 实际目录

项目类型：**{{PROJECT_TYPE}}**。下表是本项目确定的目录约定。
定期业务任务：{{RECURRING_TASKS}}。

| 目录 | 用途 |
|---|---|
{{FOLDER_ROWS}}

基础目录为 docs、outputs、skills、reference、data、config；有定期业务任务时加入 state、logs。其他目录按项目类型、实际职责和已有惯例确定，src 等代码目录名称只是示例。确定后保持稳定，不因某轮未使用或暂时为空而增删、改名；只有类型或长期职责变化时才调整，同时更新本表并记录原因。任务/run 子目录和临时、工具目录按需建立。

Git 不保存空目录，不制造占位文件；克隆后按本表补齐本项目约定需要的空目录。

| 潜在目录（不自动创建） | 适用职责；纳入时更新本表及讨论记录 |
|---|---|
| 测试、运行工具目录 | 有代码且确需时，沿用项目或框架的位置约定。 |
| outputs/releases/ | 需要独立冻结交付包时。 |
| .tmp/ | work 放活跃临时内容，disposable 放确定无用、等待手动清理的文件。 |
| .codegraph/、.venv/、工具配置目录 | 工具实际需要时建立并保持隐藏。 |

运行结果放 outputs/runs，HTML 放 outputs/reports。通用步骤按职责集中实现并导入复用，相关步骤合并，具体代码规则见 AGENTS。

## 手动清理

用户提出清理请求后，由 AI 按[维护规则](skills/project-manager/references/maintenance.md)执行；也可在项目根目录手动运行：

```text
python -X utf8 skills/project-manager/scripts/clean_temp.py --root "<项目绝对路径>"
```

只删除 .tmp/disposable 中确定无用的内容，不配置定时清理，普通任务收尾不默认删除。

## 运行与版本

尚未开展业务任务。首项业务任务完成后补充实际操作方法、运行命令（如有）和输入来源。

线上仓库：`{{REMOTE}}`。每轮实质结论保存 Git 提交并推送，正式冻结用标签；必要的独立包从指定标签导出。凭据、原始私有输入、受限原件和大型产物按实际存储方案处理，未上传材料标明保存/获取位置。

[初始化汇报](outputs/reports/{{ITERATION}}.html)；后续最新报告与 Git 同步状态见当前状态。
