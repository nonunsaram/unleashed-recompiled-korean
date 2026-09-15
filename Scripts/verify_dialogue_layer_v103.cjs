const fs=require('fs'),path=require('path');
const {apply,read,root}=require('./astra_review_common.cjs');
const display=read('Translation/display-overrides-v042.json').items;
const files=fs.readdirSync(path.join(root,'Translation')).filter(f=>f.endsWith('-all.json'));
let count=0;
for(const file of files){
 const expected=read('Translation/'+file).items;
 const current=structuredClone(expected);apply(current);
 if(current.some((r,i)=>r.korean!==expected[i].korean||r.review_note!==expected[i].review_note))throw Error('Current review is not idempotent: '+file);
 const regenerated=read('Build/Translation-v103/source-before/'+file).items;
 for(const row of regenerated){const d=display[row.translation_key];if(d)row.korean=d.korean;}
 apply(regenerated);
 if(regenerated.some((r,i)=>r.korean!==expected[i].korean||r.review_note!==expected[i].review_note))throw Error('Historical display overrides replaced latest review: '+file);
 count+=current.length;
}
const result={passed:true,catalog_entries:count,current_layer_idempotent:true,historical_layers_preserve_v103:true};
fs.writeFileSync(path.join(root,'Translation/review/v103/layer-verification.json'),JSON.stringify(result,null,2)+'\n');
console.log(result);