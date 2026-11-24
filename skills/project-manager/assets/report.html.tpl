<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}}</title>
<style>
:root{color-scheme:light;--ink:#182c3a;--muted:#526778;--line:#dbe5eb;--accent:#086f77}
*{box-sizing:border-box}body{margin:0;background:#f4f7f9;color:var(--ink);font:16px/1.75 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:1000px;margin:40px auto;padding:36px 42px;background:white;border:1px solid var(--line);border-radius:16px}
header{border-top:5px solid var(--accent);padding-top:20px}h1{font-size:30px;line-height:1.35;margin:8px 0 12px}h2{font-size:20px;margin:30px 0 10px}
.meta{color:var(--muted);font-size:14px}.summary{background:#eaf5f4;padding:18px 22px;border-radius:10px;margin:24px 0}
p{margin:8px 0}a{color:var(--accent);text-underline-offset:3px}code{background:#eef3f6;padding:2px 5px;border-radius:4px;overflow-wrap:anywhere}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:10px 12px}th{background:#f4f7f9}
li{margin:5px 0}footer{margin-top:32px;border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:13px}
@media(max-width:640px){main{margin:12px;padding:22px 18px}h1{font-size:24px}th,td{padding:8px}}
@media print{body{background:white}main{border:0;margin:0;padding:0;max-width:none}a{color:inherit}}
</style>
</head>
<body><main>
<header><div class="meta">{{META}}</div><h1>{{TITLE}}</h1></header>
<section class="summary" aria-label="结论">{{SUMMARY_HTML}}</section>
<section><h2>完成的工作</h2>{{CHANGES_HTML}}</section>
<section><h2>结果与证据</h2>{{EVIDENCE_HTML}}</section>
<section><h2>验证与保存状态</h2>{{VALIDATION_HTML}}</section>
<section><h2>下一步</h2>{{NEXT_HTML}}</section>
<footer>本报告对应一个任务版本。最新有效结论和后续变化以项目当前状态及讨论记录为准。</footer>
</main></body>
</html>
