#!/usr/bin/env python3
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
article = json.loads((ROOT/"article/process.json").read_text())
escape = html.escape
paragraphs = lambda rows: "".join(f"<p>{escape(p)}</p>" for p in rows)
body = paragraphs(article["paragraphs"])
plain = [article["title"], article["subtitle"], *article["paragraphs"]]
for section in article["sections"]:
    body += f'<h2>{escape(section["heading"])}</h2>' + paragraphs(section["paragraphs"])
    plain += [section["heading"], *section["paragraphs"]]
links = "".join(f'<li><a href="{escape(s["url"])}">{escape(s["label"])}</a></li>' for s in article["sources"])
plain += ["Sources"] + [f'{s["label"]}\n{s["url"]}' for s in article["sources"]]
document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(article['title'])}</title>
<style>@font-face{{font-family:Archivo;src:url('../assets/fonts/Archivo.ttf')}}body{{margin:0;background:#eeeae0;color:#24282d;font:18px/1.8 Archivo,sans-serif}}header,main,footer{{max-width:760px;margin:auto;padding:30px}}header{{border-bottom:1px solid #bbb;font-size:11px;letter-spacing:.12em}}a{{color:#244fc7}}h1{{font-size:clamp(38px,6vw,64px);line-height:1.05;font-weight:600;letter-spacing:-.05em}}h2{{font-size:30px;line-height:1.2;font-weight:500;margin:60px 0 20px;letter-spacing:-.03em}}.subtitle{{font-size:23px;color:#65685f;line-height:1.5}}.byline{{font-size:12px}}img,video{{width:100%;height:auto}}figure{{margin:35px 0}}figcaption{{font-size:11px;color:#666}}footer{{font-size:13px;border-top:1px solid #aaa}}li{{margin-bottom:12px}}</style></head><body>
<header><a href="../">BRIEFING STUDIO</a> / FIELD NOTES</header><main><h1>{escape(article['title'])}</h1><p class="subtitle">{escape(article['subtitle'])}</p><p class="byline">LEOGUOLABS · MADE WITH CODEX</p>
<figure><img src="../media/poster.jpg" alt="The complete engineering briefing board about AI and learning"><figcaption>One board holds the whole argument.</figcaption></figure>
{body}<figure><video controls playsinline preload="metadata" poster="../media/poster.jpg" src="../media/does-ai-help-you-learn.mp4"></video><figcaption>Does AI Help You Learn—or Just Finish?</figcaption></figure></main><footer><p>Sources and reference</p><ul>{links}</ul><p>Reference film: LemoLab, CC BY 4.0. <a href="../CREDITS.md">Full credits</a></p></footer></body></html>"""
(ROOT/"article/process.html").write_text(document)
(ROOT/"article/x-article.txt").write_text("\n\n".join(plain)+"\n")
print(f"Article prepared: {len(' '.join(plain).split())} words.")
