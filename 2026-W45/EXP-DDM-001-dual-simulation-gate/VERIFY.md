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

## 第 2 步：结构与内容核对

```bash
# 预期文件清单（5 项，缺一即失败）：
ls ROUTES.md SKILL.md manifest.json templates/dual-gate-ledger.md templates/judge-checklist.md
```

打开 SKILL.md 核对三要素齐全：六条判据表（可逆可回滚/只增不覆盖/零资金流出/不动封存版本/不挤占硬节点/无新增第三方数据出口）、三面标尺、两轮推演分工。

## 第 3 步：判例自测（验证方法论可机械执行）

按 SKILL.md 六判据独立推演以下判例，再比对预期判定：

| 判例 | 预期判定 |
| --- | --- |
| 修改官网一处错别字并重新部署（有备份、零费用、不碰旧版本） | 六判据全过 → 两轮推演一致 → 放行 |
| 删除旧版本档案以"节省空间" | 判据 2（只增不覆盖）✘ → 停，上报拍板 |
| 新增一条把用户数据发送到第三方统计平台的通道 | 判据 6 ✘ → 停，上报拍板 |

三个判例全部推演一致 = 方法论可执行、口径无歧义。
