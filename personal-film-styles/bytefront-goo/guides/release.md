# 验收、封存与回退

**从最终 MP4 检查。** 先逐镜抽取真实解码画面，另取每个风险动作的起、行、触、持、收帧。放大远肩、近肘、拇指和道具边缘；开场、标题、图例、字幕在真机尺寸下清晰。支撑手和托腮手的运动要避开头脸，校验首尾帧和任何遮罩过渡。检查字幕都有显示时间，镜头区间完全覆盖视频、无空洞或越界。

在 1× 播放器中连续听开场至少 60–90 秒、逐个跨过章节边界、术语与密集论证、结尾。记具体时间/文字和听到的现象。浏览器优先使用已授权的 Ego Lite；记录前进、拖动、结束、错误、掉帧。合成轨、原声、配乐、拟音分开定位啸声和速度变化。连续监听覆盖多久就写多久。

**技术检查。** 交付 3840×2160、24 fps、BT.709、H.264/yuv420p、AAC 48 kHz stereo。ffprobe 记录帧数、时长、色彩和音频格式；全片解码验证没有坏包。对最终 AAC 测 LUFS 和真峰值；分窗口对照冻结的 PCM 混音，排查编码或时间轴造成的漂移。所有 FFmpeg 命令通过以下入口，该入口获取跨工程共用锁，检查已有 FFmpeg 并等待：
```sh
python tools/frame_review/ffmpeg_gate.py -v error -i media/master.mp4 -map 0:v -map 0:a -f null -
python tools/frame_review/ffmpeg_gate.py -hide_banner -i media/master.mp4 -vn -af loudnorm=print_format=json -f null -
ffprobe -v error -show_format -show_streams -of json media/master.mp4
```

**交付清单。** 每种语言的最终 MP4、字幕与章节、冻结台词和来源版本、所有原始录音及其回执、词位、分镜与时间轴、图集与字体/许可、绘制与音频脚本、MIDI/分轨/混音、依赖锁、QA 报告和逐文件 SHA-256。用新目录离线重建（依赖可事先安装），验证原生 4K 关键帧与时间轴的哈希并解码。输出路径使用带版本的新文件名。归档去掉 node_modules、虚拟环境、凭据、浏览器会话和临时编码文件；校验 ZIP 哈希及实际可恢复性。个人风格版本、已检查、抽样/全检、听感是否已由用户接受分别写清。

报告模板：基线版本 / 脚本版本 / 中英声线和源文件 / 输出路径与 SHA / 实际帧数与时长 / 全片解码 / 图像样本的帧号与观察 / 接触帧与声画误差 / 连续试听区间与问题 / 如何修正、复测 / 档案恢复证据 / 仍开放的问题。

### 封存本期工程

成片停止写入后，在本期工程内执行。先查看 recipe.json 的文件列表，把本期另存的授权和报告列入其中，把非交付内容移出。source/ 可放原始文档和素材来源记录。导出位置都在工程外，均需是新路径。

```sh
python scripts/recipe.py > ../episode-recipe.json
python scripts/reproduction.py seal . ../episode-sealed --recipe ../episode-recipe.json
python scripts/reproduction.py check ../episode-sealed
python scripts/reproduction.py archive ../episode-sealed ../episode-source.tar.gz
python scripts/reproduction.py restore ../episode-sealed ../episode-restored
```

跨机器从压缩包还原时，先用 archive 命令打印的 SHA 运行 `python scripts/reproduction.py acquire ../episode-source.tar.gz ../received --sha256 HASH`，再 restore。进入恢复工程安装依赖，使用不同的输出文件名重新绘制。把真实重建与原工程的帧、声音、字幕相对照。
