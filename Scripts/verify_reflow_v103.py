"""Verify the author's requested sentence-flow revision against the previous deliverable."""
from audit_dialogue_v103 import *
def main():
 old=read(OUT/'first-pass-edits.json'); oldmap={r['translation_key']:r for r in old}
 overrides=read(OUT/'reflow-overrides.json'); revised=overrides['items']
 current={r['translation_key']:r for p in (R/'Translation').glob('*-all.json') for r in read(p)['items']}
 changes=[];shortenings=[]
 for key,a in oldmap.items():
  b=current[key];approved=revised[key]
  assert a['after']==approved['before'] and b['korean']==approved['after'],key
  assert b['japanese']==a['japanese'] and b['english']==a['english'] and b['status']==a['status']
  assert re.findall(r'\{GLYPH:\d+\}',a['after'])==re.findall(r'\{GLYPH:\d+\}',b['korean'])
  if a['after']!=b['korean']:
   lexical=re.sub(r'\s','',a['after'])!=re.sub(r'\s','',b['korean'])
   assert lexical==approved['text_changed']
   e={'key':key,'file':a['file'],'profile':a['profile'],'line':a['representative_line_id'],'japanese':a['japanese'],'english':a['english'],'previous':a['after'],'revised':b['korean'],'text_changed':lexical,'review_index':approved['review_index']}
   changes.append(e)
   if lexical:shortenings.append(e)
 assert len(shortenings)==2
 exact='저 상자 같은 걸 녀석들이 분홍색 장소로\n가져가면 파워 업해 버리는 모양이야!'
 matches=[r for r in current.values() if re.sub(r'\s','',r['korean'])==re.sub(r'\s','',exact)]
 assert len(matches)==2 and all(r['korean']==exact for r in matches)
 # A hard source newline must no longer create a stranded continuation line.
 for source in (exact.replace('\n',' '),exact.replace('가져가면 ','가져가면\n')):
  proposed=wrap(source,600,3)
  assert proposed and len(proposed.split('\n'))==2 and all(line!='가져가면' for line in proposed.split('\n'))
  assert re.sub(r'\s','',proposed)==re.sub(r'\s','',source)
 for g in overrides['groups']:
  if not g['text_changed']:assert re.sub(r'\s','',g['before'])==re.sub(r'\s','',g['after'])
 assert len(overrides['groups'])==245 and len(revised)==381
 result={'passed':True,'reviewed_previous_entries':len(old),'reviewed_unique_sentences':len(overrides['groups']),'revised_unique_sentences':sum(g['before']!=g['after'] for g in overrides['groups']),'changed_entries':len(changes),'line_break_only_entries':len(changes)-len(shortenings),'shortened_entries':len(shortenings),'user_example_exact_matches':len(matches),'unchanged_terminology_and_tokens':True,'hard_newline_regression_passed':True,'gameplay_verified':False}
 write(OUT/'reflow-changes.json',changes);write(OUT/'reflow-verification.json',result)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()