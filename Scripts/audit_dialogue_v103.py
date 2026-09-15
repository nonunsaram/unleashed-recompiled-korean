"""Audit screenshot-derived dialogue limits using the installed FTE atlas advances.
Widths use the game's 1280x720 design coordinates, not Unicode string length.
Runtime clipping still needs a playtest; no message is truncated to fit.
"""
from pathlib import Path
import json,re,collections,functools
R=Path(__file__).resolve().parents[1]
OUT=R/'Translation/review/v103'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ATLAS={r['character']:r['rect'][2]-r['rect'][0] for r in read(R/'Build/PlayableModWork/common-atlas.json')}
TOKEN=re.compile(r'\{GLYPH:[12]\}\{GLYPH:46\}|\{GLYPH:\d+\}|[^\r]')
def width(s):
 return sum(100 if t in ('{GLYPH:1}{GLYPH:46}','{GLYPH:2}{GLYPH:46}') else 35 if t.startswith('{GLYPH:') else ATLAS.get(t,28) for t in TOKEN.findall(s))
def hotdog(r):
 p=r['representative_line_id'].split('/')
 return 'TownMan_Hotdog' in p[-3] or (p[-3]=='StageList_list.fco' and int(p[-2])>=159 and int(p[-1]) in (4,5,6))
def profile(r):
 p=r['representative_line_id'].split('/')
 if r['translation_key']=='8bba07a559cbe206acede928' or r.get('status')=='확정 판정 · 원본 글리프 보존':return None
 if hotdog(r) and not (p[-2] in ('0','1','2','3') and p[-1]=='0' and 'TownMan_Hotdog' in p[-3]):return ('hotdog',720,3)
 if r['file']=='town-dialogue-all.json':return ('town',480,3)
 if r['file']=='hint-all.json':return ('hint',600,3)
 return None

def wrap(s,limit,max_lines):
 # Old line breaks are not hard boundaries. Review the whole message together.
 # This is only a proposal generator; manually reviewed boundaries are saved
 # in reflow-overrides.json and used verbatim during the build.
 words=s.split()
 @functools.lru_cache(None)
 def solve(i,n):
  if i==len(words):return (0,0,[])
  if n==0:return None
  best=None
  for j in range(i+1,len(words)+1):
   line=' '.join(words[i:j]); w=width(line)
   if w>limit:break
   tail=solve(j,n-1)
   if tail is None:continue
   penalty=(limit-w)**2
   if j<len(words):
    next_word=words[j].rstrip('!?.~…')
    if next_word in ('수','있어','있네','있는','없어','없는','보자','줘','테니','트라이얼') or words[j-1] in ('수','할','될','줄'):
     penalty+=limit*limit*4
   if line.endswith(('!','?','…','~','♪')):penalty-=limit*limit*.3
   if len(words[i:j])==1:penalty+=limit*limit*3
   result=(1+tail[0],penalty+tail[1],[line]+tail[2])
   if best is None or result[:2]<best[:2]:best=result
  return best
 result=solve(0,max_lines)
 return '\n'.join(result[2]) if result else None

def main():
 rows=[dict(file=p.name,**r) for p in sorted((R/'Translation').glob('*-all.json')) for r in read(p)['items']]
 candidates=[];failures=[];checks=[]
 for r in rows:
  pr=profile(r)
  if not pr:continue
  name,limit,lines=pr;s=r['korean'];ws=[width(t) for t in s.split('\n')]
  checks.append({'key':r['translation_key'],'profile':name,'widths':ws,'max_width':limit,'max_lines':lines})
  if len(ws)<=lines and max(ws,default=0)<=limit:continue
  after=wrap(s,limit,lines)
  item={**r,'profile':name,'widths':ws,'limit':limit,'after':after}
  candidates.append(item)
  if after is None:failures.append(item)
 write(OUT/'layout-audit-current.json',{'total_catalog':len(rows),'checks':checks,'candidates':candidates,'cannot_reflow':failures})
 # The original-source review is preserved separately in hotdog-review.json.
 print('SCOPE',len(rows),'PROFILE',collections.Counter(x['profile'] for x in checks),'FIXES',collections.Counter(x['profile'] for x in candidates),'CANNOT_REFLOW',len(failures))
 for r in failures:print(r['translation_key'],r['profile'],json.dumps([r['japanese'],r['korean']],ensure_ascii=False))
if __name__=='__main__':main()