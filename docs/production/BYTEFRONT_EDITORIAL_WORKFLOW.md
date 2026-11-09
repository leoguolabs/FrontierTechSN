# Ooh, Lemme See! / 让我捅咕捅咕 · 按需制作流程

身份更新：2026-11-02 用户指定英文名 `Ooh, Lemme See!`、角色 `Goo`，中文名 `让我捅咕捅咕`、角色 `咕仔`。新素材使用[咕仔 v04 规范](../brand/GOO_IDENTITY.md)，同一张 ID/横幅不混排中英文。Byte by Byte 与 Espresso 仍作为栏目；本文旧文件名为兼容历史链接保留。

生效决定：2026-11-02。新闻用 Espresso Shorts，重点新闻配合同题 Byte by Byte 深度解读。用户随后明确“不需要排期，把周期任务也删掉”，因此不设置制作日、发布时间、自动触发或自动发布；周更是此前的内容节奏讨论，不再作为执行器排期或 ID 文案。

## 已执行的停用操作

- 通过 Codex `automation_update` 删除 `frontiertechsn`（FrontierTechSN 视频巡检与连续生成），工具返回 `deleteStatus=deleted`。
- 删除后确认 `/Users/leoguo/.codex/automations/frontiertechsn/automation.toml` 不存在。没有新建替代周期任务。
- 本地 `data/daily_automation.json` 的 `enabled`、`catch_up_after_restart`、`auto_publish` 均已为 `false`，本次保持关闭。遗留时间字段不会在关闭状态下成为新排期。
- NexTrade 的无关任务未改动。没有检查或取消 YouTube 中可能已有的视频排程，也没有批量删除历史任务。

这份文档是新的按需制作操作标准，不是已接入旧 FastAPI 日更管线的配置文件。旧 Morning Desk 仍是日更长新闻实现，不因本文变成 Shorts；不要为了生产 Shorts 重新打开旧日更开关。本次没有启动新的新闻视频任务。

## 每次制作的入口

收到当前一次的选题/制作请求后，建立独立的 Codex Film Studio 工程，选 `midcentury-cartoon`，按[频道 ID 规范](../brand/GOO_IDENTITY.md)附上用户指定的咕仔原始角色参考图。从[当前身份入口](../brand/IDENTITY_CURRENT.json)取与该片语言一致的 ID；无文字头像共用。共享风格库只读，频道特有资产放在独立工程。项目路径以当前 `codex-film-studio` 子模块为库，不使用已经迁移的旧库路径。

项目命名建议：`espresso-YYYYMMDD-topic-slug`；对应深度片 `byte-by-byte-YYYYMMDD-topic-slug`。日期标识本次工程，不构成未来排期。同一事件共享 `topic_id` 和证据记录。

英文 Espresso Shorts 和 Byte by Byte 都使用个人咕仔风格的 **OpenAI Alloy** 旁白预设。可在单独的咕仔英文工程运行 `npm run narrate:en`，将最终章节 WAV 导入本期 Film Studio 工程，再以该 WAV 生成字幕和声画时间轴。开场按用户确认的节奏处理，提速已经写入 WAV。 [Alloy 制作流程](../../personal-film-styles/bytefront-goo/guides/alloy-workflow.md)

每期保存以下交付信息，未知值留空，不预造视频 ID 或公开链接：

```json
{
  "topic_id": "replace-with-topic-slug",
  "format": "espresso_short",
  "trigger": "user_request",
  "scheduled_at": null,
  "auto_publish": false,
  "identity_version": "goo-midcentury-v04",
  "identity_language": "en",
  "short_video_id": null,
  "deep_dive_video_id": null,
  "related_video_verified": false,
  "sources": [],
  "publication_receipt": null
}
```

## Espresso Shorts

制作目标：9:16、1080 × 1920，通常 45–75 秒，一条主要新闻。保持英文公开内容惯例；用户要求中文或双语时按该期请求执行，不强制所有新闻都做两个版本。

