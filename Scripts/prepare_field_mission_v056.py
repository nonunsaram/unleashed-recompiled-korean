from pathlib import Path
import json,textwrap,collections,shutil
R=Path.cwd();D=R/'Translation/review/mission-field-audit-v056';P=R/'Build/FieldMission-v056'
for folder in ['Mod','Native','DirectArchives']:shutil.copytree(R/'Build/SharedMission-v055'/folder,P/folder,dirs_exist_ok=True)
a=json.loads((R/'Build/PlayableModWork/common-atlas.json').read_text(encoding='utf8'));width={e['character']:e['rect'][2]-e['rect'][0] for e in a}
def wrap(t):
 lines=[];line=''
 for word in t.split():
  candidate=(line+' '+word).strip()
  if line and (len(candidate)>12 or sum(width[c] for c in candidate)>260):lines.append(line);line=word
  else:line=candidate
 if line:lines.append(line)
 assert all(len(l)<=12 and sum(width[c] for c in l)<=260 for l in lines)
 return '\n'.join(lines)
x=json.loads((R/'Build/PlayableModWork/common-input.json').read_text(encoding='utf8'));groups=[];audit={};pairs=[]
for g in x:
 rows=[];bygroup=collections.defaultdict(dict)
 for row in g['rows']:
  if row['fco_file']!='StageList_list.fco':continue
  r=dict(row);before=r['korean'];role=r['cell']
  if role in ('Explanation','Hint','Worldmap') and before:
   plain=' '.join(before.split());r['korean']=wrap(plain) if role=='Worldmap' else '\n'.join(textwrap.wrap(plain,width=18,break_long_words=False,break_on_hyphens=False))
   assert ' '.join(r['korean'].split())==plain
   audit[(r['translation_key'],role)]={'key':r['translation_key'],'role':role,'before':before,'after':r['korean'],'japanese':r['japanese'],'english':r['english'],'max_line_width':max(sum(width[c] for c in l) for l in r['korean'].splitlines()),'lines':len(r['korean'].splitlines())}
   bygroup[r['group']][role]=r
  rows.append(r)
 for group,fields in bygroup.items():
  if 'Worldmap' in fields:
   wm=fields['Worldmap']
   for role in ['Explanation','Hint']:
    if role in fields:
     other=fields[role];pairs.append({'package':g['package'],'archive':g['archive'],'group':group,'worldmap_key':wm['translation_key'],'loading_key':other['translation_key'],'loading_role':role,'same_korean_wording':' '.join(wm['korean'].split())==' '.join(other['korean'].split()),'same_cell_index':wm['cell_index']==other['cell_index']})
 if rows:groups.append({**{k:v for k,v in g.items() if k!='rows'},'rows':rows})
assert all(not p['same_cell_index'] for p in pairs)
world=[v for v in audit.values() if v['role']=='Worldmap'];load=[v for v in audit.values() if v['role']!='Worldmap'];assert max(v['lines'] for v in world)<=3;assert max(v['lines'] for v in load)<=3
(R/'Build/PlayableModWork/mission-fields-v056-input.json').write_text(json.dumps(groups,ensure_ascii=False),encoding='utf8')
unique_pairs={(p['worldmap_key'],p['loading_key'],p['loading_role']):p for p in pairs}
summary={'worldmap_unique':len(world),'loading_unique':len(load),'worldmap_max_lines':max(v['lines'] for v in world),'loading_max_lines':max(v['lines'] for v in load),'distinct_role_pairs':len(unique_pairs),'same_wording_but_separate_cells':sum(p['same_korean_wording'] for p in unique_pairs.values()),'same_cell_pairs':0,'wording_preserved':True,'worldmap_max_characters':max(len(l) for v in world for l in v['after'].splitlines()),'worldmap_max_font_width':max(v['max_line_width'] for v in world),'worldmap_native_linebreaks_ja':sum('\n' in v['japanese'] for v in world),'worldmap_native_linebreaks_en':sum('\n' in v['english'] for v in world)}
(D/'summary.json').write_text(json.dumps(summary,indent=2));(D/'all-fields.json').write_text(json.dumps(list(audit.values()),ensure_ascii=False,indent=2),encoding='utf8');(D/'field-pairs.json').write_text(json.dumps(list(unique_pairs.values()),ensure_ascii=False,indent=2),encoding='utf8')
md='# 미션 문구 항목별 전수 조사 · 0.4.16\n\n로딩은 NameTag / Explanation / Hint를 읽고, 스테이지 선택 오른쪽 설명은 Worldmap 항목을 사용합니다. 같은 StageList 파일이어도 별도 셀입니다.\n\n'+ '\n'.join(f'- {k}: {v}' for k,v in summary.items())+'\n\n## 원본 언어와 한국어 비교\n\n|항목|일본어|영어|수정 한국어|\n|---|---|---|---|\n'
for v in world:
 if any(t in v['after'] for t in ['랜서','모레이','제한 시간','300개']):md+='|Worldmap|'+ '|'.join(v[k].replace('\n',' / ').replace('|','\\|') for k in ['japanese','english','after'])+'|\n'
md+='\n문장 축약·의역 없이 줄바꿈만 변경했습니다. Worldmap은 최대 12자 및 글꼴 폭 260 이내, Explanation/Hint는 공백 포함 18자 이내입니다. 두 종류 모두 최대 3줄입니다. 81종 위험 목록은 서로 다른 화면 항목을 혼합한 잘못된 분류여서 폐기합니다.\n'
(D/'README-KO.md').write_text(md,encoding='utf8')
s=(R/'Scripts/build_shared_mission_v055.ps1').read_text(encoding='utf8').replace('SharedMission-v055','FieldMission-v056').replace('SharedMissionWork-v055','FieldMissionWork-v056').replace('mission-loading-input.json','mission-fields-v056-input.json').replace("$r.cell_index-notin@(1,2)-or","")
(R/'Scripts/build_field_mission_v056.ps1').write_text(s,encoding='utf8');print(json.dumps(summary))
