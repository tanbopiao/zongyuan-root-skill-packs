#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_skeleton.py — 规约回灌闭环参考实现（纯标准库，零外部依赖）

职责：装配→校验→回灌→重生成→复判→正例回灌 的最小可运行骨架。
改造点：
  1. P0_RULES      —— 换成你自己的业务红线正则（秘钥/越权/口径）
  2. default_executor —— 接上你的生成器（LLM/流水线）
  3. RULES/SAMPLES —— 规约库与样例池的存储路径
"""
import json, os, re, time

BASE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(BASE, "rules.json")
SAMPLES_P = os.path.join(BASE, "samples_positive.jsonl")
SAMPLES_N = os.path.join(BASE, "samples_negative.jsonl")
LEDGER = os.path.join(BASE, "ledger.jsonl")
MAX_RETRY = 2  # 重试上限：用尽即升级人工复核，不无限重试

# —— P0 红线（示例：秘钥泄漏类；请替换为你的业务红线）——
P0_RULES = {
    "MR-SEC-001": re.compile(
        r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}"
        r"|token[=:]\s*['\"]?[A-Za-z0-9]{24,})", re.I),
}


def _read_all(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _append(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _log(ev):
    _append(LEDGER, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **ev})


def _load_rules():
    if not os.path.exists(RULES):
        return []
    with open(RULES, encoding="utf-8") as f:
        rules = json.load(f)
    # 约定：缺 status 视为 ACTIVE（防静默失效）
    return [r for r in rules if r.get("status", "ACTIVE") == "ACTIVE"]


def assemble_pack(intent="", scene="*", top_n=3):
    """按意图与场景装配活跃规约；layer1 宪法层恒在背景、不进路由结果。"""
    rules = _load_rules()
    routed = [r["rule_id"] for r in rules
              if r.get("layer", 2) >= 2 and (scene in r.get("scope", ["*"]) or "*" in r.get("scope", []))]
    pos = _read_all(SAMPLES_P)
    examples = [p for p in pos if p.get("scene") in ("*", scene)][:top_n]
    pack = {"pack_id": "pack-%s" % time.strftime("%Y%m%d%H%M%S"),
            "intent": intent, "scene": scene, "routed": routed,
            "examples": [p.get("sample", "")[:200] for p in examples]}
    _log({"event": "assemble", "pack_id": pack["pack_id"],
          "routed": routed, "examples": len(examples)})
    return pack


def verify(session_id, output_text, pack_id=""):
    """P0 正则逐字校验；命中即判违规并指出违了哪条。"""
    for rid, pat in P0_RULES.items():
        m = pat.search(output_text)
        if m:
            _log({"event": "escape", "session_id": session_id,
                  "rule_id": rid, "pack_id": pack_id,
                  "hit": m.group(0)[:4] + "***"})
            return {"verdict": "FAIL", "rule_id": rid, "match": m.group(0)}
    return {"verdict": "PASS", "rule_id": None, "match": None}


def feedback_positive(session_id, pack_id, sample, confidence=1.0):
    _append(SAMPLES_P, {"session_id": session_id, "pack_id": pack_id,
                        "sample": sample, "confidence": confidence,
                        "scene": "*", "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})


def feedback_escape(session_id, pack_id, rule_id, deviation_type, sample, confidence=1.0):
    _append(SAMPLES_N, {"session_id": session_id, "pack_id": pack_id,
                        "rule_id": rule_id, "deviation_type": deviation_type,
                        "sample": sample, "confidence": confidence,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})


def default_executor(task_output, verdict=None):
    """占位执行器：直接原样返回。请替换为你的生成器。
    真实实现应读取负例与违规点，生成修复后的输出。"""
    if verdict is None:
        return task_output
    return "[regenerated] " + task_output


def run_session(session_id, task_output, scene="*", intent="", executor=None):
    """主入口：装配→执行→校验→回灌→重生成→复判→正例回灌→指标。"""
    executor = executor or default_executor
    pack = assemble_pack(intent=intent, scene=scene)
    output = executor(task_output, None)
    verdict = verify(session_id, output, pack["pack_id"])
    attempt = 1
    while verdict["verdict"] != "PASS" and attempt <= MAX_RETRY:
        feedback_escape(session_id, pack["pack_id"], verdict["rule_id"],
                        "p0-hit", output)
        output = executor(task_output, verdict)
        verdict = verify(session_id, output, pack["pack_id"])
        attempt += 1
    if verdict["verdict"] == "PASS":
        feedback_positive(session_id, pack["pack_id"], output,
                          confidence=1.0 / (1 + attempt))
        _log({"event": "closed", "session_id": session_id,
              "attempts": attempt, "final": "PASS"})
        return {"ok": True, "output": output, "attempts": attempt}
    # 重试用尽 → 升级人工复核，完整轨迹留痕
    _log({"event": "escalate", "session_id": session_id,
          "attempts": attempt, "final": "FAIL", "rule_id": verdict["rule_id"]})
    return {"ok": False, "output": output, "attempts": attempt,
            "escalated": True, "rule_id": verdict["rule_id"]}


def metrics():
    pos, neg = _read_all(SAMPLES_P), _read_all(SAMPLES_N)
    events = _read_all(LEDGER)
    closed = [e for e in events if e.get("event") == "closed"]
    return {"positive": len(pos), "negative": len(neg),
            "closed_sessions": len(closed),
            "note": "escape_rate_7d 按实际业务接入后统计"}


if __name__ == "__main__":
    r = run_session("demo-001", "处理任务，绝不外泄 token=abc123456789012345678901234",
                    intent="demo", scene="*")
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("metrics:", metrics())
