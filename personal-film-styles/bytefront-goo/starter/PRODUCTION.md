# 当前单语言工程

当前工程采用 style-lock.json 指定的个人风格版本。读 guides/production.md 做本期脚本与分镜，guides/character.md 给出无录音预演和触物动作的命令。中英文分工程制作。参考图在 reference/gallery.html；角色原稿在 reference/character-reference.png。

在本目录执行 npm ci --ignore-scripts --no-audit --no-fund。用 Python 3.11 创建并激活虚拟环境，安装 requirements-rebuild.txt。新英文片的 voice-config.json 默认 Tim，美式男声；导入时统一 1.1 倍速，之后再对齐。详见 guides/tim-workflow.md。新录音先运行 python scripts/prepare.py，再按 guides/audio.md 生成英文或导入中文章节，最后运行 npm run proof 或 npm run build。单独查看某一帧可运行 node scripts/draw.mjs 3840 review/frame.png FRAME；先创建 review 并将 FRAME 替换为已规划的实际帧号。已有成片再改时给输出指定新文件名。

封存与恢复的完整命令见 guides/release.md；在新工程运行 scripts/recipe.py 后复核文件清单。
