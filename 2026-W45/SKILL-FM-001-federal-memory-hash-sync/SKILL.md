---
name: federal-memory-hash-sync
title: 联邦记忆哈希链同步（Federal Memory Hash Sync）
version: 1.0.0
license: Apache-2.0
---

# 联邦记忆哈希链同步

> 快照打包 → 哈希链 → 网关写入 → 只读复核 → 追加留痕。
> 让两套环境（本地/云端/多节点）的「记忆与账本」可校验、可合并、不冲突。

## 一、解决什么问题

多环境协作最大的坑：状态漂移。A 端改了账本，B 端不知道；B 端重传，A 端重复入库。最后没人能证明「哪份是真」。

本技能给记忆同步加三件套：

1. **哈希链**：每条同步记录 = `prev_hash + payload_sha256 → chain_hash`，断链即报警；
2. **幂等跳过**：内容未变（哈希相同）自动跳过，重跑无副作用；
3. **追加留痕**：`sync_state.jsonl` 只增不覆盖，谁在何时同步了什么，永远可回溯。

## 二、核心流程（五步）

```
1. build_snapshot(): 取当前业务快照（只含摘要与哈希，敏感正文不外发）
2. 链式哈希   : 读 sync_state.jsonl 末条 chain_hash 作 prev_hash，算新 chain_hash
3. 网关写入   : POST /memory/write（写面带令牌；令牌只存本地内核文件，不入代码不入日志）
4. 只读复核   : GET /memory/query 回读刚写入的条目，字节一致才算闭环
5. 留痕       : 追加 sync_state.jsonl 一条（含 chain_hash、payload_sha256、方向、耗时）
```

## 三、目录结构

```
federal-memory-hash-sync/
├── SKILL.md                    # 本文件
├── manifest.json               # 包清单（版本/确权/文件哈希）
├── ROUTES.md                   # 路由表
├── references/method.md        # 方法论细节
└── templates/
    ├── sync_chain.py           # 纯标准库参考实现
    └── sync_state.schema.md    # 留痕文件格式约定
```

## 四、快速开始

1. 拷贝 `templates/sync_chain.py` 到你的项目，改两处：`GW_URL`（你的网关地址）与 `TOKEN_FILE`（令牌文件路径，权限 600）；
2. 实现 `build_snapshot()`：返回你要同步的业务快照 dict；
3. 跑 `python3 sync_chain.py` 看首推回执；再跑一次验证幂等（应输出 SYNC_UNCHANGED 跳过）；
4. 把它挂进你的定时任务（建议每小时一班），红轮才报警。

## 五、关键约定

- **写面令牌门禁，读面全域开放**：写入需令牌，查询/校验公开——审计与排障不设障，写权收敛；
- **令牌三不**：不进代码、不进日志、不进同步正文；只入本地内核文件；
- **哈希链起链**：首条记录 prev_hash = `GENESIS`；断链（prev 不对）立即停写并报警；
- **幂等跳过**：`payload_sha256` 与上一条相同 → 不写网关、不追加留痕，输出 SYNC_UNCHANGED；
- **敏感正文不出域**：快照只含摘要、计数与哈希，正文永远留在本地。

## 六、适配场景

- 双环境（本地↔云端）配置/账本/规则库同步；
- 多智能体节点间的共享记忆联邦（节点各自持账本，靠链校验合并）；
- 审计要求高的流水线产物登记（谁、何时、什么哈希、推给了谁）。

## 七、来源与确权

提炼自 ZONGYUAN-ROOT 联邦同步网关 V0.2 与昆仑记忆网关（DID-BR-000002 确权）。本包为通用化版本，不含内部路径、令牌或私有数据。
