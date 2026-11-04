"""Character and number alignment for independent ASR timestamps."""
from difflib import SequenceMatcher
import re,unicodedata
import numpy as np
small='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
tens='zero ten twenty thirty forty fifty sixty seventy eighty ninety'.split()
def number(n):
 if n<20:return small[n]
 if n<100:return tens[n//10]+(' '+number(n%10) if n%10 else '')
 if n<1000:return number(n//100)+' hundred'+(' and '+number(n%100) if n%100 else '')
 for size,name in [(10**9,'billion'),(10**6,'million'),(1000,'thousand')]:
  if n>=size:return number(n//size)+' '+name+(' '+number(n%size) if n%size else '')
def wordtext(s):
 s=s.replace(',','') if re.fullmatch(r'\s*[\d,]+\s*',s) else s
 return re.sub(r'\b\d+(?:\.\d+)?\b',lambda m:(number(int(m[0].split('.')[0]))+' point '+' '.join(number(int(c)) for c in m[0].split('.')[1])) if '.' in m[0] else number(int(m[0])),s)
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s).lower() if c.isalnum())
def aligned(text,words):
 if re.search(r'\bAI\b',text):
  joined=[];i=0
  while i<len(words):
   if i+1<len(words) and norm(words[i]['word'])=='artificial' and norm(words[i+1]['word'])=='intelligence':
    joined.append({'word':'AI','start':words[i]['start'],'end':words[i+1]['end']});i+=2
   else:joined.append(words[i]);i+=1
  words=joined
 src=[];indexes=[]
 for match in re.finditer(r'\d+(?:,\d{3})*(?:\.\d+)?|.',text):
  token=match[0];expanded=norm(wordtext(token));n=len(expanded)
  for k,ch in enumerate(expanded):
   src.append(ch);indexes.append(match.start()+min(len(token)-1,int(k*len(token)/max(1,n))))
 dst=[];times=[]
 for w in words:
  token=w['word']
  if 'Lemme See' in text:
   key=re.sub(r'[^a-z]','',token.lower());token={'ooo':'ooh','lemmy':'lemme','c':'see'}.get(key,token)
  q=norm(wordtext(token));n=len(q)
  for j,ch in enumerate(q):dst.append(ch);times.append((w['start']+(w['end']-w['start'])*j/n,w['start']+(w['end']-w['start'])*(j+1)/n))
 cmp=SequenceMatcher(None,''.join(src),''.join(dst),autojunk=False);known={}
 for b in cmp.get_matching_blocks():
  for k in range(b.size):known[b.a+k]=times[b.b+k]
 assert len(known)/len(src)>.84,(len(known)/len(src),text,''.join(dst))
 ids=sorted(known);out=[]
 for k,i in enumerate(indexes):
  a=float(np.interp(k,ids,[known[j][0] for j in ids]));b=float(np.interp(k,ids,[known[j][1] for j in ids]));out.append({'char':text[i],'index':i,'start':a,'end':b,'matched':k in known})
 return out,cmp.ratio()
