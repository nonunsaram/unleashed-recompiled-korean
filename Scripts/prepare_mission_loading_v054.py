from pathlib import Path
import json,textwrap,hashlib
R=Path(__file__).resolve().parents[1]
D=R/'Translation/review/mission-loading-v054';D.mkdir(parents=True,exist_ok=True)
groups=json.loads((R/'Build/PlayableModWork/common-input.json').read_text(encoding='utf8'))
result=[];unique={}
for group in groups:
    rows=[]
    for row in group['rows']:
        if row['fco_file']!='StageList_list.fco':continue
        item=dict(row);before=item['korean']
        if item['cell_index'] in (1,2) and before:
            plain=' '.join(before.split())
            after='\n'.join(textwrap.wrap(plain,width=18,break_long_words=False,break_on_hyphens=False))
            assert ' '.join(after.split())==plain
            assert all(len(line)<=18 for line in after.splitlines()),(row['line_id'],after)
            item['korean']=after
            key=item['translation_key']
            v={'translation_key':key,'before':before,'after':after,'japanese':row['japanese'],'english':row['english']}
            if key in unique:assert unique[key]==v
            unique[key]=v
        rows.append(item)
    if rows:result.append({**{k:v for k,v in group.items() if k!='rows'},'rows':rows})
(R/'Build/PlayableModWork/mission-loading-input.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
(D/'wrapping.json').write_text(json.dumps({'width_including_spaces':18,'abbreviated':False,'entries':list(unique.values()),'archives':len(result),'physical_cells':sum(len(g['rows']) for g in result)},ensure_ascii=False,indent=2),encoding='utf8')
print('Loading-only input:',len(result),'archives;',len(unique),'unique objectives/descriptions; no wording removed')
