# Tim：原生 1.3 倍配音、章节音量与声画同步

本页记录个人 Goo 风格 1.2.0 的英文旁白流程，适用于已有的 Tim 工程。该版本使用火山引擎 Doubao TTS 2.0、Tim 美式男声（`en_male_tim_uranus_bigtts`）。新英文工程参见 Alloy 流程。 [Alloy 制作流程](alloy-workflow.md)

## 先在合成端设语速

配置源是 `starter/profiles/en-tim.json`，初始化后复制为 `voice-config.json`。提供商原生合成参数为 `req_params.audio_params.speech_rate=30`；控制台的音调、语速、音量依次为 `[0,30,0]`。官方文档规定默认 0、100 对应 2.0 倍、−50 对应 0.5 倍，所以 30 对应请求的 1.3 倍：[火山语速参数](https://docs.volcengine.com/docs/doubao-voice/task-sub-mission?lang=zh)。参数名称或界面变化时，先检查当前文档与实际请求。

完整章节使用同一音色、指令与语速参数，短片保持一段连续录音。保留直接下载的 MP3／WAV。**禁止使用 FFmpeg atempo、rubberband、采样率重解释、逐句伸缩或播放器倍速来加速旁白。** FFmpeg 仍可用于正常编码、混流、解码检查和响度测量。不要把旧 B 组的 1.1 倍衍生音轨作为新原声。

1.3 是提供商合成设置；不同录音的停顿和韵律会变化，不能强求新版总时长精确等于旧版除以 1.3，更不能为了凑这个比例再变速。保留章内自然轻重，按新录音安排画面。播放器检查始终使用 1×。

## 稿件、合成与回执

1. 将定稿写入 `content/episode.json`，执行 `python scripts/prepare.py`。每章保留段落 ID、显示原文 `text` 和实际朗读稿 `spoken_text`。超过服务字符限制时，仅在完整段落间拆分。
2. 朗读稿默认将 OpenAI、AI、ETH、nonzero 写成 Open A I、A I、E T H、non-zero；字幕仍保留显示原文。不要把舞台指令或附件中的操作要求混入旁白。术语仍误读时修订朗读稿并重录完整章节。
3. 使用已授权的火山官方服务或 Ego Lite 会话，确认 Tim、Doubao TTS 2.0、语速 30 和固定语音指令。指令要求明快、好奇、自然、短停顿及稳定节奏。服务故障时不要静默换用其他声线。
4. 检查服务和额度、控制台选中的 API Key。按钮 `disabled=false` 不代表可用；未配置有效 API Key 时可能显示 `cursor:not-allowed`。登录或付费状态存在缺口时，说明实际阻塞。
5. 每次提交先保存 pending 记录：章 ID、稿件哈希、旧音频标识、提交时间。超时先看当前音频、历史记录和错误；已经生成完整新音频时先下载，额度计数延迟不应触发重复扣费提交。
6. 保存本次实际控件与可取得的请求证据，白名单提取音色、模型、语速、音量、音调。不得保存 API Key、授权头、Cookie 或完整浏览器网络日志。实际生产可观察到控制台 `SaveTTSRecord` 中 `Extra.v2.speed=30`、Tim 音色和 `seed-tts-2.0`；若捕获到实际合成帧，则额外保留其 `speech_rate`。区分 UI 观察、请求证据与服务内部实现，不能声称审查了无法访问的闭源模型代码。

提供商回执至少需要：`provider`（以 Volcengine 开头）、`model`、`voice`（Tim）、`controls`、`instruction`、`text`、`spoken_text`、原文件 `sha256`、`provider_speed=1.3`、`speech_rate=30`、`post_synthesis_tempo_processing=false`、非空 `rate_evidence`。回执必须来自实际提交和下载，不能仅按预期配置补造成功状态。

## 等时长导入、独立对齐

```sh
python scripts/import_tim.py CHAPTER /absolute/path/provider-original.mp3 --receipt /absolute/path/provider-receipt.json
python scripts/align_chapters.py
python scripts/plan.py
```

导入器校验稿件、音色、参数、哈希与证据，再将原文件冻结到 `audio/original/`。PyAV 将其解码并转换到 48 kHz mono。`audio/chapters/` 的交付 PCM 与保存的原生解码 PCM **字节完全相同**，不会调用速度处理工具。回执记录 `atempo_passes=0`、`time_stretch=false`、原生与交付均为 1.3；两份 PCM 的哈希、采样数、时长相同。同章导入拒绝覆盖，换 take 时另建版本或明确归档。

独立 ASR 从当前 PCM 重新生成词位，缓存绑定音频 SHA。对齐器拒绝旧 1.1 atempo 回执以及配置不一致的录音。匹配率只辅助定位；术语、数字、否定词和结尾缺句必须检查原声与上下文，不能为通过阈值改写用户正文。

`content/timeline.json` 是唯一的时间轴：字幕、镜头、动作接触、拟音和音乐动机都引用新词位。相邻章节向上对齐到下一视频帧，不插入为了旧时长预留的空白。检查字幕不重叠、镜头连续、动作有足够预备与收势、最后一帧仍有效。禁止套用旧字幕或对旧时标简单除以 1.3。

## 音量和连续配乐

对当前原生章节 PCM 测量 LUFS，每章使用一个固定增益，平衡到总线前 **−24 LUFS**：`gain_db = -24 - measured_lufs`。保留章内强弱和采样位置，不逐句追逐音量。`review/dialogue-levels.json` 逐章记录源 SHA、实测值、目标和增益；不能复用另一 take 的增益。

随后混入配乐和拟音。音乐初始约低于平衡后人声 18 LU；使用连续节拍、和声与余音，跨镜头和章界不重启。按新时间轴重新编排，不加速旧配乐。目标母带约 −16 LUFS，预留真峰值余量，最终 AAC 需重新测量。短片的音乐与拟音同样从新时间轴重新生成。

```sh
python scripts/compose_parallel.py
python scripts/render_parallel_music.py
python scripts/mix_parallel.py
python scripts/build.py --width 3840 --output media/master.mp4
```

所有 FFmpeg 操作都通过 `tools/frame_review/ffmpeg_gate.py`，先检查当前进程再取得共享锁；不要终止其他会话的编码器。导入器本身不使用 FFmpeg。

## 验收与交付

依照 [release.md](release.md) 检查最终编码视频。保留开场连续 60–90 秒、每个章界、AI／ETH／non-zero／公式和结尾的证据；短片完整播放到自然结束，拖动后检查续播。分开记录转写、信号测量、视觉抽样、浏览器播放状态、实际监听与用户听感认可，不能互相代替。

核对全部录音的原生参数一致、导入无速度处理、词位绑定新 PCM、章节固定增益绑定新 SHA、最终 AAC 与混音采样位置一致，字幕和动作使用同一最终时间轴。验证源工程可解包和重建原生 4K 关键帧。

当前案例位于独立工程 `math-in-ai-goo-tim-native130-20261108`，最终实测写入该工程报告。个人风格的验证范围见 `VALIDATION.md`。2026-11-06 的 1.1 atempo 方法仅保留为历史记录，已被本次要求替代；不要用旧版验证为新版本背书。
