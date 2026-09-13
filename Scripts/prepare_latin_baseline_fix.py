"""Create isolated fix inputs. Existing work is preserved; rebuild is explicit."""
from pathlib import Path
from PIL import ImageFont
import json, math, re, shutil
R=Path(__file__).resolve().parents[1];W=R/'Build/LatinBaseline-Audit'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    expected=read(W/'cutscene-expected.json')
    names=sorted({x['archive'] for x in expected if re.search(r'[A-Za-z0-9]',x['korean'])})
    index={x['archive']:x for x in read(W/'archive-index.json') if x['version']=='v102'}
    jobs=[];fixed=[]
    for name in names:
        source=Path(index[name]['folder']);target=W/'FixedWork'/source.name
        if not target.exists():shutil.copytree(source,target)
        jobs.append({'archive':name,'folder':str(target),'rows':[x for x in expected if x['archive']==name]})
        fixed.append({'archive':name,'folder':str(target),'version':'fixed','sha256':name})
    font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),27)
    widths={str(n):max(8,math.ceil(max(font.getlength(chr(n)),font.getbbox(chr(n))[2]-font.getbbox(chr(n))[0]))+2) for n in range(33,127)}
    for name,data in [('fix-jobs',jobs),('fixed-index',fixed),('latin-widths',widths)]:
        (W/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print('Prepared',len(jobs),'archives; existing work preserved.')
if __name__=='__main__':main()
