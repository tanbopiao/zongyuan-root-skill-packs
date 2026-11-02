# 独立验证指南（任何人 / 任何 AI 可执行）

前置：Python 3.10+，联网安装一次依赖。

```bash
# 第 1 步：完整性核对（对照 SHA256SUMS）
sha256sum -c SHA256SUMS

# 第 2 步：安装唯一外部依赖
pip install sqlite-vec

# 第 3 步：运行单元测试（桩编码器，不下载模型，秒级完成）
python3 -m unittest test_vec_index -v

# 预期输出（原文）：
#   test_chunk_overlap (test_vec_index.T.test_chunk_overlap) ... ok
#   test_add_and_dedup (test_vec_index.T.test_add_and_dedup) ... ok
#   test_search_returns (test_vec_index.T.test_search_returns) ... ok
#   test_source_filter (test_vec_index.T.test_source_filter) ... ok
#   test_stats (test_vec_index.T.test_stats) ... ok
#   ----------------------------------------------------------------------
#   Ran 5 tests in 0.0XXs
#
#   OK

# 第 4 步（可选，需模型）：真实语义检索体验
#   mkdir -p ~/my-docs && echo "逆元回滚通过乘法逆元将除法转化为乘法，是底层原语。" > ~/my-docs/demo.md
#   pip install sentence-transformers
#   python3 build_index.py ~/my-docs
#   预期：日志显示"候选文档 1 份"，新增 1 块，库存统计含 chunks: 1
```

任何一步与预期不符，即验证失败——请携带输出提交 issue。
