const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const decisions=JSON.parse(fs.readFileSync(path.join(root,'Translation/review/source-status-v048/decisions.json'),'utf8'));
function apply(items){
 const map=new Map(items.map(x=>[x.translation_key,x]));
 for(const d of decisions){
  const r=map.get(d.translation_key);if(!r)continue;
  for(const k of ['japanese','english','representative_line_id'])if(r[k]!==d[k])throw Error('Source status source mismatch: '+d.translation_key);
  if(![d.before_status,d.status].includes(r.status))throw Error('Source status future edit: '+d.translation_key);
  if(![d.before_review_note,d.review_note].includes(r.review_note))throw Error('Source note future edit: '+d.translation_key);
  r.status=d.status;r.review_note=d.review_note;r.source_review=d.source_review;
 }
}
module.exports={apply,decisions};
