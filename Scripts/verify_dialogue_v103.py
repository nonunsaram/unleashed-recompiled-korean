"""Check the complete catalog delta, layout, placeholders, and built archive manifests."""
from audit_dialogue_v103 import *
import hashlib,shutil,html
W=R/'Build/Translation-v103'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 edits=read(OUT/'edits.json');emap={r['translation_key']:r for r in edits}
 rows=[];before=[];diff=[];layout=[];variants=collections.defaultdict(list)
 for p in sorted((R/'Translation').glob('*-all.json')):
  old=read(W/'source-before'/p.name);new=read(p)
  assert len(old['items'])==len(new['items'])
  for a,b in zip(old['items'],new['items']):
   key=a['translation_key'];assert key==b['translation_key']
   for field in a:
    if field not in ('korean','review_note'):assert a[field]==b[field],(key,field)
   assert re.findall(r'\{GLYPH:\d+\}',a['korean'])==re.findall(r'\{GLYPH:\d+\}',b['korean'])
   if a['korean']!=b['korean']:
    assert key in emap and emap[key]['before']==a['korean'] and emap[key]['after']==b['korean']
    if emap[key]['reason'].startswith('FTE-width'):assert re.sub(r'\s','',a['korean'])==re.sub(r'\s','',b['korean'])
    diff.append(key)
   else:assert key not in emap
   row={'file':p.name,**b};rows.append(row)
   pr=profile(row)
   if pr:
    kind,limit,n=pr;ws=[width(t) for t in b['korean'].split('\n')]
    assert len(ws)<=n and max(ws,default=0)<=limit,(key,ws)
    layout.append({'key':key,'kind':kind,'widths':ws})
   if p.name in ('town-dialogue-all.json','hint-all.json','stage-ui-all.json'):
    variants[(p.name,b.get('speaker_id',''),re.sub(r'\s','',b['japanese']))].append(row)
 assert len(rows)==11912 and len({r['translation_key'] for r in rows})==11912
 assert set(diff)==set(emap)
 strength=[r for r in rows if r['file']=='skill-ui-all.json' and r['english']=='Strength\nleveled up!']
 assert len(strength)==2 and all(r['korean']=='STRENGTH가\n레벨 업했다!' for r in strength)
 manifest=read(W/'resource-verification.json');assert manifest['passed']
 for patch in manifest['patches']:
  assert sha(W/'Resources'/patch['relative'])==patch['after_sha256']
  assert sha(R/'Build/Development-v102/UnleashedKorean'/patch['relative'])==patch['before_sha256']
 for g in manifest['archives']:assert g['roundtrip_verified']
 raw=read(W/'resource-input.json');physical=[r for g in raw for r in g['rows']]
 assert len(physical)==sum(g['changed_physical_cells'] for g in manifest['archives'])
 assert len({r['line_id'] for r in physical})==len(physical)
 variant_review=[]
 for group in variants.values():
  if len({re.sub(r'\s','',r['korean']) for r in group})<2:continue
  reason=('Existing documented correction: detailed mission goal and English require 250 rings' if any(r['translation_key']=='652b01c0e39c7ff479ed1064' for r in group) else 'Context-specific person/shop distinction, or equivalent wording/punctuation; retained after comparison')
  variant_review.append({'japanese':group[0]['japanese'],'rows':[{k:r[k] for k in ('translation_key','representative_line_id','english','korean','review_note')} for r in group],'decision':reason})
 write(OUT/'duplicate-source-review.json',variant_review)
 result={'passed':True,'catalog_entries':len(rows),'unique_keys':len(rows),'changed_entries':len(edits),'layout_only_entries':sum(e['reason'].startswith('FTE-width') for e in edits),'semantic_or_terminology_entries':sum(not e['reason'].startswith('FTE-width') for e in edits),'dialogue_entries_checked':len(layout),'hotdog_entries_source_compared':len(read(OUT/'hotdog-review.json')),'remaining_profile_overflow':0,'unchanged_sources_and_status':True,'control_tokens_preserved':True,'unaffected_entries_preserved':True,'archive_count':len(manifest['archives']),'physical_cells':len(physical),'strength_physical_cells':sum(r['translation_key'] in {x['translation_key'] for x in strength} for r in physical),'duplicate_source_groups_compared':len(variant_review),'gameplay_verified':False,'automated_scope_note':'All catalog structure checked; dialogue width profiles only; full semantic comparison for hotdog plus flagged dialogue and duplicate-source groups, not a claim of manual retranslation of all 11912 entries.'}
 write(OUT/'verification.json',result)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()