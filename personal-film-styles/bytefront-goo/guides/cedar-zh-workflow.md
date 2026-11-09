# OpenAI Realtime Cedar 普通话旁白

《让我捅咕捅咕》的新中文长片、短片、Espresso Shorts 和 Byte by Byte 默认使用 **OpenAI `gpt-realtime-2.1-mini` / Cedar / 标准普通话男声**。用户于 2026-11-09 选定第一轮 14.564 秒普通话样音；台湾口音和后续试音不作为默认。英文使用独立的 `en-cedar.json`。

1. 新建 `--language zh` 工程。初始化器将 `starter/profiles/zh-cedar.json` 复制成 `voice-config.json`，其中保留样音的完整声音指令和处理参数。填写 `content/episode.json`，开场和紧接的正文放在同一语义章。术语、数字或英文缩写需要明确读法时填 `spoken_text`，字幕保留 `text`。
2. 安装 `requirements-rebuild.txt` 和本地对齐所需的 `requirements-review.txt`。运行 `npm run narrate:zh`，或 `npm run narrate:zh -- --chapter intro`。每章连续合成；正文长度变化不固定成 14.564 秒。
3. 复用本机 macOS 钥匙串的 `com.leoguolabs.goo.openai-realtime` 凭据。其他平台可配置有 Realtime 请求权限的 `OPENAI_API_KEY`。项目只记录配置和来源回执，不记录密钥。
4. 生成端 `speed=1.0`，完整保留已批准样音的普通话男声指令。处理端在 −43 dB、至少 0.22 秒的静音区间中将长停顿收紧至 0.26 秒；首尾留白分别保留 0.04／0.10 秒，切口淡化 6 毫秒。以每秒 5.4 个汉字为节奏目标，保留音高的提速最多 1.12 倍，不把自然较快的录音拉慢。批准样音实际触及 1.12 倍上限；这个目标值不是每期的硬性达标速度。
5. 两遍响度处理目标 −20 LUFS、真峰值 −2 dBTP、LRA 9，输出 48 kHz mono PCM16 WAV。成片混音继续按既有每章 −24 LUFS 的人声总线前规则平衡；音乐和播放器不再重复提速。检查“咕仔”“捅咕捅咕”、本期术语和完整末句，试听开场到正文的衔接。
6. 运行 `python scripts/align_chapters.py`、`python scripts/plan.py`。字幕、镜头和拟音全部绑定最终 WAV。程序校验原声、处理后音频、配置和回执的 SHA，重复运行复用已冻结的章节。重录前归档该章的原声、交付 WAV 和回执。

批准音频在本机忽略目录 `outputs/goo-voice-reference/cedar-zh-approved-20261109.mp3`；同目录保存原始 WAV、处理后 WAV、请求与回执，哈希写入配置。参数与批准样音已固定；新文本的实际发音仍需逐期听审。发布节目时标明旁白为 AI 生成。

历史中文数学片和已冻结的解说小明工程按原配置重建；该历史导入方法见 [audio.md](audio.md)。[OpenAI Realtime 文档](https://developers.openai.com/api/docs/guides/realtime-conversations#voice-options)
