#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地语义检索管线 —— SQLite + sqlite-vec 嵌入式向量索引，bge-small-zh 本地编码。
语义：文档分块 → 向量化 → 入库；检索走 vec 近邻 + 原文回读。
设计纪律：私有化部署、零新增成本、单文件库（备份即拷文件）、只增不覆盖（重建落新文件）。
"""

import hashlib
import json
import os
import sqlite3
import time

import sqlite_vec

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "vec_index.db")
DIM = 512  # bge-small-zh-v1.5
MODEL = "BAAI/bge-small-zh-v1.5"


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def connect(path=DB_PATH):
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    return db


class Encoder:
    """bge-small-zh 编码器：首次运行自动下载模型（约100MB，本地缓存后离线）。"""

    def __init__(self, model=MODEL):
        from sentence_transformers import SentenceTransformer
        self.m = SentenceTransformer(model)
        dim = (self.m.get_embedding_dimension()
               if hasattr(self.m, "get_embedding_dimension")
               else self.m.get_sentence_embedding_dimension())
        assert dim == DIM

    def encode(self, texts):
        return self.m.encode(list(texts), normalize_embeddings=True).tolist()


def init_db(db):
    db.execute("""CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL, path TEXT NOT NULL, chunk_no INTEGER,
        text TEXT NOT NULL, sha TEXT NOT NULL, added_at TEXT)""")
    db.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    db.execute(f"""CREATE VIRTUAL TABLE IF NOT EXISTS vecs USING vec0(
        chunk_id INTEGER PRIMARY KEY, embedding float[{DIM}])""")
    db.commit()


def chunk_text(text, size=400, overlap=50):
    """滑窗分块：中文按字符切，块间留重叠防切断语义。"""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out = []
    step = size - overlap
    for i in range(0, len(text), step):
        piece = text[i:i + size].strip()
        if len(piece) >= 30:  # 碎片不入库
            out.append(piece)
        if i + size >= len(text):
            break
    return out


def add_documents(db, enc, docs):
    """docs: [(source, path, text)]。同 sha 去重（只增不覆盖）。"""
    added = 0
    for source, path, text in docs:
        for no, chunk in enumerate(chunk_text(text)):
            sha = hashlib.sha256(chunk.encode()).hexdigest()
            row = db.execute("SELECT id FROM chunks WHERE sha=?", (sha,)).fetchone()
            if row:
                continue
            cur = db.execute(
                "INSERT INTO chunks(source,path,chunk_no,text,sha,added_at) VALUES(?,?,?,?,?,?)",
                (source, path, no, chunk, sha, _now()))
            vec = enc.encode([chunk])[0]
            db.execute("INSERT INTO vecs(chunk_id,embedding) VALUES(?,?)",
                       (cur.lastrowid, json.dumps(vec)))
            added += 1
    db.commit()
    return added


def search(db, enc, query, k=5, source=None):
    qv = json.dumps(enc.encode([query])[0])
    sql = """SELECT c.id, c.source, c.path, c.text,
                    v.distance FROM vecs v JOIN chunks c ON c.id=v.chunk_id
             WHERE v.embedding MATCH ? AND k=?
             """ + ("AND c.source=?" if source else "") + """
             ORDER BY v.distance LIMIT ?"""
    args = [qv, k] + ([source] if source else []) + [k]
    return [{"source": r[1], "path": r[2], "text": r[3], "distance": round(r[4], 4)}
            for r in db.execute(sql, args)]


def stats(db):
    n = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    pools = dict(db.execute("SELECT source, COUNT(*) FROM chunks GROUP BY source").fetchall())
    return {"chunks": n, "pools": pools}
