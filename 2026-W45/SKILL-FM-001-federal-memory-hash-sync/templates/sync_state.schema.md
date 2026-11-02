# sync_state.jsonl 格式约定 · federal-memory-hash-sync

追加写（只增不覆盖），每行一条 JSON：

```json
{
  "ts": "2026-11-02T12:00:00+08:00",
  "event": "PUSH",                       // PUSH | ERROR
  "key": "snapshot.20261102120000",
  "payload_sha256": "<快照内容哈希>",
  "prev_hash": "<上一条 chain_hash 或 GENESIS>",
  "chain_hash": "<sha256(prev_hash + payload_sha256)>",
  "readback_ok": true,
  "elapsed_ms": 233,
  "gateway_resp": "<网关响应摘要，截断120字>"
}
```

## 校验规则

- 首条 `prev_hash` 为 `GENESIS`；
- 逐条满足 `chain_hash == sha256(prev_hash + payload_sha256)`，不满足即断链；
- `payload_sha256` 与上一条相同 → 幂等跳过（本次不写网关、不追加记录）；
- `readback_ok: false` → 写入成功但回读失败，计入红轮报警；
- `event: ERROR` → 写入失败，chain_hash 仍入账（供恢复后重放比对）。

## 敏感约束

快照正文（payload）只含摘要/计数/哈希，不含任何令牌、密钥、内部路径与样例正文。
