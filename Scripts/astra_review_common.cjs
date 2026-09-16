const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8').replace(/^\uFEFF/,''));
const fixes=read('Translation/review/astra-final/fixes.json');
const latestFile='Translation/review/v101/character-edits.json';
const latest=fs.existsSync(path.join(root,latestFile))?new Map(read(latestFile).map(x=>[x.translation_key,x])):new Map();
const dialogueFile='Translation/review/v103/edits.json';
const dialogue=fs.existsSync(path.join(root,dialogueFile))?read(dialogueFile):[];
function apply(items){
 const map=new Map(items.map(x=>[x.translation_key,x]));
 // Re-enter historical guards at the pre-v1.0.3 value, then apply the newest review last.
 for(const edit of dialogue){
  const row=map.get(edit.translation_key);if(!row)continue;
  if(row.korean===edit.after)row.korean=edit.before;
  const note=(edit.review_note+' [2026-09-16] '+edit.reason).trim();
  if(row.review_note===note)row.review_note=edit.review_note;
 }
 for(const fix of fixes){
  const row=map.get(fix.translation_key);if(!row)continue;
  for(const field of ['japanese','english','representative_line_id'])if(row[field]!==fix[field])throw Error('Astra source mismatch: '+fix.translation_key+' '+field);
  if(row.korean!==fix.before&&row.korean!==fix.after&&row.korean!==latest.get(fix.translation_key)?.after)throw Error('Astra translation changed: '+fix.translation_key);
  if(row.korean!==latest.get(fix.translation_key)?.after)row.korean=fix.after;
 }
 require('./source_status_common_v048.cjs').apply(items);
 for(const [key,edit] of latest){
  const row=map.get(key);if(!row)continue;
  if(row.korean!==edit.before&&row.korean!==edit.after)throw Error('v1.0.1 translation changed: '+key);
  row.korean=edit.after;
  if(key==='261837789180fc0cbc6e7687'){
   row.speaker_id='cue:es';row.speaker_evidence='Japanese subtitle/audio trigger frame 4609, J_m6_03_410_es';
  }
 }
 for(const edit of dialogue){
  const row=map.get(edit.translation_key);if(!row)continue;
  for(const field of ['japanese','english','representative_line_id'])if(row[field]!==edit[field])throw Error('v1.0.3 source mismatch: '+edit.translation_key);
  if(row.korean!==edit.before&&row.korean!==edit.after)throw Error('v1.0.3 translation changed: '+edit.translation_key);
  if(row.review_note!==edit.review_note)throw Error('v1.0.3 review note changed: '+edit.translation_key);
  row.korean=edit.after;
  row.review_note=(edit.review_note+' [2026-09-16] '+edit.reason).trim();
 }
}
module.exports={apply,fixes,read,root};
