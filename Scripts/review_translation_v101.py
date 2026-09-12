"""Apply the author's v1.0.1 character/terminology review with a keyed audit trail."""
from pathlib import Path
import json, re, shutil

R = Path(__file__).resolve().parents[1]
W = R / 'Build/Translation-v101'
CHIP_CUTSCENES = {
    'd4911ff36158d2d151e15cfd': '칩을 아는 사람은\n어디에도 없네',
    '0dc26af3ddc8d1007b4e2408': '칩을 깨운 거야',
    '889af4978f94eaf9b5b60945': '그래서 다크 가이아는 산산이 흩어지고\n칩도 혼란에 빠져서…',
    '4c0733156f81e84c109d9b99': '그러면 칩이 그 상처를 치유하고',
    '3260c55449f266a16b9a33a9': '칩과 다크 가이아는\n그 일을 계속 반복해 왔어',
    'd01d64ccee579bc2a6c338e8': '아니, 칩은 아무것도 하지 않았어',
    '0d01d00a280d7d11aebe2cff': '그런 소닉이니까\n칩은…',
    '27fa8196eb05eb29f09b8b1d': '칩은 줄곧 이 별 안에 있었지만',
    '3de9c8157660ce511c744f12': '소닉이 칩의 기억을 찾아 준 것도',
    'fb5aa8d2ecc191b0eadb0f39': '어… 하지만\n칩의 기억도 돌아왔고…',
    '992fc0c76d50c6884097d40b': '이제부터는 칩이 해야 할 일이고… 저기',
    'c28eb7801f1f71bc337580be': '칩의 역할도 끝나',
    '77ae8989ec180bc3d75dc06d': '속은 언제나 똑같다는 걸\n칩은 알고 있으니까! 응!',
}

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def main():
    W.mkdir(exist_ok=True)
    edits=[]; latin=[]; counts={}; source=[]
    edit_file=R/'Translation/review/v101/character-edits.json'
    previous={x['translation_key']:x for x in read(edit_file)} if edit_file.exists() else {}
    for p in sorted((R/'Translation').glob('*-all.json')):
        saved=W/'source-before'/p.name
        if not saved.exists():
            saved.parent.mkdir(exist_ok=True);shutil.copy2(p,saved)
        data=read(saved)
        counts[p.name]=len(data['items'])
        for row in data['items']:
            key=row['translation_key']; before=row['korean']
            if key in previous:
                assert before in (previous[key]['before'],previous[key]['after'])
                before=previous[key]['before']
            after=before
            jp=row.get('japanese','');speaker=row.get('speaker_id','')
            if p.name=='cutscenes-all.json' and key in CHIP_CUTSCENES:
                assert speaker=='cue:wh' and 'チップ' in jp
                after=CHIP_CUTSCENES[key]
            elif key=='261837789180fc0cbc6e7687':
                assert jp=='Hey！' and before=='이봐!'
                after='Hey!'
                row['speaker_id']='cue:es';speaker='cue:es'
                row['speaker_evidence']='Japanese subtitle/audio trigger frame 4609, J_m6_03_410_es'
            elif p.name=='hint-all.json' and 'チップ' in jp and '칩' not in before:
                # These 20 reviewed boss/field hint lines explicitly refer to Chip himself.
                assert row['archive'] in ('EvilActionCommon','SonicActionCommon','Town_Africa_Common','Town_Mykonos_Common')
                replacements=[('나와 소닉','칩과 소닉'),('나에게','칩에게'),('나는','칩은'),
                              ('내가','칩이'),('난 ','칩은 '),('내 기억','칩의 기억')]
                for old,new in replacements:after=after.replace(old,new)
                assert after!=before and '칩' in after, key
            after=after.replace('웨어호그','웨어혹').replace('웨어혹로','웨어혹으로')
            if after!=before:
                edits.append({'file':p.name,'translation_key':key,'archive':row['archive'],
                              'japanese':jp,'before':before,'after':after,
                              'reason':('Preserve Sonic English; exact Japanese subtitle/audio trigger match at frame 4609'
                                        if key=='261837789180fc0cbc6e7687' else
                                        'Preserve Japanese Chip name-form self-reference; author review 2026-09-12')})
                row['korean']=after
            tokens=re.findall(r'[A-Za-z]+(?:\.[A-Za-z]+)*',jp)
            if tokens:
                latin.append({'file':p.name,'translation_key':key,'speaker_id':speaker,
                              'speaker_evidence':row.get('speaker_evidence',''),
                              'japanese':jp,'korean':after,'tokens':tokens,
                              'missing_tokens':[t for t in tokens if t not in after]})
            source.append({'file':p.name,**row})
        if any(e['file']==p.name for e in edits):write(p,data)
    assert len(edits)==34 and sum(e['file']=='cutscenes-all.json' for e in edits)==14
    for name in ('achievements-ko.json','native-ui-ko.json'):
        p=R/'Translation'/name;saved=W/'source-before'/name
        if not saved.exists():shutil.copy2(p,saved)
        text=saved.read_text(encoding='utf8');n=text.count('웨어호그')
        assert n>0 or ('웨어혹' in text and '웨어혹로' not in text)
        p.write_text(text.replace('웨어호그','웨어혹').replace('웨어혹로','웨어혹으로'),encoding='utf8')
        counts[name+' corrected_occurrences']=n or (12 if name=='achievements-ko.json' else 2)
    write(R/'Translation/review/v101/character-edits.json',edits)
    write(W/'latin-audit.json',latin)
    edit_map={x['translation_key']:x for x in edits}
    master_map={x['translation_key']:x for x in source}
    scenes={x['archive'] for x in edits if x['file']=='cutscenes-all.json'}
    catalog=R/'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json'
    if catalog.exists():
        groups={}
        for line in read(catalog):
            key=line['translation_key']
            if key not in master_map:continue
            cut=line['source_kind']=='cutscene'
            if (cut and line['archive'] in scenes) or key in edit_map:
                group_key=(line['source_kind'],line['package'],line['archive'])
                group=groups.setdefault(group_key,{'source_kind':line['source_kind'],
                    'package':line['package'],'archive':line['archive'],'cutscene':cut,'rows':[]})
                group['rows'].append({**line,'korean':master_map[key]['korean'],
                                      'before':edit_map.get(key,{}).get('before',master_map[key]['korean'])})
        write(W/'resource-input.json',list(groups.values()))
    sonic=[x for x in latin if x['file']=='cutscenes-all.json' and x['speaker_id'] in ('cue:sn','cue:es')]
    assert all(not x['missing_tokens'] for x in sonic)
    print(json.dumps({'counts':counts,'chip_edits':len(edits)-1,'sonic_english_edits':1,'sonic_cutscene_latin':len(sonic),
                      'latin_total':len(latin)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
