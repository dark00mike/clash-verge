#!/usr/bin/env python3
"""
End-to-end isolated verification script for Clash Verge / Mihomo Antigravity US routing schemes.
Zero side-effects on the running system Clash Verge service (uses isolated temp ports & no TUN).

Usage:
    python3 verify_antigravity_routing.py [yaml_file]
Default yaml_file: version/双订阅分流-v2.yaml
"""

import http.server
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import yaml

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
MIHOMO_BIN = "/usr/bin/verge-mihomo"
AGY_NODE_BIN = "/home/mike/.config/Antigravity/bin/agy-node"
MIXED_PORT = 28797
CTRL_PORT = 29097


def pick_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def ctrl_get(path, timeout=5):
    url = f"http://127.0.0.1:{CTRL_PORT}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ctrl_put(path, payload):
    url = f"http://127.0.0.1:{CTRL_PORT}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status


def parse_mihomo_logs(log_text):
    """Extract routing match records from Mihomo info logs."""
    # Example:
    # time="..." level=info msg="[TCP] 127.0.0.1:35470(curl, uid=1000) --> accounts.google.com:443 match Domain(accounts.google.com) using Antigravity[🇺🇸 美国 🄳]"
    records = []
    pat = re.compile(
        r'msg="\[(?P<proto>TCP|UDP)\]\s+(?P<src>.+?)\s+-->\s+(?P<dst>\S+)\s+match\s+(?P<rule>.+?)\s+using\s+(?P<chain>.+?)"'
    )
    for line in log_text.splitlines():
        m = pat.search(line)
        if m:
            records.append(m.groupdict())
    return records


def run_agy_node_http(url, proxy_url, timeout=15):
    js = r"""
const http = require('http');
const https = require('https');
const tls = require('tls');
const { URL } = require('url');

const target = new URL(process.argv[1]);
const proxy = new URL(process.argv[2]);

if (target.protocol === 'http:') {
  const req = http.request({
    host: proxy.hostname,
    port: proxy.port,
    method: 'GET',
    path: target.href,
    headers: { Host: target.host, Connection: 'close' },
    timeout: 12000,
  }, (res) => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
      console.log(JSON.stringify({ status: res.statusCode, body }));
    });
  });
  req.on('error', e => { console.error(e.message); process.exit(2); });
  req.end();
} else {
  const port = target.port || 443;
  const creq = http.request({
    host: proxy.hostname,
    port: proxy.port,
    method: 'CONNECT',
    path: `${target.hostname}:${port}`,
    timeout: 12000,
  });
  creq.on('connect', (res, sock) => {
    if (res.statusCode !== 200) {
      console.error('CONNECT failed:', res.statusCode);
      process.exit(3);
    }
    const tlsSock = tls.connect({ socket: sock, servername: target.hostname }, () => {
      const hreq = https.request({
        host: target.hostname,
        port,
        path: target.pathname + target.search,
        method: 'GET',
        createConnection: () => tlsSock,
        headers: { Host: target.host, 'User-Agent': 'antigravity-verify/1.0', Connection: 'close' },
        timeout: 12000,
      }, (hres) => {
        let body = '';
        hres.on('data', c => body += c);
        hres.on('end', () => {
          console.log(JSON.stringify({ status: hres.statusCode, body }));
        });
      });
      hreq.on('error', e => { console.error(e.message); process.exit(4); });
      hreq.end();
    });
    tlsSock.on('error', e => { console.error(e.message); process.exit(5); });
  });
  creq.on('error', e => { console.error(e.message); process.exit(6); });
  creq.end();
}
"""
    r = subprocess.run(
        [AGY_NODE_BIN, "-e", js, url, proxy_url],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(f"agy-node failed (rc={r.returncode}): {r.stderr.strip()}")
    return json.loads(r.stdout.strip())


def run_curl(url, proxy_url, timeout=12, head_only=True, extra_args=None, retries=1):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-x", proxy_url]
    if head_only:
        cmd.extend(["-I", "-o", "/dev/null", "-w", "%{http_code}"])
    else:
        cmd.extend(["-w", "\n%{http_code}"])
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)
    for attempt in range(retries + 1):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 or attempt == retries:
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        time.sleep(0.5)


