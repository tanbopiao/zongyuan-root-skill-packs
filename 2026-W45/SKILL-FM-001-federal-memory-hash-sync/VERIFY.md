# 独立验证指南（任何人 / 任何 AI 可执行）

前置：Python 3.10+（本包零外部依赖）。每一步都是机械动作，任何一步与预期不符即验证失败，请携带完整输出提交 issue。

```bash
# 第 1 步：完整性核对（对 manifest.json 的 files_sha256 逐文件核对）
python3 - << 'EOF'
import hashlib, json
m = json.load(open("manifest.json"))
ok = all(hashlib.sha256(open(f, "rb").read()).hexdigest() == h
         for f, h in m["files_sha256"].items())
print("MANIFEST-CHECK", "OK" if ok else "FAIL")
EOF

# 预期输出：MANIFEST-CHECK OK
```

## 第 2 步：无网关降级路径验证（无需任何配置）

```bash
python3 templates/sync_chain.py

# 预期输出（原文）：
# SYNC_WRITE_ERROR
```

同时验证降级不丢证据：`templates/sync_state.jsonl` 应新增一行 `"event": "ERROR"` 记录，且其中的 `chain_hash` 可自行复算：

```bash
python3 - << 'EOF'
import hashlib, json
rec = [json.loads(l) for l in open("templates/sync_state.jsonl") if l.strip()][-1]
calc = hashlib.sha256((rec["prev_hash"] + rec["payload_sha256"]).encode()).hexdigest()
print("CHAIN-CHECK", "OK" if calc == rec["chain_hash"] else "FAIL")
EOF

# 预期输出：CHAIN-CHECK OK
```

## 第 3 步（可选，需自建记忆网关）：闭环验证

把 `GW_URL` 改为你的网关地址、放置 600 权限令牌文件后重跑，预期输出 `SYNC_OK`，且 `sync_state.jsonl` 新记录 `readback_ok: true`（写入后只读复核通过）。
