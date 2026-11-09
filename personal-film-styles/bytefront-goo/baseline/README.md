# 原片证据与恢复入口

| 基线 | 实际交付 | 核验与代表用途 |
|---|---|---|
| 英文 Math in AI v29 | math-in-ai-goo-v29/media/math-in-ai-en-4k-rebuild-v29.mp4，13,763 帧，9:33.458 | verification.json、continuity.json、music-mix.json、caption-timeline.json、player-check.json、visual-observations.json。用于角色、连续 Eric、电子乐、图文与播放器检查 |
| 中文 Math in AI v23c | math-in-ai-goo-v23/media/math-in-ai-zh-4k-rebuild-v23c.mp4，16,778 帧，11:39.083 | verification-zh-v23c.json。男声为火山解说小明 2.0。两国语速与时间轴独立 |
| 封存可编辑工程 | math-in-ai-goo-v29-editable.zip，986,367,299 字节，689 个清单内文件 | archive-check.json 有完整 SHA、恢复证据及四个原生 4K 校准帧。包含中英原料；成片另存 |

本机项目库是 `/Volumes/TP-1TB/WorspacePlus/Myself/codex-film-studio-projects`。可将档案拷到其他盘，下面的命令接收实际路径。新题材模板自带基础材料。精确回看原片才需要这份大型外部档案。

```sh
python3 scripts/restore_baseline.py "/path/to/math-in-ai-goo-v29-editable.zip" "/new/path/math-v29"
```

该命令从风格目录运行，先验证封存 ZIP 的已知 SHA，检查条目路径和类型，再按内部清单逐文件核验和解包。恢复后按照档案中 README.md 运行原工程，使用本机支持的原生编码器。可用 verification*.json 核对另存的 MP4。基线参考图来自真实编码文件；包内 reference/frames/index.json 给出镜头功能、时间、帧号和缩略图哈希。编码器或平台改变时可有字节差异。

### 查实现

- math-episode/content/narration-{en,zh}.json 保留本期段落；rebuild-{en,zh}.json 是分镜；rebuild-captions-{en,zh}.json 是字幕排布；motion-v16.json 是动作节拍。
- math-episode/src/rebuild/scenes.mjs 的 study()、starter/src/rebuild/goo.mjs 的 writingReach() 和 goo-hand.mjs 的接触标记一起读。其余具体课题道具和转场实现保存在相邻模块。这份案例节选用于查阅，完整可运行的原片依赖由 ZIP 提供。
- 原片测过英文 89 段、12 章；章内 77 个相邻段的 ASR 估计间隙中位数 0.598→0.247 秒，P90 为 0.707→0.426 秒，对比的是 v27 和 v29。v29 编码成片为 −15.99 LUFS / −1.63 dBTP。这些数值用于重现历史，并非其他视频的硬指标。
- 明确认可的是 v15 的运动速度、v23b 的握笔方向。v29 的听感保留为待主观评价。原片视觉报告记录规则开关镜头中短暂的手臂与标题重叠；新镜头的文字应避开操作路径。

math-episode 中的 DIRECTOR/METHOD/AUDIO/PRODUCTION/REVIEW 是原档按原样摘留的历史文件，可能描述前期技术或后来淘汰的选择。本版本默认决策以个人风格 guides 和上表记录的实际交付为准。


## 2026-11-09 中文证据画面重剪

独立工程：`FrontierTechSN/outputs/goo-evidence-20261109/`。沿用上述中文 v23c 的 16778 帧基线与原 AAC 音轨，在六处加入真实来源、原创计算图、论文实页与课堂情境；共 59.875 秒。完整 4K 和 1080p 片分别为 `media/math-ai-zh-evidence-r2-4k.mp4` 与 `media/math-ai-zh-evidence-r2-1080p.mp4`，可编辑包为 `goo-ai-math-zh-editable-20261109.zip`。

[四段参考逐帧研究与本期对应关系](../../../production-records/2026-11-09-goo-evidence/REFERENCE-ANALYSIS.md) · [来源与剪辑参数](../../../production-records/2026-11-09-goo-evidence/evidence.json)。方法升级到 1.4.0，但本案例沿用冻结的中文录音，不应用英文 Alloy 参数。参考 YouTube 的 840 个取样位置仅用于本地分析，没有进入成片。原片的完整历史动画重建不在本次重新验证范围内，新增插段与本次合成链有独立源码和重建检查。
