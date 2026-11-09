# OpenAI Realtime Cedar 英文旁白

《Ooh, Lemme See!》的新英文 Espresso Shorts、Byte by Byte 和咕仔影片使用 OpenAI `gpt-realtime-2.1-mini` 的 **Cedar** 音色。参照是用户于 2026-11-09 确认的 7.85 秒美式男声试听。具体语速和停顿在 `starter/profiles/en-cedar.json`，由新工程复制为 `voice-config.json`。

1. 新建英文工程并写好 `content/episode.json`。将片头和接着的正文放在同一个语义章。显示稿用 `text`，需要明确读法时另填 `spoken_text`。
2. 安装 `requirements-rebuild.txt` 和本地对齐所需的 `requirements-review.txt`。运行 `npm run narrate:en`，或用 `npm run narrate:en -- --chapter intro` 试读一章。
3. 合成程序在 macOS 钥匙串读取 `com.leoguolabs.goo.openai-realtime`。在其他机器或非 macOS 环境，可以通过进程环境配置有 Realtime 请求权限的 `OPENAI_API_KEY`。密钥保存在凭据存储，源代码、工程文件和回执只保存非敏感配置。
4. 每章用一个 Realtime 会话，以明确的美式男声指令按稿连续朗读。程序把原始 24 kHz PCM 和回执存入 `audio/original/`，然后保留音高，按参照收紧片头和句间空拍，输出 48 kHz mono WAV 到 `audio/chapters/`。交付语速以样音约 237 词/分钟为参照。原声偏慢时，保留音高的末段调速最多额外加快 15%。7.85 秒是同稿试听的时长，实际章节按内容和原声调整。
5. 播放最终 WAV 核对连读、Goo 的读法、末句及章节交界。用这份 WAV 重做词位、字幕、镜头、拟音和音乐。发布节目时标明旁白为 AI 生成。

重复运行会验证并复用已经冻结的章和回执。需要重录时先归档该章的原声、成片 WAV 及各自的回执。历史 Alloy 项目沿用冻结的配置。 [Realtime WebSocket](https://developers.openai.com/api/docs/guides/realtime-websocket) · [历史 Alloy 流程](alloy-workflow.md)
