# Bytefront Studio · Goo / 咕仔

**个人风格 `bytefront-goo`，1.6.0。** 新作者从 [SKILL.md](SKILL.md) 开始。英文频道 ID 是 **Ooh, Lemme See! · Goo**，中文是 **让我捅咕捅咕 · 咕仔**。新英文节目使用用户确认的 **OpenAI Realtime Cedar 美式男声**，按 7.85 秒试听校准开场和正文节奏。新中文节目使用用户确认的 **Cedar 标准普通话男声**，语速和停顿沿用第一轮 14.564 秒样音。这个目录自带角色、绘制代码、字体、音频制作链和例片原料。每期的脚本、道具、音乐主题和交付物归该期自己的目录。 [英文 Cedar 流程](guides/cedar-workflow.md) · [中文 Cedar 流程](guides/cedar-zh-workflow.md)

### 给下一位 agent 的第一句话

> 读取 FrontierTechSN/personal-film-styles/bytefront-goo/SKILL.md。用咕仔风格做一期《〈新题材〉》，分别制作英文和中文。请在新的制作目录里工作。先选一个需要解释的动作，给我看 12–25 秒连续声画，再扩展到完整影片。

### 制作入口

| 想做什么 | 从哪里进入 | 产出 |
|---|---|---|
| 第一次认风格 | [定妆](reference/character-reference.png) · [成片逐镜索引](reference/gallery.html) · [18 秒打板小样](examples/clap-sync/preview.mp4) | 看人物、工作台、印刷色和真实节奏 |
| 换题材 | [制作步骤](guides/production.md) · [角色](guides/character.md) · [声音](guides/audio.md) | 每种语言一份可单独剪辑、导出和复查的工程 |
| 添加新闻、论文、图片或实拍 | [证据插段方法](guides/evidence.md) | 绑定具体台词、真实来源、可读黄笔与固定数据；允许零插段 |
| 复原数学原片或调查旧问题 | [原片档案](baseline/README.md) · [返工诊断](guides/lessons.md) · [验收](guides/release.md) | 查原帧号、原声证据、脚本及封存工程 |

### 从干净目录运行

需要 Node ≥20.11、Python 3.11、FFmpeg 和 ffprobe。下列命令从本风格目录执行。首次安装依赖需要访问包仓库；随包的历史 Eric 小样有真实录音和已对齐的词位，无须再调用 TTS 或下载 Whisper 模型。

```sh
python3 scripts/check_kit.py
python3 scripts/new_project.py "$HOME/Movies/Goo-clap-proof" --example clap-sync
cd "$HOME/Movies/Goo-clap-proof"
npm ci --ignore-scripts --no-audit --no-fund
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-rebuild.txt
npm run proof
npm run build
```

预览在 `media/proof.mp4`，4K 在 `media/master.mp4`。对应的章节、SRT、VTT、音乐 MIDI 和六个分轨都在工程内。重复编码时使用新的输出名，例如 `python scripts/build.py --output media/master-r2.mp4`。

制作新题材，从风格目录分别执行以下命令。填好新工程的 `content/episode.json`，在 `src/topic.mjs` 实现新道具和分镜。字段可对照 [打板脚本](examples/clap-sync/episode.json) 与[对应画面代码](examples/clap-sync/topic.mjs)。

```sh
python3 scripts/new_project.py "$HOME/Movies/Goo-next-en" --language en
python3 scripts/new_project.py "$HOME/Movies/Goo-next-zh" --language zh
```

**升级风格**：锁定版本跟随每个新工程。以后修改基础角色、节奏或配乐时按 [升级办法](CHANGELOG.md) 留下前后对照与测试。历史基线、新题材小样和用户的主观认可分别记录。

另外两个校准材料可直接用于审片。原片的连续 90 秒 Eric 录音用于历史跨段衔接校准。直尺回弹预演演示真实手指压住物体、松开并让物体回弹。打板例的原生 4K 接触帧和交接验证报告可用于核对重建结果。 [原片声音](reference/opening-90s-v29.m4a) · [直尺回弹预演](examples/ruler-study/README.md) · [接触帧](examples/clap-sync/contact-4k.jpg) · [验证报告](VALIDATION.md)