def start_local_ping_server():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"LOCAL_OK")
        def log_message(self, *args):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def main():
    target_name = sys.argv[1] if len(sys.argv) > 1 else "version/双订阅分流-v2.yaml"
    yaml_path = target_name if os.path.isabs(target_name) else os.path.join(WORKSPACE, target_name)
    assert os.path.exists(yaml_path), f"Config not found: {yaml_path}"
    print(f"=== Testing Clash Verge Scheme: {yaml_path} ===\n")

    failures = []

    def check(cond, msg):
        if cond:
            print(f"  [PASS] {msg}")
        else:
            print(f"  [FAIL] {msg}")
            failures.append(msg)

    # ------------------------------------------------------------------
    # 1. Official verge-mihomo -t validation
    # ------------------------------------------------------------------
    print("[1/7] Running verge-mihomo -t config validation...")
    t_res = subprocess.run(
        [MIHOMO_BIN, "-d", WORKSPACE, "-t", "-f", yaml_path],
        capture_output=True, text=True
    )
    check(t_res.returncode == 0, f"verge-mihomo -t exited with code {t_res.returncode}")
    if t_res.returncode != 0:
        print(t_res.stdout)
        print(t_res.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Launch isolated runtime Mihomo instance
    # ------------------------------------------------------------------
    print("\n[2/7] Launching isolated verge-mihomo runtime (no TUN, isolated ports)...")
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Overlay isolated runtime settings mimicking Clash Verge (including Script.js rule)
    runtime_cfg = dict(cfg)
    runtime_cfg["mode"] = "rule"
    runtime_cfg["mixed-port"] = MIXED_PORT
    runtime_cfg["allow-lan"] = False
    runtime_cfg["log-level"] = "info"
    runtime_cfg["ipv6"] = False  # avoid local IPv6 socket ambiguity in test harness
    runtime_cfg["external-controller"] = f"127.0.0.1:{CTRL_PORT}"
    runtime_cfg["tun"] = {"enable": False}
    # Disable standalone DNS listener (:53) in non-root isolated test instance
    runtime_cfg["dns"] = {"enable": False}
    # Apply Clash Verge Script.js rule prepending
    rules = list(runtime_cfg.get("rules", []))
    ubuntu_rule = "DOMAIN,connectivity-check.ubuntu.com,DIRECT"
    if ubuntu_rule not in rules:
        rules.insert(0, ubuntu_rule)
    runtime_cfg["rules"] = rules

    # Copy geo files symlink or use WORKSPACE as -d (need Country.mmdb for GEOIP,CN!)
    cv_dir = os.path.expanduser("~/.local/share/io.github.clash-verge-rev.clash-verge-rev")
    with tempfile.TemporaryDirectory(prefix="mihomo-verify-") as td:
        # Symlink profiles & geodata into td so SAFE_PATHS allows ./profiles/... and GEOIP works
        os.symlink(os.path.join(WORKSPACE, "profiles"), os.path.join(td, "profiles"))
        for geo in ("Country.mmdb", "geoip.dat", "geosite.dat", "ASN.mmdb"):
            src_geo = os.path.join(cv_dir, geo)
            if os.path.exists(src_geo):
                os.symlink(src_geo, os.path.join(td, geo))
        cfg_file = os.path.join(td, "runtime.yaml")
        log_file = os.path.join(td, "mihomo.log")
        with open(cfg_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(runtime_cfg, f, allow_unicode=True, sort_keys=False)

        lf = open(log_file, "w+", encoding="utf-8")
        proc = subprocess.Popen(
            [MIHOMO_BIN, "-d", td, "-f", cfg_file],
            stdout=lf, stderr=subprocess.STDOUT,
        )
        local_srv, local_port = start_local_ping_server()
        proxy_url = f"http://127.0.0.1:{MIXED_PORT}"

        try:
            # Wait for API + initial lazy:false health check (~7s for dead feiniaoyun 5s timeout)
            ready = False
            for _ in range(30):
                try:
                    ctrl_get("/version")
                    ready = True
                    break
                except Exception:
                    time.sleep(0.3)
            check(ready, "Isolated Mihomo API is reachable")
            if not ready:
                sys.exit(1)

            print("  Waiting 7s for startup US health-checks (lazy: false) to settle...")
            time.sleep(7.0)

            # Inspect providers & groups
            provs = ctrl_get("/providers/proxies").get("providers", {})
            ag_mz = [p["name"] for p in provs.get("antigravity-miaoz", {}).get("proxies", [])]
            ag_fn = [p["name"] for p in provs.get("antigravity-feiniaoyun", {}).get("proxies", [])]
            print(f"  antigravity-miaoz ({len(ag_mz)}): {ag_mz}")
            print(f"  antigravity-feiniaoyun ({len(ag_fn)}): {ag_fn}")

            check(len(ag_mz) == 3 and all("美国" in n for n in ag_mz), f"antigravity-miaoz has strictly 3 US nodes: {ag_mz}")
            check(len(ag_fn) == 12 and all("美国" in n for n in ag_fn), f"antigravity-feiniaoyun has strictly 12 US nodes")
            check(not any("港" in n or "HK" in n.upper() for n in ag_mz + ag_fn), "Zero HK nodes in Antigravity US providers")

            proxies = ctrl_get("/proxies").get("proxies", {})
            ag_grp = proxies.get("Antigravity", {})
            ag_auto = proxies.get("Antigravity 美国自动", {})
            ag_fb = proxies.get("Antigravity 美国故障转移", {})
            mz_us = proxies.get("喵子美国专线", {})

            print(f"  Antigravity now={ag_grp.get('now')} | all_count={len(ag_grp.get('all', []))}")
            print(f"  Antigravity 美国自动 now={ag_auto.get('now')}")
            print(f"  Antigravity 美国故障转移 now={ag_fb.get('now')}")
            print(f"  喵子美国专线 now={mz_us.get('now')}")

            check(ag_grp.get("now") == "Antigravity 美国自动", f"Antigravity defaults to 'Antigravity 美国自动' (got: {ag_grp.get('now')})")
            check("DIRECT" not in ag_grp.get("all", []), "Antigravity group has NO DIRECT option")
            check(not any("香港" in x or "日本" in x or "狮城" in x or "台湾" in x for x in ag_grp.get("all", [])), "Antigravity group has ZERO non-US nodes")
            check("美国" in (ag_auto.get("now") or ""), f"Antigravity 美国自动 selected live US node: {ag_auto.get('now')}")
            check("美国" in (ag_fb.get("now") or ""), f"Antigravity 美国故障转移 selected live US node: {ag_fb.get('now')}")

            # Helper to read new logs since offset
            lf.flush()
            log_pos = os.path.getsize(log_file)

            def read_new_records():
                nonlocal log_pos
                time.sleep(0.25)
                lf.flush()
                with open(log_file, "r", encoding="utf-8", errors="replace") as rf:
                    rf.seek(log_pos)
                    chunk = rf.read()
                    log_pos = rf.tell()
                return parse_mihomo_logs(chunk), chunk

            # Static audit of PROCESS-PATH-REGEX against all real Antigravity executables on disk
            proc_rule = next((r for r in cfg.get("rules", []) if r.startswith("PROCESS-PATH-REGEX,")), "")
            proc_pat = proc_rule.split(",", 2)[1] if proc_rule else ""
            must_match = [
                "/home/mike/.local/opt/google-antigravity/antigravity",
                "/home/mike/.local/opt/google-antigravity/resources/bin/language_server",
                "/home/mike/.local/opt/google-antigravity/chrome_crashpad_handler",
                "/home/mike/.local/bin/agy",
                "/home/mike/.local/bin/agy.1795454350022895753.old",
                "/home/mike/.config/Antigravity/bin/agy-node",
                "/home/mike/.gemini/antigravity/bin/agentapi",
                "/home/mike/.gemini/antigravity/builtin/plugins/swarm/sidecars/swarm_board/main.mjs",
                "/home/mike/.cache/antigravity-updater/pending/update",
            ]
            must_not_match = [
                "/usr/bin/curl",
                "/usr/bin/python3",
                "/usr/lib/chatgpt/ChatGPT",
                "/usr/lib/chatgpt/resources/codex",
                "/home/mike/.local/bin/agysomething",
            ]
            check(
                bool(proc_pat) and all(re.search(proc_pat, p) for p in must_match) and not any(re.search(proc_pat, p) for p in must_not_match),
                f"PROCESS-PATH-REGEX matches all {len(must_match)} Antigravity binary paths and rejects all {len(must_not_match)} non-Antigravity paths"
            )

            # ------------------------------------------------------------------
            # 3. Process-Path Matching (agy-node -> non-Antigravity domains) + US Exit Geo Verification
            # ------------------------------------------------------------------
            print("\n[3/7] Testing Antigravity binary (agy-node) PROCESS-PATH-REGEX + US Exit IP Geolocation...")
            read_new_records()  # clear buffer

            trace_res = run_agy_node_http("https://www.cloudflare.com/cdn-cgi/trace", proxy_url)
            recs_trace, _ = read_new_records()
            trace_kv = dict(line.split("=", 1) for line in trace_res["body"].splitlines() if "=" in line)
            print(f"  agy-node -> cloudflare trace: ip={trace_kv.get('ip')} loc={trace_kv.get('loc')} colo={trace_kv.get('colo')}")
            matched_trace = [r for r in recs_trace if "cloudflare.com" in r["dst"]]
            print(f"  Mihomo log match: {matched_trace}")
            check(trace_kv.get("loc") == "US", f"agy-node actual exit IP country is US (loc={trace_kv.get('loc')}, ip={trace_kv.get('ip')})")
            check(
                any("ProcessPathRegex" in r["rule"] and "Antigravity" in r["chain"] and "美国" in r["chain"] for r in matched_trace),
                f"agy-node -> cloudflare.com matched ProcessPathRegex -> Antigravity (US): {matched_trace}"
            )

            geo_res = run_agy_node_http("https://ipinfo.io/json", proxy_url)
            recs_geo, _ = read_new_records()
            geo_j = json.loads(geo_res["body"])
            print(f"  agy-node -> ipinfo.io: ip={geo_j.get('ip')} country={geo_j.get('country')} region={geo_j.get('region')} city={geo_j.get('city')} org={geo_j.get('org')}")
            matched_geo = [r for r in recs_geo if "ipinfo.io" in r["dst"]]
            check(geo_j.get("country") == "US", f"ipinfo.io confirms US exit ({geo_j.get('city')}, {geo_j.get('region')}, {geo_j.get('country')})")
            check(
                any("ProcessPathRegex" in r["rule"] and "Antigravity" in r["chain"] for r in matched_geo),
                f"agy-node -> ipinfo.io matched ProcessPathRegex -> Antigravity: {matched_geo}"
            )

            # ------------------------------------------------------------------
            # 4. Antigravity Process Localhost/LAN DIRECT Bypass (Rule #1)
            # ------------------------------------------------------------------
            print("\n[4/7] Testing Antigravity binary localhost/127.0.0.1 DIRECT bypass (Rule #1)...")
            for host in ("127.0.0.1", "localhost"):
                res_loc = run_agy_node_http(f"http://{host}:{local_port}/ping", proxy_url)
                recs_loc, _ = read_new_records()
                matched_loc = [r for r in recs_loc if str(local_port) in r["dst"]]
                print(f"  agy-node -> {host}:{local_port}: body={res_loc['body']!r} log={matched_loc}")
                check(
                    res_loc["status"] == 200 and res_loc["body"] == "LOCAL_OK"
                    and any("DIRECT" in r["chain"] and "AND" in r["rule"] for r in matched_loc),
                    f"agy-node -> {host}:{local_port} bypassed proxy via Rule #1 AND -> DIRECT"
                )

            # ------------------------------------------------------------------
            # 5. Domain & Regex Rules via Non-Antigravity Process (curl = Chrome/MCP/SDK)
            # ------------------------------------------------------------------
            print("\n[5/7] Testing Antigravity/CloudCode/AI/OAuth/Updater domain rules via curl (non-Antigravity process)...")
            domain_cases = [
                ("https://antigravity.google", "antigravity.google"),
                ("https://daily-cloudcode-pa.googleapis.com", "daily-cloudcode-pa.googleapis.com"),
                ("https://cloudcode-pa.googleapis.com", "cloudcode-pa.googleapis.com"),
                ("https://aicode.googleapis.com", "aicode.googleapis.com"),
                ("https://generativelanguage.googleapis.com", "generativelanguage.googleapis.com"),
                ("https://us-central1-aiplatform.googleapis.com", "us-central1-aiplatform.googleapis.com"),
                ("https://us-discoveryengine.googleapis.com", "us-discoveryengine.googleapis.com"),
                ("https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/manifest/", "antigravity-hub-auto-updater"),
                ("https://accounts.google.com", "accounts.google.com"),
                ("https://oauth2.googleapis.com", "oauth2.googleapis.com"),
                ("https://www.googleapis.com", "www.googleapis.com"),
                ("https://play.googleapis.com", "play.googleapis.com"),
                ("https://lh3.googleusercontent.com", "lh3.googleusercontent.com"),
                ("https://www.gstatic.com/generate_204", "www.gstatic.com"),
            ]
            for url, needle in domain_cases:
                rc, code, err = run_curl(url, proxy_url, timeout=12, head_only=True)
                recs, _ = read_new_records()
                matched = [r for r in recs if needle in r["dst"]]
                ok_route = any("Antigravity" in r["chain"] and "美国" in r["chain"] for r in matched)
                ok_http = rc == 0 and code.isdigit() and int(code) in (200, 204, 301, 302, 400, 401, 403, 404)
                detail = f"{needle} -> HTTP {code} | rule={matched[0]['rule'] if matched else 'NONE'} | chain={matched[0]['chain'] if matched else 'NONE'}"
                check(ok_route and ok_http, detail)

            # Also test regex-matched staging/sandbox endpoints (routing match check even if DNS/HTTP returns 404/err)
            for host in ("autopush-cloudcode-pa.googleapis.com", "businessaicode.us.rep.googleapis.com"):
                rc, code, err = run_curl(f"https://{host}", proxy_url, timeout=8, head_only=True)
                recs, _ = read_new_records()
                matched = [r for r in recs if host in r["dst"]]
                ok_route = any("DomainRegex" in r["rule"] and "Antigravity" in r["chain"] and "美国" in r["chain"] for r in matched)
                check(ok_route, f"Regex endpoint {host} -> rule={matched[0]['rule'] if matched else 'NONE'} | chain={matched[0]['chain'] if matched else 'NONE'}")

            # ------------------------------------------------------------------
            # 6. TLS SNI Sniffing Test (Raw IP Connection simulating Chrome DoH)
            # ------------------------------------------------------------------
            print("\n[6/7] Testing TLS SNI Sniffer (raw IP -> accounts.google.com)...")
            # Resolve real Google IP via live DNS over US proxy? Just query 142.250.189.205 (or resolve via DoH/curl)
            # Get a live IP for accounts.google.com from DoH via proxy so it's always valid
            rc_doh, doh_out, _ = run_curl(
                "https://dns.google/resolve?name=accounts.google.com&type=A",
                proxy_url, timeout=10, head_only=False
            )
            google_ip = None
            if rc_doh == 0:
                try:
                    j = json.loads(doh_out.rsplit("\n", 1)[0])
                    for a in j.get("Answer", []):
                        if a.get("type") == 1:
                            google_ip = a["data"]
                            break
                except Exception:
                    pass
            read_new_records()
            if google_ip:
                # Connect via raw IP to proxy (CONNECT <google_ip>:443) with TLS SNI accounts.google.com!
                # Use python ssl over HTTP CONNECT to <google_ip>:443
                s = socket.create_connection(("127.0.0.1", MIXED_PORT), timeout=10)
                s.sendall(f"CONNECT {google_ip}:443 HTTP/1.1\r\nHost: {google_ip}:443\r\n\r\n".encode())
                resp = s.recv(4096)
                import ssl
                ctx = ssl.create_default_context()
                tls_s = ctx.wrap_socket(s, server_hostname="accounts.google.com")
                tls_s.sendall(b"HEAD / HTTP/1.1\r\nHost: accounts.google.com\r\nConnection: close\r\n\r\n")
                tls_resp = tls_s.recv(512).decode(errors="replace")
                tls_s.close()
                recs_sni, _ = read_new_records()
                matched_sni = [r for r in recs_sni if "accounts.google.com" in r["dst"] or google_ip in r["dst"]]
                print(f"  Raw IP {google_ip}:443 with SNI accounts.google.com -> HTTP: {tls_resp.splitlines()[0] if tls_resp else 'empty'} | log={matched_sni}")
                check(
                    any("Antigravity" in r["chain"] and "美国" in r["chain"] for r in matched_sni),
                    f"TLS SNI sniffer caught raw-IP connection to {google_ip} (SNI accounts.google.com) -> Antigravity (US)"
                )
            else:
                check(False, "Could not obtain Google IP via dns.google for SNI test")

            # ------------------------------------------------------------------
            # 7. Non-Regression Checks (Other Dual-Subscription Rules Intact)
            # ------------------------------------------------------------------
            print("\n[7/7] Testing non-regression of existing dual-subscription rules...")
            non_reg = [
                ("https://chatgpt.com/api/auth/session", "chatgpt.com", "🤖 ChatGPT"),
                ("https://api.github.com", "api.github.com", "🚀 代理节点"),
                ("http://connectivity-check.ubuntu.com", "connectivity-check.ubuntu.com", "DIRECT"),
                ("https://www.baidu.com", "www.baidu.com", "🎯 国内流量"),
                ("https://www.todesk.com", "www.todesk.com", "🎯 国内流量"),
                ("https://www.youtube.com", "www.youtube.com", "📺 YouTube"),
            ]
            for url, needle, expected_group in non_reg:
                rc, code, err = run_curl(url, proxy_url, timeout=10, head_only=True)
                recs, _ = read_new_records()
                matched = [r for r in recs if needle in r["dst"]]
                ok = any(expected_group in r["chain"] for r in matched)
                check(ok, f"Non-regression {needle} -> expected '{expected_group}' | got chain={matched[0]['chain'] if matched else 'NONE'} (HTTP {code})")

            # Also verify Antigravity Failover mode works end-to-end
            ctrl_put("/proxies/" + urllib.parse.quote("Antigravity"), {"name": "Antigravity 美国故障转移"})
            ag_after = ctrl_get("/proxies/" + urllib.parse.quote("Antigravity"))
            read_new_records()
            fb_trace = run_agy_node_http("https://www.cloudflare.com/cdn-cgi/trace", proxy_url)
            fb_kv = dict(line.split("=", 1) for line in fb_trace["body"].splitlines() if "=" in line)
            fb_recs, _ = read_new_records()
            fb_matched = [r for r in fb_recs if "cloudflare.com" in r["dst"]]
            check(
                ag_after.get("now") == "Antigravity 美国故障转移"
                and fb_kv.get("loc") == "US"
                and any("Antigravity" in r["chain"] and "美国" in r["chain"] for r in fb_matched),
                f"Fallback mode (Antigravity -> Antigravity 美国故障转移) verified US exit: ip={fb_kv.get('ip')} loc={fb_kv.get('loc')} chain={fb_matched[0]['chain'] if fb_matched else 'NONE'}"
            )

        finally:
            local_srv.shutdown()
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
            lf.close()

    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED 100%!")
        sys.exit(0)


if __name__ == "__main__":
    main()
