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

## 第 2 步：差分核验实跑（--check 模式零推送、零密钥、零写操作）

```bash
cp templates/config.example.json templates/config.json
# 编辑 templates/config.json：把 sitemap_url / site / host 换成你自己的站点
python3 templates/seo_pusher.py --check

# 预期输出（格式原文，实测样例）：
# sitemap=352 todo=352
#   diff: https://huodouai.com/
#   diff: https://huodouai.com/a2a
#   ...（逐条列出线上有、本地未推送的 URL）
```

`--check` 只抓取你的 sitemap 做差分比对，不向任何搜索引擎发送请求、不写任何密钥。首行两个数字应相等且等于你站点 sitemap 的实际 URL 数（打开 <你的站点>/sitemap.xml 数一下即可交叉核对）。

## 第 3 步（可选）：真实推送

在站点根放置 IndexNow 密钥文件后执行 `--push`（只推新增+变更）或 `--full`（全量），推送台账落在 `templates/push_ledger.jsonl`，逐条含时间戳与响应结果，可回查。
