#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_chain.py — 联邦记忆哈希链同步参考实现（纯标准库，零外部依赖）

链路：build_snapshot → 哈希链(prev_hash + payload_sha256 → chain_hash)
      → POST /memory/write → 只读复核(GET /memory/query) → 追加 sync_state.jsonl

改造点：
  1. GW_URL      —— 你的记忆网关地址
  2. TOKEN_FILE  —— 令牌文件路径（权限 600，不入代码不入日志）
  3. build_snapshot() —— 你要同步的业务快照
"""
import hashlib, json, os, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
SYNC_STATE = os.path.join(BASE, "sync_state.jsonl")
GW_URL = "http://127.0.0.1:9210"          # ← 改成你的网关
TOKEN_FILE = os.path.join(BASE, ".token")  # ← 改成你的令牌文件（600）

GENESIS = "GENESIS"


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def last_chain() -> str:
    if not os.path.exists(SYNC_STATE):
        return GENESIS
    last = GENESIS
    with open(SYNC_STATE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line).get("chain_hash", last)
    return last


def append_log(rec: dict):
    with open(SYNC_STATE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_snapshot() -> dict:
    """示例快照：规则库计数与哈希摘要（敏感正文不外发）。请替换为你的业务。"""
    return {
        "library": "my-service",
        "items_count": 0,
        "summary_sha256": sha256(json.dumps({"placeholder": True}, sort_keys=True)),
        "packaged_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def _post(path: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-GW-Token"] = token
    req = urllib.request.Request(GW_URL + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _get(path: str, params: str = "") -> dict:
    req = urllib.request.Request(GW_URL + path + params)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def sync_once() -> str:
    prev = last_chain()
    snap = build_snapshot()
    payload = {
        "key": f"snapshot.{time.strftime('%Y%m%d%H%M%S')}",
        "payload": snap,
        "payload_sha256": sha256(json.dumps(snap, ensure_ascii=False, sort_keys=True)),
    }
    # 幂等：内容与上一条相同 → 跳过
    if os.path.exists(SYNC_STATE):
        with open(SYNC_STATE, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        if lines:
            last_rec = json.loads(lines[-1])
            if last_rec.get("payload_sha256") == payload["payload_sha256"]:
                print("SYNC_UNCHANGED")
                return "UNCHANGED"
    payload["prev_hash"] = prev
    payload["chain_hash"] = sha256(prev + payload["payload_sha256"])
    token = ""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            token = f.read().strip()
    t0 = time.time()
    try:
        resp = _post("/memory/write", payload, token)
    except Exception as e:
        append_log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "event": "ERROR", "error": str(e)[:120],
                    "chain_hash": payload["chain_hash"]})
        print("SYNC_WRITE_ERROR")
        return "ERROR"
    # 只读复核
    try:
        q = _get("/memory/query", f"?key={payload['key']}")
        readback_ok = q.get("found") is not False
    except Exception:
        readback_ok = False
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "event": "PUSH", "key": payload["key"],
           "payload_sha256": payload["payload_sha256"],
           "chain_hash": payload["chain_hash"],
           "prev_hash": prev, "readback_ok": readback_ok,
           "elapsed_ms": int((time.time() - t0) * 1000),
           "gateway_resp": str(resp)[:120]}
    append_log(rec)
    print("SYNC_OK" if readback_ok else "SYNC_PUSH_OK_READBACK_FAIL")
    return "OK"


if __name__ == "__main__":
    sync_once()
