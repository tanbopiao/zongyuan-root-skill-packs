# 路由表 · seo-global-pusher

| 场景/触发词 | 意图 | 路由动作 |
| --- | --- | --- |
| "新内容上了，推给搜索引擎" | push | 运行 `seo_pusher.py --push`（sitemap 差分推送） |
| "第一次接入" / "新站上线" | init | 生成 key 并放置 → `--full` 建基线 |
| "只看看有什么待推" | check | `--check`（只差分不推送，巡检用） |
| "推送日志在哪" | audit | 读 `push_ledger.jsonl` 最近 N 条 |
| "百度通道开了吗" | baidu_status | 读 config：有 token 则已启用，否则 skipped |
| "被引擎拒收了" | debug_key | 检查 key 文件是否在站点根可公开访问（HTTP 200） |

## 宿主集成约定

- 固定低峰时段每日一班（如每日 10:20）；绿轮静默，失败/拒收才报告；
- 内容发布钩子（CI/部署脚本）末尾追加一次 `--push`，实现"上新即推"；
- 多站点矩阵：每站点一套 config+state，按站点目录隔离。

## 例外与边界

- state.json 与 ledger 均为本地真相，误删可由 sitemap 重建（丢 lastmod 历史而已）；
- key/token 入本地配置（600），不进代码库、不进台账；
- 收效验证走官方后台，不用第三方"收录查询"接口替代。
