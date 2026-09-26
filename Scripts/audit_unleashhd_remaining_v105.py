"""Inventory overlapping DDS still intentionally served by the Korean patch."""
from __future__ import annotations
import json
from pathlib import Path
from build_unleashhd_ui_compat_v105 import members

ROOT=Path(__file__).resolve().parents[1]
KOREAN=ROOT/'Build/Development-v104-Final/UnleashedKorean/Languages/English'
HD=ROOT/'UnleashedRecomp-Windows/mods/UnleasHD-1440p/MainMod/Languages/English'
OVERLAY=ROOT/'Build/UnleasHD-Compatibility-v105-HUD2/verification.json'
OUT=ROOT/'Translation/review/unleashhd-v105/residual-conflicts.json'

def main():
    handled={(r['archive'],r['file']) for r in json.loads(OVERLAY.read_text(encoding='utf8'))['textures']}
    remaining=[]
    for korean_arl in KOREAN.glob('*.arl'):
        hd_arl=HD/korean_arl.name
        if not hd_arl.is_file(): continue
        stem=korean_arl.stem.lstrip('+')
        for file in sorted(members(korean_arl)&members(hd_arl)):
            if not file.lower().endswith('.dds') or (stem,file) in handled: continue
            kind=('korean-font-atlas' if file.startswith('fte_ConverseMain_') else
                  'translated-tails-event' if stem=='ExStageTails_Common' and file.startswith('evex_ex') else 'unclassified')
            assert kind!='unclassified',(stem,file)
            remaining.append({'archive':stem,'file':file,'kind':kind,
                              'decision':'retain Korean asset; its text must remain translated'})
    counts={kind:sum(r['kind']==kind for r in remaining) for kind in sorted({r['kind'] for r in remaining})}
    assert len(remaining)==17 and counts=={'korean-font-atlas':15,'translated-tails-event':2},counts
    report={'passed':True,'handledHdUiTextures':len(handled),'remainingKoreanDdsOverlaps':len(remaining),
            'counts':counts,'fullConflictFree':False,'entries':remaining}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},ensure_ascii=False))
if __name__=='__main__': main()
