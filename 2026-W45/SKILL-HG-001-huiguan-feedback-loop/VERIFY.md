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

## 第 2 步：回观引擎实跑（零配置，纯标准库）

```bash
python3 templates/verify_skeleton.py

# 预期输出（原文，实测值）：
# {
#   "ok": false,
#   "output": "[regenerated] 处理任务，绝不外泄 token=abc123456789012345678901234",
#   "attempts": 3,
#   "escalated": true,
#   "rule_id": "MR-SEC-001"
# }
# metrics: {'positive': 0, 'negative': 2, 'closed_sessions': 0, 'note': 'escape_rate_7d 按实际业务接入后统计'}

# 预期输出：JSON 五个键值与上完全一致——本用例演示"提示注入攻击被规则拒绝并升级"，
# ok:false 与 escalated:true 是正确行为，不是故障。
```

## 第 3 步：结构核对

`templates/rules.schema.json`（规则模式）、`templates/samples.format.md`（样本格式）、`references/method.md`（方法论）三件齐全可读。
