# 直尺回弹 · 无声动作练习

这是独立作者第一次接手风格包后制作的中英文动作练习。观察按住尺端、压弯、松开和弹回的四相。[四相近照](four-phases.jpg) · [中文动作](ruler-zh.gif)。起始接触帧 14，释放帧 34，总计 80 帧。topic.mjs 同时验证指尖和尺端坐标，误差须低于 0.001 逻辑像素。

从风格包根目录执行，目标选一个尚不存在的目录：

```sh
kit="$PWD"
python3 scripts/new_project.py "$HOME/Movies/Goo-ruler-study" --language zh
cd "$HOME/Movies/Goo-ruler-study"
npm ci --ignore-scripts --no-audit --no-fund
cp "$kit/examples/ruler-study/topic.mjs" src/topic.mjs
cp "$kit/examples/ruler-study/blocking-zh.json" study.json
mkdir -p review
for f in 0 14 30 41 79; do node scripts/draw.mjs 960 "review/ruler-$f.png" "$f" study.json; done
```

换英文时加载 blocking-en.json。两份诊断时间轴都不依赖旁白；制作有声正片时，把这些动作锚点绑定到本语言真实的词位。
