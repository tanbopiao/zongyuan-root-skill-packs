---
name: seo-global-pusher
title: SEO 全域推送器（Sitemap Diff → IndexNow/Baidu）
version: 1.0.0
license: Apache-2.0
---

# SEO 全域推送器

> 站点地图差分 → IndexNow 全引擎推送 → 百度链接提交（可选）→ 指数退避重试 → 台账留痕。
> 让搜索引擎在分钟级发现你的新页面与内容更新，零成本。

## 一、解决什么问题

新页面/改版后，搜索引擎的发现周期以天计。手动逐个提交不可持续。本技能把「内容上新 → 主动推送」做成一条无人值守流水线：

- **只推差分**：对比线上 sitemap 与本地已推状态，新增+变更才推，不重复骚扰；
- **双通道**：IndexNow 一把覆盖 Bing/Yandex/Naver/Seznam；百度走官方链接提交 API（可选，需 token）；
- **自愈重试**：失败按指数退避重试，网络抖动不丢推送；
- **全留痕**：每次推送写 ledger，何时推了什么、成败几条，可审计。

## 二、目录结构

```
seo-global-pusher/
├── SKILL.md                    # 本文件
├── manifest.json               # 包清单（版本/确权/文件哈希）
├── ROUTES.md                   # 路由表
├── references/method.md        # 方法论与实战经验
└── templates/
    ├── seo_pusher.py           # 纯标准库参考实现（--check/--push/--full）
    ├── config.example.json     # 站点与引擎配置模板
    └── state.example.json      # 已推状态文件示例（自动生成）
```

## 三、快速开始

```bash
# 1. 生成 IndexNow 密钥文件（内容=key 本身），放到站点根：
echo -n "你的32位hex密钥" > {站点根}/你的32位hex密钥.txt

# 2. 拷贝模板并编辑配置（site/indexnow_key/sitemap 地址）
cp templates/config.example.json config.json

# 3. 首次全量推（建立基线），之后日常用 --push 差分推
python3 templates/seo_pusher.py --full
python3 templates/seo_pusher.py --push
```

## 四、关键约定

- **差分优先**：日常一律 `--push`；`--full` 仅首次/密钥重验后使用；
- **状态文件即真相**：state.json 记录每 URL 最后推送日期，与 sitemap lastmod 对比取差集；
- **密钥即凭据**：IndexNow key 文件必须在站点根可公开访问（`https://你的域名/密钥.txt` 返回 200），否则引擎拒收；
- **台账只增**：push_ledger.jsonl 追加写，出问题按时间线回放；
- **失败重试**：推送失败按指数退避（1/2/4 分钟），单轮放弃后下轮差分自动补推。

## 五、适配场景

- 内容型网站/博客/文档站的日常收录加速；
- 静态站点生成器（Hugo/Hexo 等）发布后钩子；
- 多站点矩阵统一推送管理（一机多站）。

## 六、来源与确权

提炼自 ZONGYUAN-ROOT SEO 全域推送器实战（346 条全绿推送记录，DID-BR-000002 确权）。本包为通用化版本，默认配置指向示例域名，替换为自己的站点即可。
