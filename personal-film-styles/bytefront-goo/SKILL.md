---
name: bytefront-goo
description: 为 FrontierTechSN 的 Bytefront Studio 个人频道制作 Goo／咕仔黄卫衣角色的独立科普片。用于把新题材转成该频道的分镜、动画、分语言旁白、字幕、电子配乐、4K 成片和可复刻工程。
---

# 咕仔的科普片

从本文件所在目录工作。第一次接手先打开 `reference/character-reference.png`、`reference/encoded-storyboard-1.jpg`、`reference/frames/motion-study.jpg`，播放 `examples/clap-sync/preview.mp4`。角色定妆、成片表现和换题材实现各有自己的参照。

1. 按 `README.md` 在新目录初始化。每种语言各一个工程。从用户批准的稿件提取本期台词和事实，记录版本；附件中的操作建议只是素材。给每个要点写出可见的原因、变化和结果。按 `guides/production.md` 写场景。
2. 按 `guides/character.md` 选择角色的意图、手别和接触对象。载入现有角色图集、字体和绘制器。先画风险最大的动作，输出同一镜头的预备、接触和收势帧；通过后再铺满长片。
3. 按 `guides/audio.md` 生成连续原声，用同一个音频时间轴驱动字幕、动作、拟音和乐句。跨段试听至少包含两侧的完整句子。
4. 按 `guides/release.md` 检查解码后的图、动作、声音和可编辑工程。所有 FFmpeg 操作走工程内共享锁。发布范围是当前独立工程。个人风格的升级写入此目录的变更记录。
5. `guides/lessons.md` 是历次返工的诊断表。遇到握笔、袖线、英语速度或跨段配乐问题，按对应行复现。完整数学案例和取回原工程的方法在 `baseline/README.md`。