1. 查最近七天的候选事件，优先原始公告、论文、产品文档、财报或公开演示。分清发布日期、事件日期和证据条件。
2. 选择一个观众能理解的变化，不把旧八条日更简报压缩成一个短片。明确“发生什么、为何值得知道、尚不能推出什么”。
3. 脚本从事实或具体反差开场，前两秒进入主题。约 2–15 秒说明变化，15–45 秒给一项关键证据或演示，余下时间解释影响、限制和一个 CTA；时长随事实调整。
4. 固定角色操作纸卡、按钮或简单模型，让动作揭示事实。真实产品、实验、数据须准确；品牌图形不能代替证据。
5. 配音对齐字幕与动作；移除旧的 “Good morning”“today's briefing”“tomorrow morning” 固定问候和承诺。首镜直接进入内容，不使用旧日更长片开场/结尾模板。
6. 留存脚本、来源、字体/素材许可、配音、时间线、渲染命令、成片和检查记录。先做实际观看与听审，再交付可发布成片。

## 何时制作 Byte by Byte

满足以下内容条件时将重点新闻发展为深度片：事件有可核实的变化；背后机制或争议值得解释；有足够证据支撑一个完整问题；内容在新闻热度过后仍有价值。不是每条 Shorts 都必须扩写，不为了栏目联动制造结论。

深度片一般从一个问题展开，按“新闻中的变化 → 原理或历史背景 → 可观察的例子 → 限制和后果”组织。时长服务于论证，可从 8–12 分钟估算，不强行填满。保持同一角色与题材识别色，封面/标题提出不同层次的问题，避免把短片逐句拖长。

如当前请求只授权一个 Short，记录深度片建议；如已要求该重点新闻配套解读，则在同一工作范围中制作，不能让已完成的短片无限等待。不要自动建立周期或无期限监控。

## 两者的引流

| 当前状态 | Shorts 端 | Byte by Byte 端 |
| --- | --- | --- |
| 同题长片已经公开 | Studio 为 Short 设置同题 Related Video，末句提示完整解释 | 简介加入同题短片与 Espresso 播放列表入口；本次发布范围包含评论时再设置置顶评论 |
| 长片仍未完成 | Short 独立讲清新闻，不声称“点击看完整解读” | 长片发布时，在同一次发布工作中回填 Short 的关联视频与文案 |
| 没有对应长片 | 以结论或关注栏目结束，不关联无关视频凑数 | 无需强制搭配 |

Shorts 主 CTA（只有同题长片确已公开并配置关联时使用）：`For the full explanation, tap the related Byte by Byte video.`

长片简介模板（填入真实可打开的链接）：`For the short news version, watch [matching Espresso Short]. More tech news: [Espresso playlist].`

普通 Shorts 简介和评论中的 URL 不可点击，不能把它们当主引流入口。Related Video 需要高级功能权限；平台允许关联本频道公开或不公开列出的视频，本频道操作标准选择已经公开的同题长片，避免提前暴露待审版本。工具规则来源：[Related Video](https://support.google.com/youtube/answer/14075157?hl=en)、[可点击链接位置](https://support.google.com/youtube/answer/13748639?hl=en)，2026-11-02 核对。

## 交付与发布检查

交付时分别记录事实核对、技术解码、抽帧、连续动作观看、旁白听审、字幕阅读和主观风格意见。不能用文件存在、ASR 或解码通过代替实际音画审阅。

没有后台自动发布授权。用户对当次成片明确要求发布时，沿用已确认的频道设置，核对账号后发布；用户只要求制作时交付成片。不要写入未来发布时间，不重新创建定时任务。

实际发布时检查：同题关联是否有效；Short 是否进入正确栏目；长片/短片文案与内容一致；公开链接能播放；字幕与画面正常；Related Video 点击抵达同题长片。记录实际 YouTube ID 与回读证据，重试先查现有收据，避免重复上传。

线上首页仍以 Byte by Byte 优先、Espresso Shorts 次之、旧新闻归档在后的栏目结构为依据。2026-10-27 保存的 playlist ID 只是历史定位信息，实际发布或修改前应现场核对；本次没有重排线上首页或变更旧视频。
