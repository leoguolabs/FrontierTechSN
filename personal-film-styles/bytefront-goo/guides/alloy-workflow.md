# OpenAI Alloy 英文旁白

本页用于保留 1.3.0 的历史 Alloy 工程流程。新英文项目使用 Cedar。 [Cedar 制作流程](cedar-workflow.md)版本 1.3.0 以用户在 2026-11-09 确认的 **7.85 秒 Alloy 试听**为节奏参照。各期按实际稿件和发音确定时长。

## 生成录音

1. 新建英文工程并完成 `content/episode.json`。按语义章组织连续朗读。显示稿使用 `text`，需要发音调整时用 `spoken_text`。片头和紧接的正文放在同一次请求里。
2. 在环境中配置 `OPENAI_API_KEY`，运行 `npm run narrate:en`。首次有品牌开场时，按 `requirements-review.txt` 配好本地 Whisper 词位依赖。可用 `npm run narrate:en -- --chapter INTRO` 只生成一章，将 INTRO 换成实际请求 ID。
3. 配置使用 OpenAI Audio API、`gpt-4o-mini-tts` 和 `alloy`。API `speed` 为 1.0，指令指定清楚、紧凑的美式口语，Goo 用硬 G 并与 *too* 押韵。脚本先收紧静音和开场节拍，然后用保留音高的 `atempo=1.08` 完成额外提速。片头后接正文时，参考 Goo 后约 0.06 秒、片名后约 0.12 秒的短停顿。停顿定位依赖原声词位与安静区间，交付前连听片头、接句和章节交界。
4. `audio/original/` 保存原始音频与来源回执，`audio/chapters/` 保存成片使用的 48 kHz mono WAV、处理记录和校验值。构建用交付 WAV 重新对齐词位、字幕、动作、拟音和音乐，并按章节平衡旁白响度。播放器保持 1×。要重做一章，先归档该章的原声、交付 WAV 和各自回执，再按同一请求 ID 生成。

## 导入官方试听页原声

没有 API 密钥时，可以用官方 OpenAI.fm 合成并下载原声，再用同一条处理链导入。记录页面实际使用的模型、音色、朗读稿和指令。来源回执 JSON 包含 `source: "OpenAI.fm"`、原文件的 `sha256`，以及 `request` 对象中的 `model`、`voice`、`input`、`instructions`、`speed`、`response_format`。如果页面没有独立的速度参数，使用原声默认值 1.0。已剪辑或已提速的音频应作为验收参照保存。

```sh
python scripts/synthesize_alloy.py --chapter intro --original /path/to/original.mp3 --receipt /path/to/openai-fm.json
```

真实 API 调用、官方试听页导入和后期处理分别保存在回执里。OpenAI 公布当前模型将于 **2027-01-06** 停用。更换模型时，先用用户确认的 Alloy 样音复核音色、开场和语速。对外发布时标明旁白为 AI 生成。 [OpenAI Speech API](https://developers.openai.com/api/reference/resources/audio/subresources/speech/methods/create) · [OpenAI 语音生成指南](https://developers.openai.com/api/docs/guides/text-to-speech)
