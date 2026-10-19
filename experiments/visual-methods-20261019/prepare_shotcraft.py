"""Adapt three Apache-2.0 shot recipes, retaining the source motion grammar.
Original source: Vincentwei1021/video-shotcraft @ 43bd349a136651865ecfa6ea1cf012f6e957d304.
The generated vendor directory is reproducible and intentionally not committed.
"""

from pathlib import Path
import shutil
import re

BASE = Path(__file__).resolve().parent
SRC = BASE.parents[1] / "outputs/visual-methods-20261019/vendor/video-shotcraft"
OUT = BASE / "react/vendor"
OUT.mkdir(parents=True, exist_ok=True)
shutil.copytree(SRC / "demos/_fixtures", OUT / "_fixtures", dirs_exist_ok=True)
for slug, cat, name in [
    ("orbit-ring-title-open", "opening", "OrbitRingTitleOpen"),
    ("scanline-annotate-focus", "effects", "ScanlineAnnotateFocus"),
    ("word-relay-geometry", "typography", "WordRelayGeometry"),
]:
    s = (SRC / f"demos/{cat}/{slug}/{name}.tsx").read_text()
    s = s.replace("../../_fixtures/", "./_fixtures/")
    s = s.replace(
        "const { fps } = useVideoConfig();",
        "const fps = 30; // source frame coordinates are virtual 30 fps",
    )
    s = s.replace('<ShotcraftMark size={44} tone="dark" />', "").replace(
        '<ShotcraftMark size={34} tone="dark" />', ""
    )
    s = s.replace("{BRAND.name}", "Bytefront")
    if name == "OrbitRingTitleOpen":
        replacements = {
            "'让镜头卡替你想好'": "'An AI model can give you'",
            "'每一个动效'": "'an answer'",
            "'SHOT RECIPE CARDS'": "'THE STARTING POINT'",
            "5.33 - 0.14) / 5.05": "4.58 - 0.14) / 4.30",
            "Motion, considered.": "A starting point.",
            "Every card ships with timing, easing": "A useful response to your goal.",
            "and a validated reference build.": "The next step is yours.",
            "RELEASE NOTES · 4.2": "CONCEPTUAL RESPONSE",
            "RENDERS / DAY": "OUTPUT SIGNAL",
            "+18.4%": "RESULT",
            "Draft the storyboard": "Read the goal",
            "Pick shot cards": "Choose a tool",
            "Tune easing curves": "Inspect the result",
            "Render & review": "Adjust the next step",
            "ETA 12 min": "A possible route",
            "~/shotcraft": "~/agent-loop",
            "$ npx remotion render Open": "$ use_tool(goal)",
            "✓ Bundled in 2.1s": "✓ Operation returned",
            "  Rendering frames 0–149": "  Checking the result",
            "✓ Done → out/open.mp4": "✓ Ready to inspect",
            "WEEKLY SUMMARY": "GOAL SUMMARY",
            "12 shots approved": "One goal received",
            "3 pending review · 1 re-render": "Work still to be checked",
            "Q3 launch plan": "The next action",
            "Owner · Studio team": "Use the result",
            "Due Oct 18": "Adjust the plan",
            "2026 · Q3": "NEXT STEP",
            "GO LIVE": "TAKE ACTION",
        }
        for a, b in replacements.items():
            s = s.replace(a, b)
        s = s.replace(
            "const val = 128 + Math.round(F(f, 8, 40, Easing.out(Easing.quad)) * 84);",
            "const val = 'READY';",
        )
    if name == "WordRelayGeometry":
        for a, b in {
            "word: 'Faster'": "word: 'Action'",
            "word: 'Tighter'": "word: 'Feedback'",
            "word: 'Stronger'": "word: 'Correction'",
            "One prompt to a finished promo.": "Take a concrete step.",
            "Every cut locked to the beat.": "Inspect what came back.",
            "Launch films that feel studio-made.": "Change the next action.",
        }.items():
            s = s.replace(a, b)
        s = s.replace("...type(40, 450)", "...type(56, 450)")
        s = s.replace("s.in0 + (i === 2 ? 34 : 16)", "s.in0 + 12").replace(
            "each={16} gap={2.2}", "each={12} gap={1.5}"
        )
        s = s.replace("146", "136").replace("148", "138").replace("158", "148")
    if name == "ScanlineAnnotateFocus":
        a = s.index("  const ts: Target[] = [")
        b = s.index("  ];", a) + 4
        s = (
            s[:a]
            + """  const ts: Target[] = [
    {key:'goal',x:70,y:180,w:1420,h:138,head:'GOAL',detail:'Read',tag:'above',ft:0},
    {key:'tool',x:70,y:400,w:1420,h:138,head:'TOOL',detail:'Use',tag:'above',ft:0},
    {key:'result',x:70,y:620,w:1420,h:138,head:'RESULT',detail:'Check',tag:'above',ft:0},
  ];"""
            + s[b:]
        )
        a = s.index("const Page: React.FC =")
        b = s.index("// ───────────── 取景框", a)
        s = (
            s[:a]
            + """const Page: React.FC = () => (
 <div style={{position:'absolute',inset:0,background:'#f8f2e9',fontFamily:FONT.sans,color:L.ink}}>
  <div style={{position:'absolute',left:70,top:60,fontSize:28,letterSpacing:3,color:L.ink3}}>CONCEPTUAL AGENT OPERATION / 03 STEPS</div>
  {[
   ['01','Read a goal','What result are we trying to produce?'],
   ['02','Use a tool','Carry out a concrete operation.'],
   ['03','Check the result','Use the evidence to guide the next action.']
  ].map(([n,title,sub],i)=><div key={n} style={{position:'absolute',left:86,top:196+i*220,width:1388,height:106,borderBottom:'1px solid #d9cdbc',display:'flex',alignItems:'center',gap:44}}><div style={{fontSize:80,fontWeight:700,color:TERRA}}>{n}</div><div style={{width:590,fontSize:58,fontWeight:700,letterSpacing:-2}}>{title}</div><div style={{width:530,fontSize:32,lineHeight:1.2,color:L.ink2}}>{sub}</div></div>)}
 </div>
);

"""
            + s[b:]
        )
        s = s.replace("'BRAND READ'", "'RESULT CHECKED'").replace(
            "'READING'", "'INSPECTING'"
        )
        s = s.replace("SIGNALS ", "STEPS ")
        # Keep the sample fully in the safe area and reserve a clean status line.
        s = s.replace("const WY = 168;", "const WY = 150;").replace(
            "const WH = 840;", "const WH = 840;"
        )
    (OUT / f"{name}.tsx").write_text(s)
shutil.copy2(SRC / "LICENSE", OUT / "LICENSE")
# Adapt the source clock explicitly, including fixture effects and the opening's
# nested frozen card clock. Remotion Freeze clamps virtual global frames to the
# root composition duration, truncating the last shot when changing frame rates.
for path in OUT.rglob("*.tsx"):
    s = path.read_text()
    if "useCurrentFrame" not in s and "<Freeze" not in s:
        continue
    s = re.sub(
        r"import \{([^}]+)\} from 'remotion';",
        lambda m: (
            "import {"
            + ", ".join(
                x.strip()
                for x in m[1].split(",")
                if x.strip() not in ("useCurrentFrame", "Freeze")
            )
            + "} from 'remotion';"
        ),
        s,
    )
    s = s.replace("useCurrentFrame()", "useRecipeFrame()")
    s = s.replace("<Freeze ", "<RecipeFrameProvider ").replace(
        "</Freeze>", "</RecipeFrameProvider>"
    )
    prefix = (
        "../../RecipeClock" if path.parent.name == "_fixtures" else "../RecipeClock"
    )
    s = "import {useRecipeFrame, RecipeFrameProvider} from '" + prefix + "';\n" + s
    path.write_text(s)
print("Prepared exact recipe adapters in", OUT)
