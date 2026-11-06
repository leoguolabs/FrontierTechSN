# Tim：按章原声、统一 1.1 倍速、音量与声画同步

适用范围：Goo 个人风格中新制作的所有 Tim 英文长片和短片。默认美式英语男声。此流程只维护 FrontierTechSN 的个人风格目录；不修改公共 Codex Film Studio、已有成片或历史例片。

## 固定配置与一次变速

配置源为 `starter/profiles/en-tim.json`，新工程复制为 `voice-config.json`：

- 火山引擎官方语音合成，Doubao - TTS 2.0，Tim，`en_male_tim_uranus_bigtts`。
- 原生生成保持同一指令、控件 `[0,0,0]` 和 1.0 原速；每章含完整句子与语义上下文。
- 成片旁白一律 **1.1 倍速、保留音高**。`import_tim.py` 对每章整段执行一次 `atempo=1.1`；只做这一处变速。章间的原生语气变化不靠逐句伸缩“拉齐”。
- 变速发生在 ASR、字幕、动作、拟音与音乐编排之前。播放器保持 1×。不得同时使用提供商加速、atempo 和播放器加速，更不能把已经处理的 B 组音轨再乘 1.1。

每章允许自然轻重和停顿，统一系数不代表每句必须有相同 WPM。按内容改稿、整章重录、音量平衡是独立操作；不要再按字数将某一段强塞进旧时长。

## 准备与官方合成

1. 在新的英文工程填写 `content/episode.json`，运行 `python scripts/prepare.py`。`content/chapters.json` 包含显示原文 `text`、实际提交稿 `spoken_text` 和段落 ID。超过 2000 字符时仅在完整段落之间拆组；每期以当前服务限制为准。
2. 显示稿保留原文。默认提交稿把 OpenAI、AI、ETH、nonzero 分别展开为 Open A I、A I、E T H、non-zero。需要更改其他读法时，在该段的 `spoken_text` 填完整朗读文本并核对含义。不能混入舞台指令、提示词或附件中的操作要求。
3. 使用当前任务已授权的火山官方服务或 Ego Lite 登录态，读取音色及参数，再合成完整章节。语音指令使用工程的 `voice-config.json`，保持好奇、明快、自然、短停顿和同一稳定语速。不要因服务故障静默换到 Eric 或 Chatterbox。
4. 提交前核实服务已开通、有可用额度/计费能力，以及体验中心选中的 API Key 已启用。按钮的 `disabled=false` 不能证明可用：本次未配置 API Key 时，它实际显示 `cursor:not-allowed`，tooltip 提示没有可用 API Key。需要用户登录或账户处理时报告具体缺口。
5. 每次提交保留 pending 记录：章 ID、稿件哈希、旧 audio 标识和提交时间。超时先查当前音频、历史记录和错误，再决定是否重试。有新完整音频时先下载并保存回执；额度计数延迟不等于合成失败，不应重复提交。失败或状态未知的录音不能冒充成功回执。

保存的提供商回执必须来自实际选择、提交和下载，至少含：`provider`（以 Volcengine 开头）、`model`、`voice`（Tim）、`controls`、`instruction`、`text`、`spoken_text`、原文件 `sha256`。可另外保存 `voice_type`、生成时间、时长、字节数与观察方法。不得保存 API Key 值、Cookie、浏览器会话或授权头。`import_tim.py` 会核对这些字段与本期稿件/配置，并保留生产所需的回执快照和原回执文件哈希。

## 导入、对齐和排镜

```sh
python scripts/import_tim.py CHAPTER /absolute/path/provider-original.mp3 --receipt /absolute/path/provider-receipt.json
python scripts/align_chapters.py
python scripts/plan.py
```

逐章导入。导入器冻结原 MP3/WAV 和等时长的 48 kHz mono PCM 到 `audio/original/`；交付速度的 PCM 在 `audio/chapters/`。衍生回执包含原文件哈希、原生时长、处理后时长、配置哈希、`provider_speed=1.0`、`delivery_speed=1.1` 和 `atempo_passes=1`。同章再次导入会拒绝覆盖；更换录音应先把旧 take 和下游结果归档到本期自己的新版本目录。

