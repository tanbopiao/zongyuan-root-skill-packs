#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建库示例：把任意目录下的 .md/.json 文档分块入库。用法：python3 build_index.py <文档目录...>"""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vec_index as V


def collect(roots):
    docs = []
    for root in roots:
        name = os.path.basename(root.rstrip("/")) or "docs"
        pats = [os.path.join(root, "**", "*.md"), os.path.join(root, "**", "*.json")]
        for pat in pats:
            for p in sorted(glob.glob(pat, recursive=True)):
                if not os.path.isfile(p):
                    continue
                try:
                    text = open(p, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                docs.append((name, os.path.relpath(p, root), text))
    return docs


def main():
    if len(sys.argv) < 2:
        print("用法: python3 build_index.py <文档目录> [更多目录...]"); sys.exit(1)
    db = V.connect(); V.init_db(db)
    enc = V.Encoder()
    docs = collect(sys.argv[1:])
    print(f"候选文档 {len(docs)} 份，开始分块编码入库…")
    added = V.add_documents(db, enc, docs)
    print("新增块:", added, "| 库存:", V.stats(db))


if __name__ == "__main__":
    main()
