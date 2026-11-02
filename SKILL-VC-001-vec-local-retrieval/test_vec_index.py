#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向量底座单测：分块/去重/入库/近邻检索/写保护口径。编码器用桩向量，不依赖模型下载。"""
import importlib.util
import json
import os
import tempfile
import unittest

_s = importlib.util.spec_from_file_location(
    "vec_index", os.path.join(os.path.dirname(os.path.abspath(__file__)), "vec_index.py"))
V = importlib.util.module_from_spec(_s)
_s.loader.exec_module(V)


class FakeEnc:
    """桩编码器：按关键词给稳定向量，验证近邻序即可。"""

    def encode(self, texts, **kw):
        out = []
        for t in texts:
            v = [0.0] * V.DIM
            for i, ch in enumerate(t[:V.DIM]):
                v[i] = (ord(ch) % 97) / 97.0
            out.append(v)
        return out


class T(unittest.TestCase):
    def setUp(self):
        self.db = V.connect(":memory:") if False else None
        # sqlite-vec 走文件库；用临时文件
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
        self.db = V.connect(self.tmp)
        V.init_db(self.db)
        self.enc = FakeEnc()

    def tearDown(self):
        self.db.close()
        os.remove(self.tmp)

    def test_chunk_overlap(self):
        text = "甲" * 900
        chunks = V.chunk_text(text, size=400, overlap=50)
        self.assertTrue(all(len(c) <= 400 for c in chunks))
        self.assertGreater(len(chunks), 2)

    def test_add_and_dedup(self):
        """同块二次入库去重（只增不覆盖）。"""
        n1 = V.add_documents(self.db, self.enc, [("s", "p1", "逆元算子是真值算子的可逆补偿原语" * 10)])
        n2 = V.add_documents(self.db, self.enc, [("s", "p1", "逆元算子是真值算子的可逆补偿原语" * 10)])
        self.assertGreater(n1, 0)
        self.assertEqual(n2, 0)

    def test_search_returns(self):
        V.add_documents(self.db, self.enc, [
            ("s", "a", "AxiomGate 裁决内核负责准入与终审" * 8),
            ("s", "b", "联邦记忆池做双向同步与种子真值萃取" * 8),
        ])
        hits = V.search(self.db, self.enc, "记忆池同步", k=2)
        self.assertEqual(len(hits), 2)
        self.assertIn("distance", hits[0])
        self.assertLessEqual(hits[0]["distance"], hits[1]["distance"])

    def test_source_filter(self):
        V.add_documents(self.db, self.enc, [
            ("p1", "a", "向量底座内容块" * 20),
            ("p2", "b", "另一个池的内容块" * 20),
        ])
        hits = V.search(self.db, self.enc, "内容块", k=5, source="p2")
        self.assertTrue(hits and all(h["source"] == "p2" for h in hits))

    def test_stats(self):
        V.add_documents(self.db, self.enc, [("p1", "a", "统计口径样例" * 20)])
        st = V.stats(self.db)
        self.assertEqual(st["pools"].get("p1"), 1)


if __name__ == "__main__":
    unittest.main()