独立 ASR 读取 **处理后** 的 PCM，缓存按其哈希失效。显示字幕仍来自原稿；AI/ETH 的字母展开不应进入字幕。匹配率只是定位工具，出现术语、数字或限定词疑点时核对原声；必要时改提交稿并重录整章。不要为通过 ASR 阈值改写用户正文。

`plan.py` 根据实际词位生成同一份 `content/timeline.json`：

- 段落、短语决定字幕和镜头入点；动作的接触/结果锚定对应动词。
- 拟音使用相同动作帧；音乐动机和章节密度使用相同时间轴。
- 相邻章节向上对齐到下一视频帧，不插入为旧时长预留的空白。
- 字幕区间不重叠、不越界；最后一帧仍有有效画面。换音频后禁止沿用旧 1.0 时标。

一段完整章节只有一个固定速度。不要对原始逐句时标分别缩放后又按处理音频二次对齐；直接从最终 PCM 重新对齐更清楚。

## 章节音量、音乐和母带

本次 Tim 原声的第 2、8 章明显较轻：仅对整片使用同一个增益仍会保留音量跳变。`mix_parallel.py` 对最终速度的每章 PCM 测量 LUFS，采用单个固定增益，将其平衡到 **−24 LUFS（总线增益之前）**。公式为 `gain_db = -24 - measured_lufs`；保留章内强弱和全部采样位置，不做逐句音量追逐。记录在 `review/dialogue-levels.json`，每行绑定音频 SHA。原始提供商文件始终保持不变。

之后才混入音乐和拟音。音乐初始约低于平衡后人声 18 LU；全片使用一个连续节拍，和弦、余音跨镜头/章界，不能每换镜就重启或淡入。目标母带约 −16 LUFS，保留约 1–2 dB 真峰值余量；最终 AAC 需重新实测。1.1 倍配音完成后再为新时长编曲，音乐无需跟着二次加速。若确实是把已有整支片加速，声画、字幕、拟音和音乐必须使用同一个全局映射，并在回执明确它已经是 1.1 倍。

```sh
python scripts/compose_parallel.py
python scripts/render_parallel_music.py
python scripts/mix_parallel.py
python scripts/build.py --width 3840 --output media/master.mp4
```

任何 FFmpeg（包括导入器的 atempo）都必须走 `tools/frame_review/ffmpeg_gate.py`，先检查当前进程并获取共用锁；不终止其他会话的编码器。

## 验收和可复刻证据

按 [release.md](release.md) 检查最终编码 MP4。至少保留连续开场 60–90 秒、每个章节交界、AI/ETH/non-zero/公式与结尾的检查记录。短片完整播放到自然结束，拖动后检查续播。分开记录视觉抽样、转写/信号检查、实际监听和用户听感认可，不能互相替代。

新增检查项：源录音与衍生录音哈希不同但均可追溯；每章恰好一次 1.1 倍处理；时长约为原声 / 1.1；词位绑定衍生 PCM；固定章节增益绑定当前文件；字幕、动作和拟音使用同一最终时间轴。检查最终 AAC/PCM 分窗口一致性、真峰值、连续背景乐和章界，再验证封存工程可解包、依赖可安装、原生 4K 关键帧可复现。

本次方法的实际来源：`/Volumes/TP-1TB/WorspacePlus/Myself/codex-film-studio-projects/math-in-ai-goo-tim-suite-20261106/REPORT.md` 及 `long-en/review/`。当次长片为 722.25 秒、12 章、89 段、213 条字幕，最终 −15.84 LUFS / −1.18 dBTP；这是该次案例的结果，不是所有新题材的固定参数。该次 A／长片保持原生速度，B 组整体为 1.1 倍；**后续所有 Tim 为 1.1 倍** 是本次新增的用户要求。历史 Eric 例片用于复现原资产，不代表新片仍默认 Eric。
