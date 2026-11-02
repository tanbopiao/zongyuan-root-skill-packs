# 样例池格式约定 · huiguan-feedback-loop

## rules.json（分层规约库）

JSON 数组，每条规约字段：

```json
[
  {
    "rule_id": "MR-SEC-001",
    "layer": 3,
    "scope": ["*"],
    "text": "任何输出不得包含明文秘钥、令牌或口令",
    "version": 1,
    "status": "ACTIVE"
  }
]
```

- `layer`: 1=宪法层（恒在背景，不参与路由装配）；2=场景规约；3=安全红线
- `scope`: 适用场景列表，`["*"]` 通配
- `status`: `ACTIVE` / `ARCHIVED`；**缺失按 ACTIVE 处理**（防静默失效）

## samples_positive.jsonl（正例池）

每行一条 JSON：

```json
{"session_id":"s-001","pack_id":"pack-20261102...","sample":"合格输出全文（本地保存，不外发）","confidence":1.0,"scene":"*","ts":"2026-11-02T12:00:00+08:00"}
```

## samples_negative.jsonl（负例池）

每行一条 JSON：

```json
{"session_id":"s-002","pack_id":"pack-20261102...","rule_id":"MR-SEC-001","deviation_type":"p0-hit","sample":"违规输出全文（本地保存，不外发）","confidence":1.0,"ts":"2026-11-02T12:00:00+08:00"}
```

- `deviation_type`: `p0-hit`（红线命中）/ `drift`（口径漂移）/ `omission`（漏项）等，自行扩展
- 样例正文只留在本地；对外同步/上报时仅携带摘要与哈希，防污染真值池

## ledger.jsonl（闭环台账）

只增不覆盖。事件类型：`assemble` / `escape` / `closed` / `escalate`。字段以事件自带为准，至少含 `ts`、`event`。
