"""Apply keyed v1.0.3 dialogue corrections and prepare physical resource inputs."""
from audit_dialogue_v103 import *
import shutil
W=R/'Build/Translation-v103'
# Reviewed Japanese/English alongside every changed row in edits.json.
# Match complete Korean text, including OCR source variants, never broad vocabulary.
REPHRASE={
 '그럼 포 유!! 핸드메이드 핫도그입니다!!':'자, 당신을 위해 준비했어요!!\n직접 만든 핫도그입니다~!',
 '감동했어!! 멋있어!! 시간에 쫓기며 질주하는 네 모습!':'감동했어!! 시간에 쫓기면서도\n질주하는 네 모습, 정말 멋있어!!',
 '아이야!! 역시 소닉이야!! 밤에도 빠르네!! 평범한 고슴도치가 아니야!':'아이야!! 역시 소닉이야!!\n밤에도 빠르네!!\n보통 고슴도치가 아니라니까!',
 '감동했어!! 멋있어!! 펄쩍펄쩍 뛰어다니는 네 모습!':'감동했어!! 펄쩍펄쩍 뛰어다니는\n네 모습, 정말 멋있어!!',
 '정말 인상적이야! 네 콤보! 어때? 기분 좋았어?':'네 콤보, 정말 인상적이야!\n어때? 기분 좋았어?',
 '최고야! 철벽같이 지키는 네 모습! 궁지에 몰려도 침착했어!':'철벽같은 방어, 최고야!\n궁지에 몰려도 침착하더라!',
 '감동했어!! 멋있어!! 네 긍지를 똑똑히 보여 줬어!':'감동했어!! 정말 멋있어!!\n네 긍지를 똑똑히 보여 줬구나!',
 '네 노력에 마음이 움직였어! 이번 시즌 가장 마음 따뜻한 추억이야!':'네 노력에 감동했어!\n올 시즌 가장 가슴 따뜻한 추억이야!',
 '다녀와라, 도전자여! 무사히 여기로 돌아오라고!?':'다녀와라, 도전자여!\n꼭 무사히 여기로 돌아와라!',
 '다녀와라, 도전자여! 네 삶의 방식을 보여 줘!':'다녀와라, 도전자여!\n네가 어떤 녀석인지 보여 줘!',
 '하라쇼!! 스파시바!! 피 끓고 살 떨리는 전투였어!!':'하라쇼!! 스파시바!!\n피가 끓어오르는 전투였어!!',
 '축하해!! 클리어야!! 차가운 마음으로 펼친 뜨거운 전투였어!!':'축하해!! 해냈어!!\n냉정함을 잃지 않으면서도\n뜨겁게 싸우더구나!!',
 '준비 운동은 OK입니까? 그러면 레디 고!!':'준비 운동은 OK인가요?\n그럼 준비, 출발!!',
 '싸울 각오는 OK입니까? 그러면 레디 고!!':'싸울 준비는 OK인가요?\n그럼 준비, 출발!!',
 '마이 갓!! 테크니션!! 그레이트!!':'마이 갓!! 솜씨가 대단해요!!\n그레이트!!',
 '마이 갓!! 크레이지!! 그레이트!!':'마이 갓!! 정말 화끈하군요!!\n그레이트!!',
 '그건 아주 힘든 미션입니다만… 도전 OK? 레디 고!!':'아주 힘든 미션인데…\n도전할 준비는 OK인가요? 출발!!',
 '링 내놔!! {GLYPH:1}{GLYPH:46}개 내놔!!':'링을 내 줘!!\n{GLYPH:1}{GLYPH:46}개면 돼!!',
 '그래서 소닉! 어떤 미션이 좋아?':'자, 소닉!\n어떤 미션이 좋아?',
 '극한의 땅에 자리한 핫도그 체인 돈 파치오 홀로스카점이다!':'혹한의 땅에 자리한 핫도그 체인\n돈 파치오 홀로스카점이다!',
 '이건 가벼운 트라이얼이다! 한번 멋지게 부탁한다고!':'이건 가볍게 도전할 만한 미션이야!\n한번 멋지게 달려 보라고!',
 'OK! 네 배짱에는 놀라게 된다니까! 클리어하면 좋은 걸 줄 테니 힘내라고!':'OK! 네 배짱에는 놀랐다니까!\n클리어하면 좋은 걸 줄 테니 힘내라고!',
 '레일 위를 미끄러지면서 차리리링♪ 하고 링을 먹는 소리, 최고지!':'레일 위를 미끄러지며\n차리리링♪ 하고 링을 모으는 소리!\n정말 끝내주지!',
 '휘유, 최고야! 링을 먹는 소리가 내 오장육부에 기분 좋게 울려 퍼졌다고!':'휘유, 최고야! 링을 모으는 소리가\n온몸에 기분 좋게 울려 퍼졌다고!',
}
MANUAL={
 '5a7b0ac326938b65bc8fff7d':'예전 소식일 수도 있지만\n샤마르, 엠파이어 시티,\n아다바트도 혼란스럽다더군…',
 '0202c7c3a72bc0596a564e07':'기둥 옆에서 {GLYPH:101} 버튼을 누르면\n기둥을 잡을 수 있어!',
 '8dc90388a8b019c31d9f3c02':'기둥 옆에서 {GLYPH:101} 버튼을 누르면\n기둥을 잡을 수 있어!',
 '493aab87fbdf127c2e9fd7f7':'드디어 엠파이어 시티로\n돌아갈 수 있겠어…',
 '42d19aac195f78fca3262acf':'드디어 엠파이어 시티로\n돌아갈 수 있겠어…',
}
def main():
 OUT.mkdir(parents=True,exist_ok=True); W.mkdir(parents=True,exist_ok=True)
 edits=[];rows=[];hot_review=[];checks=[];unknown=[];used=set()
 reflow=read(OUT/'reflow-overrides.json')['items'] if (OUT/'reflow-overrides.json').exists() else {}
 for p in sorted((R/'Translation').glob('*-all.json')):
  saved=W/'source-before'/p.name
  if not saved.exists():saved.parent.mkdir(exist_ok=True);shutil.copy2(p,saved)
  data=read(saved)
  for r in data['items']:
   r['file']=p.name
   before=r['korean'];after=before;reasons=[];key=r['translation_key'];pr=profile(r)
   if hotdog(r):
    plain=' '.join(before.split())
    if plain in REPHRASE:after=REPHRASE[plain];used.add(plain)
    elif 'StageList_list.fco' in r['representative_line_id']:
     # Keep complete clauses together when removing the old 11-character wrapping.
     after=plain.replace('오오, 좋은 구경 했어 ','오오, 좋은 구경 했어!\n').replace('흥… 제법이잖아 ','흥… 제법이군.\n')
     after=after.replace('그러면 레디 고!!','그럼 준비, 출발!!').replace('축하해!! 클리어야!!','축하해!! 해냈어!!')
    if re.sub(r'\s','',after)!=re.sub(r'\s','',before):reasons.append('Japanese-source meaning and natural Korean speech review')
   if key in MANUAL:
    after=MANUAL[key]
    if re.sub(r'\s','',after)!=re.sub(r'\s','',before):reasons.append('Shorten phrasing with source meaning retained')
   if key in ('5850cc90178d02e465b6abf3','389a5a9459f60864aa5dbebe'):
    assert before=='ATTACK이\n레벨 업했다!' and r['english']=='Strength\nleveled up!'
    after='STRENGTH가\n레벨 업했다!';reasons.append('Author request: match English STATUS UI rather than Japanese ATTACK label')
   if key in reflow:
    approved=reflow[key]
    assert re.sub(r'\s','',after)==re.sub(r'\s','',approved['before']),key
    after=approved['after']
    if approved.get('text_changed'):reasons.append('Meaning-preserving shortening for natural three-line Korean layout; reflow review')
   if pr:
    kind,limit,n=pr
    if len(after.split('\n'))>n or max(map(width,after.split('\n')),default=0)>limit:
     assert key not in reflow, ('Reviewed line boundary exceeds layout limit',key)
     after=wrap(after,limit,n)
     assert after is not None, (key,r['korean'])
    assert len(after.split('\n'))<=n and all(width(t)<=limit for t in after.split('\n')),(key,after)
    checks.append({'key':key,'profile':kind,'widths':[width(t) for t in after.split('\n')],'max_width':limit,'max_lines':n})
   if after!=before:
    if not reasons:reasons.append('FTE-width wrapping; preserve all non-whitespace text; maximum 3 visible dialogue lines')
    assert re.findall(r'\{GLYPH:\d+\}',before)==re.findall(r'\{GLYPH:\d+\}',after)
    assert all(t.startswith('{GLYPH:') or t=='\n' or t in ATLAS for t in TOKEN.findall(after)),(key,after)
    e={**r,'before':before,'after':after,'reason':'; '.join(reasons),'profile':pr[0] if pr else 'status'}
    del e['korean'];edits.append(e)
    r['korean']=after
    r['review_note']=(r.get('review_note','')+' [2026-09-16] '+e['reason']).strip()
   if hotdog(r):hot_review.append({'key':key,'file':p.name,'line':r['representative_line_id'],'japanese':r['japanese'],'english':r['english'],'before':before,'after':after,'result':'edited' if before!=after else 'source-compared; retained'})
   rows.append(dict(r));del r['file']
  if any(e['file']==p.name for e in edits):write(p,data)
 write(OUT/'edits.json',edits)
 write(OUT/'hotdog-review.json',hot_review)
 write(OUT/'layout-after.json',{'catalog_total':len(rows),'profiled_total':len(checks),'checks':checks,'in_game_verified':False,'excluded_placeholder':'8bba07a559cbe206acede928'})
 master={r['translation_key']:r for r in rows};emap={r['translation_key']:r for r in edits};groups={}
 for line in read(R/'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json'):
  key=line['translation_key']
  if key not in emap:continue
  assert line['source_kind']!='cutscene'
  gkey=(line['source_kind'],line['package'],line['archive'])
  g=groups.setdefault(gkey,{'source_kind':line['source_kind'],'package':line['package'],'archive':line['archive'],'cutscene':False,'rows':[]})
  g['rows'].append({**line,'korean':emap[key]['after'],'before':emap[key]['before']})
 write(W/'resource-input.json',list(groups.values()))
 print('EDITS',len(edits),collections.Counter(e['file'] for e in edits),'SEMANTIC',sum('wrapping;' not in e['reason'] for e in edits),'HOTDOG_REVIEW',len(hot_review),'ARCHIVES',len(groups),'PHYSICAL',sum(len(g['rows']) for g in groups.values()))
 print('UNUSED_REPHRASE',set(REPHRASE)-used)
if __name__=='__main__':main()