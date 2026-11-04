# Goo 的画面与动作

定妆以用户给的 v04 黄卫衣角色表为准。头部体积、卷发、圆眼镜、门牙、宽松连帽衫、抽绳、袋口小蓝标、深蓝裤和白鞋构成同一个人。英文和中文分别使用自己的字标。角色表是生成新表情时的图像参考；搭建新场景优先复用已经绑定的部件。

| 元素 | 实作依据 | 现场检查 |
|---|---|---|
| 暖纸、平涂色块、棕黑断续墨线 | stage.mjs 的 begin/finish 和 toon.mjs 的 PAL。纸底 #F4EAD5，身份卡底 #F6EEDC，珊瑚色做接触提示，青绿给结果 | 缩小到手机尺寸，先看到动作与因果。纹理不可盖字；相邻帧的印色轻微错位即可 |
| 衣料与袖口 | goo.mjs 共用 GOO.hoodie 与 GOO.cuff，渲染色 #EEB83B。身份表的品牌目标色与实际图集采样各有用途 | 在同一帧把袖口、肩与腹部放大，检查色差、旧身体外轮廓、透明缝 |
| 头与躯干 | 先定脚底和躯干，再用脖子、衣领的遮挡固定头根；转头依托同一锚点 | 开始、中途、动作最大处逐帧查。需耸肩时跟着改两层重叠 |
| 左右手 | 标准人物朝画面右。**人物左手在画面右侧，是近手 −1；人物右手在画面左侧，是远手 +1。** 以拇指和掌背形状判别素材原侧 | 在草图上标“人物左/右、近/远、掌心/手背”。画面镜像时变换整条链；手掌素材仅在前臂局部空间依据手别翻转一次 |
| 手与道具 | goo-hand.mjs 的 handMarker、handWorldMarker、wristAtContact。手掌、短手腕、罗纹袖口属于一个绘制单元 | 取握点、指尖或掌垫作为世界接触点。按键在指尖触面时下沉，笔尖随纸上笔画，未接触时道具不能自行移动 |
| 肩、肘、层次 | 后臂底层 → 躯干/衣领 → 前景袖和交叠的支撑前臂。近肩与远肩前景区域完整覆盖衣服外线 | 分别查画面两侧。在屏幕左侧托腮支撑臂，仔细看肩上斜黑线有无穿出。握笔时肘在躯干外侧，手臂接近伸直，桌面与纸的位置要够得着 |
| 表演 | 用身份卡的观察、轻按、发现作性格基调。思索时视线先落到道具，托腮或扶镜，结论出现后才抬头 | 拇指方向、手指受力、头与手的接触比姿势数量重要。同一动作看进入、接触、停留、离开四相，播放时还要看快慢和遮挡 |

标题用 Alfa Slab One，手写提示 Oleo Script，正文和英文字幕 Jost；中文重标题 Noto Serif SC，正文 Noto Sans SC。实际字宽来自随包字体。字幕框可单/双行，逻辑舞台上 y=912–1034；控制每条长度，必要时分句、换布局。动作可用的几何尺寸是当前 rig 的局部值；不要把原数学场景的世界坐标硬套到新桌面。原握笔、按键和托腮的实作和样本可沿 baseline/README.md 的索引复核。

### 无录音时先出三帧

在新工程的 src/topic.mjs 登记一个自定义场景后，写一个临时 study.json，结构如下。先用 host 测角色，随后把 scene 换成新道具名，并按需要在 events 填预定接触帧。这个诊断文件独立于发行时间轴。

```json
{"language":"zh","duration_frames":90,"shots":[{"paragraph":"study","scene":"host","start":0,"end":90,"ground":"mustard","kicker":"先观察","title":"看清这次接触","label":"按下去会怎样","beat":"reaction","face":"think","events":{"contact":32}}],"captions":[]}
```
```sh
mkdir -p review
for frame in 0 32 66; do node scripts/draw.mjs 1920 "review/pose-$frame.png" "$frame" study.json; done
```

host 的 face 是表情基调；beat 可选 reaction、direction、release 等动态序列。acting 会固定指定姿势，可用 rest、present、chin、glasses、scratch、aha、shrug、surprise。要做角色与新道具接触，在自定义场景中调用如下接口：

```js
import {researcher} from './rebuild/stage.mjs';
// 脚底世界锚点 (500,810)，当前比例 1。把道具接触点换算进角色局部坐标。
const foot=[500,810], scale=1, tip=[720,550];
const local=[(tip[0]-foot[0])/scale,(tip[1]-foot[1])/scale];
researcher(c,...foot,{s:scale,frame:f,acting:'prop',face:'think',
  contact:{point:local,kind:'press',branch:-1}});
```

写字用 writeGrip；把握点、笔尖及桌面分开定义，再给道具应用与手相同的变换。在初、末帧之间插入局部接触目标的轨迹，并按动作阶段移动道具。以 reference/frames/motion-study.jpg 核对外肘与伸展。
