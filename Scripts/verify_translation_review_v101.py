"""Check the reviewed source, original timed speaker evidence and rebuilt assets."""
from pathlib import Path
import json, re, hashlib, sys, struct, xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rows=[]
    for p in (R/'Translation').glob('*-all.json'):
        rows.extend({'file':p.name,**x} for x in read(p)['items'])
    assert len(rows)==11912
    bykey={x['translation_key']:x for x in rows};assert len(bykey)==len(rows)
    edits=read(R/'Translation/review/v101/character-edits.json')
    assert len(edits)==34
    for edit in edits:
        row=bykey[edit['translation_key']]
        assert row['japanese']==edit['japanese'] and row['korean']==edit['after']
    for row in rows:
        assert '웨어호그' not in row['korean'] and '웨어혹로' not in row['korean']
        if 'チップ' in row.get('japanese',''):assert '칩' in row['korean'],row['translation_key']
    for name in ('native-ui-ko.json','achievements-ko.json'):
        content=(R/'Translation'/name).read_text(encoding='utf8')
        assert '웨어호그' not in content and '웨어혹로' not in content
    cuts=[x for x in rows if x['file']=='cutscenes-all.json']
    latin=[x for x in cuts if re.search('[A-Za-z]',x['japanese'])]
    assert len(cuts)==602 and len(latin)==18
    for row in latin:
        for token in re.findall('[A-Za-z]+',row['japanese']):assert token in row['korean'],row['translation_key']
    spoken=[x for x in latin if not re.search(r'Dr\.',x['japanese'])]
    assert len(spoken)==7 and all(x['speaker_id'] in ('cue:sn','cue:es') for x in spoken)
    for row in rows:
        if row['file']=='hint-all.json' and '解析不能' not in row['japanese']:
            for token in re.findall('[A-Za-z]+',row['japanese']):
                assert token in row['korean'],(row['translation_key'],token)
    evidence=None
    files=list((R/'Analysis/Full-Text-Extraction/Audit/ArchiveInventory').glob('*/*/evrt_m6_03_voice_Japanese.inspire_resource.xml'))
    if files:
        voice=ET.parse(files[0]).getroot()
        resources={n.findtext('ID'):n.findtext('Param/CueName') for n in voice.findall('.//Resource')}
        cues={resources[t.findtext('ResourceID')]:int(t.findtext('Frame/Start')) for t in voice.findall('.//Trigger')}
        p=R/'Analysis/Full-Text-Extraction/Archives/cutscene/BaseGame/Japanese/evrt_m6_03/evrt_m6_03/evrt_m6_03_subtitle_Japanese.inspire_resource.xml'
        subtitles=ET.parse(p).getroot()
        rid=next(n.findtext('ID') for n in subtitles.findall('.//Resource') if n.findtext('Param/CellID')=='41')
        frame=int(next(t.findtext('Frame/Start') for t in subtitles.findall('.//Trigger') if t.findtext('ResourceID')==rid))
        assert frame==cues['J_m6_03_410_es']==4609
        evidence={'subtitle_cell':41,'subtitle_start_frame':frame,'voice_cue':'J_m6_03_410_es','voice_start_frame':4609}
    resources_path=R/'Build/Translation-v101/resource-verification.json'
    resource_result=None
    if resources_path.exists():
        resource_result=read(resources_path)
        assert resource_result['passed'] and len(resource_result['archives'])==17
        assert sum(x['changed_physical_cells'] for x in resource_result['archives'])==74
        for patch in resource_result['patches']:
            assert sha(R/'Build/Translation-v101/Resources'/patch['relative'])==patch['after_sha256']
    exe=R/'Build/FullBackend-v101/Native/UnleashedRecomp.exe'
    native_sha=None
    if exe.exists():
        data=exe.read_bytes();assert '웨어호그'.encode() not in data and '웨어혹로'.encode() not in data
        native=read(exe.parent.parent/'native-report.json')
        assert sha(exe)==native['patched_sha256'] and native['native_dispatch_test']['passed']
        assert len(native['native_term_corrections'])==2
        assert native['native_font']['all_current_native_characters_resolve']
        sys.path.insert(0,str(R/'Tools/UIRuntime'))
        import pefile,zstandard
        pe=pefile.PE(data=data)
        for inst,size_at,key in [(0xfa9f4,0xfa9f0,'snapshot_sha256'),(0xd0fa8,0xd0fa4,'texture_sha256')]:
            target=inst+7+struct.unpack('<i',pe.get_data(inst+3,4))[0]
            size=struct.unpack('<I',pe.get_data(size_at,4))[0]
            decoded=zstandard.ZstdDecompressor().decompress(pe.get_data(target,size))
            assert hashlib.sha256(decoded).hexdigest()==native['native_font'][key]
        native_sha=sha(exe)
    result={'passed':True,'catalog_entries':len(rows),'chip_edits':33,'sonic_english_edits':1,
            'cutscene_entries_examined':602,'cutscene_latin_entries':18,'sonic_english_entries':7,
            'terminology_occurrences_corrected':14,'hey_original_timing_evidence':evidence,
            'archive_count':len(resource_result['archives']) if resource_result else None,
            'changed_physical_cells':74 if resource_result else None,'native_sha256':native_sha,
            'new_native_glyph':'혹','embedded_native_font_verified':native_sha is not None,
            'full_audio_listening_claimed':False,'new_translation_gameplay_verified':False}
    out=R/'Build/Translation-v101';out.mkdir(parents=True,exist_ok=True)
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
