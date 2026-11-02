#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo_pusher.py — SEO 全域推送参考实现（纯标准库，零外部依赖）
用法：
  python3 seo_pusher.py --check    # 只做差分，不推送（巡检用）
  python3 seo_pusher.py --push     # 差分推送（新增+变更）
  python3 seo_pusher.py --full     # 全量推送（首次/密钥重验后用）
"""
import json, os, re, time, argparse, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "config.json")
STATE = os.path.join(BASE, "state.json")
LEDGER = os.path.join(BASE, "push_ledger.jsonl")
UA = {"User-Agent": "Mozilla/5.0 (seo-pusher; generic)"}


def load_config():
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    raise SystemExit("缺少 config.json，请先复制 templates/config.example.json")


def fetch_sitemap(sitemap_url):
    """抓线上 sitemap，返回 {url: lastmod}。"""
    req = urllib.request.Request(sitemap_url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", "replace")
    out = {}
    for m in re.finditer(r"<url>(.*?)</url>", xml, re.S):
        block = m.group(1)
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        lm = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if loc:
            out[loc.group(1).strip()] = lm.group(1).strip() if lm else ""
    return out


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(sitemap):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sitemap, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def log(rec):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def post_with_retry(url, data: bytes, headers, retries=3):
    """指数退避重试：1s/2s/4s。"""
    delay = 1
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, r.read().decode("utf-8", "replace")[:500]
        except Exception as e:
            if i == retries - 1:
                return None, str(e)
            time.sleep(delay)
            delay *= 2
    return None, "exhausted"


def push_indexnow(cfg, urls):
    """IndexNow 单接口覆盖 Bing/Yandex/Naver/Seznam。"""
    payload = json.dumps({
        "host": cfg["host"],
        "key": cfg["indexnow_key"],
        "urlList": urls,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8", **UA}
    status, body = post_with_retry("https://api.indexnow.org/IndexNow", payload, headers)
    return {"channel": "indexnow", "status": status, "count": len(urls), "body": body[:120]}


def push_baidu(cfg, urls):
    """百度链接提交（可选）：需 cfg['baidu_token'] 与推送接口配额。"""
    token = cfg.get("baidu_token")
    if not token:
        return {"channel": "baidu", "status": "skipped", "count": 0, "body": "no token"}
    site = cfg["host"].replace("https://", "").replace("http://", "")
    url = f"http://data.zz.baidu.com/urls?site={site}&token={token}"
    payload = "\n".join(urls).encode("utf-8")
    headers = {"Content-Type": "text/plain", **UA}
    status, body = post_with_retry(url, payload, headers)
    return {"channel": "baidu", "status": status, "count": len(urls), "body": body[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    sitemap = fetch_sitemap(cfg["sitemap_url"])
    state = load_state()
    if args.full:
        todo = list(sitemap.keys())
    else:
        todo = [u for u, lm in sitemap.items()
                if u not in state or (lm and state.get(u) != lm)]
    print(f"sitemap={len(sitemap)} todo={len(todo)}")
    if args.check or not args.push and not args.full:
        for u in todo[:20]:
            print("  diff:", u)
        return
    for batch_start in range(0, len(todo), 1000):
        batch = todo[batch_start:batch_start + 1000]
        r1 = push_indexnow(cfg, batch)
        r2 = push_baidu(cfg, batch)
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "indexnow": r1, "baidu": r2})
        print(json.dumps(r1, ensure_ascii=False)[:200])
        print(json.dumps(r2, ensure_ascii=False)[:200])
    save_state(sitemap)
    print("state updated")


if __name__ == "__main__":
    main()
