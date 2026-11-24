#!/usr/bin/env python3
"""Create a lean project in an empty directory; never commit, push or start tasks."""

import argparse
import ctypes
from datetime import datetime, timedelta, timezone
import html
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
FOLDERS = {
    "src": "当前业务代码、必要测试和可复用运行工具。",
    "docs": "沟通结论、当前状态及 AI 接手上下文。",
    "outputs": "运行结果在 runs；HTML 汇报在 reports。",
    "reference": "外部参考资料及综合研究笔记。",
    "skills": "随项目保存的管理 Skill 及其他项目独立技能。",
    "data": "本地输入或正式加工数据；默认不上传 Git。",
    "config": "非秘密业务配置；框架要求的根配置保留原位。",
    "state": "增量任务的持久检查点/水位；默认留本地。",
    "logs": "定期业务任务的执行日志；默认留本地。",
}


def online_remote(value):
    """Accept HTTPS/SSH repositories, rejecting local paths and embedded secrets."""
    if re.fullmatch(r"[\w.-]+@[^\s/:\\]+:[^\s\\]+", value):
        return value
    parsed = urlsplit(value)
    if (
        parsed.scheme in {"https", "ssh"}
        and parsed.hostname
        and parsed.path.strip("/")
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
        and not any(c.isspace() for c in value)
        and not (parsed.scheme == "https" and parsed.username)
    ):
        return value
    raise argparse.ArgumentTypeError("Provide an HTTPS or SSH repository URL without tokens/passwords.")


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()


def hide(path):
    if hasattr(ctypes, "windll"):
        kernel = ctypes.windll.kernel32
        attributes = kernel.GetFileAttributesW(str(path))
        if attributes == -1 or not kernel.SetFileAttributesW(str(path), attributes | 2):
            raise ctypes.WinError()


def render(source, values):
    text = source.read_text(encoding="utf-8")
    # One pass prevents text supplied by the user from becoming template syntax.
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--remote", required=True, type=online_remote)
    parser.add_argument("--name")
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--project-type", required=True, help="Descriptive project type; does not select directories.")
    parser.add_argument(
        "--recurring-tasks", action="store_true",
        help="Add state and logs for recurring business tasks; does not configure or start tasks.",
    )
    parser.add_argument(
        "--folders", nargs="*", default=[],
        help="Extra top-level directories beyond docs, outputs, skills, reference, data and config.",
    )
    args = parser.parse_args()
    if any(not re.fullmatch(r"[a-z][a-z0-9_-]*", name) for name in args.folders):
        parser.error("--folders requires simple lowercase top-level names, e.g. reference data.")
    if not args.root.is_absolute():
        parser.error("--root must be an absolute path.")
    root = args.root.resolve()
    if root.is_relative_to(SKILL_ROOT):
        parser.error("Create the project outside the source Skill directory.")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        parser.error("Target must be absent or empty; use the existing-project workflow instead.")
    if not shutil.which("git"):
        parser.error("Git is not available on PATH.")
    if not args.purpose.strip() or not args.project_type.strip() or (args.name is not None and not args.name.strip()):
        parser.error("Project name, purpose and type must not be blank.")

    parent = root.parent
    while not parent.exists():
        parent = parent.parent
    probe = subprocess.run(
        ["git", "-C", str(parent), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if probe.returncode == 0:
        parser.error("Target is inside another Git worktree; do not create a nested project.")

    moment = datetime.now(timezone(timedelta(hours=8)))
    iteration = moment.strftime("%Y%m%d-%H%M%S-init")
    selected = {"docs", "outputs", "skills", "reference", "data", "config", *args.folders}
    if args.recurring_tasks:
        selected.update({"state", "logs"})
    folders = {key: value for key, value in FOLDERS.items() if key in selected}
    folders.update({key: "待执行者补充该目录的具体职责。" for key in sorted(selected - FOLDERS.keys())})
    folder_rows = "\n".join(f"| `{key}/` | {value} |" for key, value in folders.items())
    project_type = args.project_type.strip()
    values = {
        "NAME": args.name or root.name,
        "PURPOSE": args.purpose,
        "REMOTE": args.remote,
        "TIMESTAMP": moment.isoformat(timespec="seconds"),
        "ITERATION": iteration,
        "FOLDER_ROWS": folder_rows,
        "PROJECT_TYPE": project_type,
        "RECURRING_TASKS": "有（仅准备目录，未配置或启动任务）" if args.recurring_tasks else "无",
    }
    templates = {
        "README.md": "README.md.tpl",
        "AGENTS.md": "AGENTS.md.tpl",
        ".gitignore": "gitignore.tpl",
        ".gitattributes": "gitattributes.tpl",
        "docs/project-status.md": "project-status.md.tpl",
        "docs/discussion-log.md": "discussion-log.md.tpl",
    }
    documents = {name: render(ASSETS / "project" / template, values) for name, template in templates.items()}
    esc = html.escape
    rows = "".join(
        f"<tr><td><code>{key}/</code></td><td>{esc(value)}</td></tr>"
        for key, value in folders.items()
    )
    report = render(ASSETS / "report.html.tpl", {
        "TITLE": esc(f"{values['NAME']} · 项目初始化"),
        "META": esc(f"{values['TIMESTAMP']} · {iteration}"),
        "SUMMARY_HTML": f"<p>已按{esc(project_type)}建立本地结构与协作记录；目录约定记入 README，后续保持稳定。</p><p>项目目标：{esc(args.purpose)}</p>",
        "CHANGES_HTML": '<div class="table-wrap"><table><thead><tr><th>目录</th><th>职责</th></tr></thead><tbody>' + rows + "</tbody></table></div>",
        "EVIDENCE_HTML": '<ul><li><a href="../../README.md">项目导航</a></li><li><a href="../../AGENTS.md">AI 协作规则</a></li><li><a href="../../docs/project-status.md">当前状态</a></li><li><a href="../../docs/discussion-log.md">讨论记录</a></li></ul>',
        "VALIDATION_HTML": "<p>已建立本地 Git 仓库并配置 origin。此脚本不执行远端检查、提交或推送，执行者需填入实际结果。尚未开展业务任务；临时清理仅按用户请求手动执行，不配置定时清理。</p>",
        "NEXT_HTML": "<p>完成首版远程保存，回填实际状态；首项业务任务待用户指定。</p>",
    })
    documents[f"outputs/reports/{iteration}.html"] = report

    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--initial-branch=main")
    git(root, "remote", "add", "origin", args.remote)
    hide(root / ".git")
    for directory in selected:
        (root / directory).mkdir(exist_ok=True)
    shutil.copytree(
        SKILL_ROOT, root / "skills" / "project-manager",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".tmp"),
    )
    for relative, content in documents.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    print(f"Created project: {root}")
    print(f"Report: {root / 'outputs' / 'reports' / (iteration + '.html')}")
    print("Git: initialized; origin configured. No commit, push, network check or tasks performed.")


if __name__ == "__main__":
    main()
