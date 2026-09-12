"""Shared typography and original-English preservation for UI atlas rows."""
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
import json,hashlib,shutil
import numpy as np

def render(R,W,source,labels,layout_scale=1,selected_indices=None):
    W.mkdir(parents=True,exist_ok=True)
    decisions=json.loads((R/'Translation/review/remaining-ui/texture-decisions.json').read_text(encoding='utf8'))
    if selected_indices is not None:
        selected_indices=set(selected_indices)
        labels=[v for v in labels if v['texture'] in selected_indices]
    labels=[v for v in labels if v['texture']!=15 and decisions[v['texture']]['decision']!='keep_english']
    labels=[v for v in labels if not ((v['texture']==17 and v['box'][1] in (210,240)) or (v['texture']==21 and v['korean']!='종료') or (v['texture']==23 and v['box'][1]==0) or (v['texture']==26 and v['korean']=='신상품!'))]
    paths={'regular':'LINESeedKR-Rg.ttf','bold':'SBAggroM.ttf','slant':'SBAggroB.ttf'}
    colors={'white':((255,255,255),(225,229,233),(8,8,8)), 'gold':((255,255,255),(242,207,101),(99,73,16))}
    for v in labels:
        i=v['texture'];x0,y0,x1,y1=v['box'];v.update(size=22,align='left',anchor_x=x0+3,top=y0+3,group=str(i),font='regular',style='white')
        if i in (0,32):v.update(size=24,font='slant' if i==0 else 'bold',group='stage_names',top=y0+3)
        elif i in (10,11):v.update(size=19,group='loading_controls',anchor_x=48 if i==10 and y0>=235 else 3,top=y0+2)
        elif i==15:v.update(size=13,font='bold',top=1)
        elif i==16:v.update(size=24,align='center',anchor_x=135,top=y0+4)
        elif i in (17,18):
            v.update(size=22,group='common_buttons',anchor_x=3,top=y0+7.75)
            if i==17 and y0==150:v.update(align='center',anchor_x=64)
        elif i in (19,25):
            if y0<64:v.update(size=24,font='slant',group='pause_heading',top=y0+3)
            else:v.update(size=20,font='bold',group='pause_conditions',align='center',anchor_x=192,top=y0+5)
        elif i==21:v.update(size=23,font='slant',top=y0+3)
        elif i==23:
            v.update(size=19,align='center',anchor_x=128 if y0 in (78,206,258,336,362,388,414) else (64 if x0<128 else 192),top=y0+3)
        elif i==24:v.update(size=20,align='center',anchor_x=64,top=y0+3)
        elif i==26:v.update(size=26,font='bold',top=y0+2.5)
        elif i in (28,29):v.update(size=34,font='bold',group='media',style='gold',align='left' if i==28 else 'center',anchor_x=3 if i==28 else 256,top=y0+4)
        elif i==31:v.update(size=25,font='bold',align='right',anchor_x=252,top=y0+3)
        v['layout_box']=[x0+1,y0+1,x1-1,y1-1]
        if i==16:v['layout_box']=[25,y0+1,245,y0+31]
        if i in (17,18):v['layout_box']=[1,y0+1,126 if i==17 else 159,y0+29]
    if layout_scale != 1:
        for v in labels:
            v['box']=[round(x*layout_scale) for x in v['box']]
            v['layout_box']=[round(x*layout_scale) for x in v['layout_box']]
            v['size']=round(v['size']*layout_scale)
            v['anchor_x']*=layout_scale
            v['top']*=layout_scale
    scale=4
    for group in {v['group'] for v in labels}:
        members=[v for v in labels if v['group']==group];size=min(v['size'] for v in members)
        while any(ImageFont.truetype(str(R/'Tools/Fonts'/paths[v['font']]),size*scale).getlength(v['korean'])/scale+6>v['layout_box'][2]-v['layout_box'][0] for v in members):
            size-=1;assert size>=10
        for v in members:v['size']=size
    for v in labels:
        if v['texture'] in (10,11):
            # Loading's actual UV rows are 26px, with two rows for X/A/stick
            # explanations. Main face-button labels share one screen-space
            # left edge; shoulder/stick labels retain the original ink center.
            i=v['texture'];n=v['box'][1]//26
            f=ImageFont.truetype(str(R/'Tools/Fonts'/paths[v['font']]),v['size']*scale)
            bb=f.getbbox(v['korean'],anchor='ls');ref=f.getbbox('가나다',anchor='ls')
            v['top']=n*26+13+ref[1]/scale-(bb[1]+bb[3])/(2*scale)
            # Cast left positions in the original 1280x720 loading scene.
            right={3:541,4:540,5:540,6:539,7:538,8:538} if i==10 else {1:540,2:539,3:540,4:540,5:540,6:539}
            width=96 if (i==10 and n>=9) or (i==11 and n in (8,9)) else 240
            v['layout_box']=[1,n*26+1,width-1,(n+1)*26-1]
            if n in right:
                mask_bounds=f.getmask(v['korean']).getbbox()
                v['align']='left';v['anchor_x']=544-right[n]-(bb[0]+mask_bounds[0])/scale
            else:
                original=np.array(Image.open(source[i]['english']).convert('RGBA'))[n*26:(n+1)*26,:width]
                yy,xx=np.where((original[:,:,3]>127)&(original[:,:,:3].mean(axis=2)>150))
                assert len(xx)
                center=(int(xx.min())+int(xx.max())+1)/2
                if i==10 and n>=9:center=70.5
                if i==11 and n in (8,9):center=26.5
                # Use the ink center, not the font advance, for short labels.
                v['align']='left';v['anchor_x']=center-(bb[0]+bb[2])/(2*scale)
            v['group']='loading_controls'
        if v['texture']==23:
            f=ImageFont.truetype(str(R/'Tools/Fonts'/paths[v['font']]),v['size']*scale)
            bb=f.getbbox('가나다',anchor='ls');ink=(bb[3]-bb[1])/scale
            v['top']=v['box'][1]+14-ink/2
            # Title CSD uses y=182..206 and 390..414, not the original guessed rows.
            if v['korean']=='이어하기':v['top']=194-ink/2
            if v['korean']=='새 게임':v['top']=402-ink/2
            v['top']-=2 # 0.4.3: playtest optical correction above the UV midpoint.
            if v['korean']=='옵션':v['top']-=1 # 0.4.12: requested one-pixel title-menu correction.
    (R/'Translation/ui-textures-ko.json').write_text(json.dumps({'version':'0.4.12','policy':'Common English preserved; fixed font sizes and alignment per family','labels':labels},ensure_ascii=False,indent=2),encoding='utf8')
    panel_source=Image.open(source[19]['english']).convert('RGBA')
    report=[]
    for i,row in enumerate(source):
        if selected_indices is not None and i not in selected_indices:continue
        original=Image.open(row['english']).convert('RGBA');out=original.copy();changed=[];metrics=[]
        for v in [v for v in labels if v['texture']==i]:
            box=tuple(v['box']);x0,y0,x1,y1=box
            if v['background']:
                if i==16:
                    clear=(90,y0+2,200,y0+29)
                    for py in range(clear[1],clear[3]):
                        for px in range(clear[0],clear[2]):out.putpixel((px,py),original.getpixel((70,py)))
                else:
                    clear=(130,y0+3,254,min(y0+28,y1))
                    for py in range(clear[1],clear[3]):
                        for px in range(clear[0],clear[2]):out.putpixel((px,py),panel_source.getpixel((px if px<150 or px>237 else 140,98+py-y0)))
            else:clear=box;out.paste((0,0,0,0),clear)
            changed.append(clear)
            font=ImageFont.truetype(str(R/'Tools/Fonts'/paths[v['font']]),v['size']*scale)
            reference=font.getbbox('가나다',anchor='ls');baseline=round(v['top']*scale-reference[1])
            advance=font.getlength(v['korean']);ax=v['anchor_x']*scale
            textx=ax if v['align']=='left' else ax-advance/2 if v['align']=='center' else ax-advance
            layer=Image.new('RGBA',(original.width*scale,(y1-y0)*scale));face=Image.new('L',layer.size)
            ImageDraw.Draw(face).text((round(textx),baseline-y0*scale),v['korean'],font=font,anchor='ls',fill=255)
            stroke=face.filter(ImageFilter.MaxFilter(9 if v['font']=='regular' else 11));top,bottom,edge=colors[v['style']]
            layer.paste((*edge,255),(0,0,layer.width,layer.height));layer.putalpha(stroke)
            gradient=np.zeros((layer.height,layer.width,4),dtype='uint8')
            for py in range(layer.height):
                t=min(1,max(0,(py-(v['top']-y0)*scale)/(v['size']*scale)))
                if v['style']=='gold':t=min(1,max(0,(t-.35)/.65))
                gradient[py,:,:3]=np.array(top)*(1-t)+np.array(bottom)*t
            gradient[:,:,3]=np.array(face);layer.alpha_composite(Image.fromarray(gradient))
            if v['font']=='slant':layer=layer.transform(layer.size,Image.Transform.AFFINE,(1,.12,-(v['size']+v['top']-y0)*scale*.12,0,1,0),resample=Image.Resampling.BICUBIC)
            layer=layer.resize((original.width,y1-y0),Image.Resampling.LANCZOS);bb=layer.getbbox();assert bb
            out.alpha_composite(layer,(0,y0));changed.append((bb[0],y0+bb[1],bb[2],y0+bb[3]))
            metrics.append({'text':v['korean'],'font':v['font'],'size':v['size'],'align':v['align'],'anchor_x':v['anchor_x'],'baseline':baseline/scale,'row_top':y0})
        folder=W/f'{i:03}';folder.mkdir(exist_ok=True)
        if metrics:out.save(folder/row['file'])
        else:shutil.copy2(row['english'],folder/row['file'])
        out.save(folder/'korean.png');allowed=np.zeros((out.height,out.width),dtype=bool)
        for xx0,yy0,xx1,yy1 in changed:allowed[yy0:yy1,xx0:xx1]=True
        assert np.array_equal(np.array(original)[~allowed],np.array(out)[~allowed])
        reopened=Image.open(folder/row['file']).convert('RGBA');assert np.array_equal(np.array(reopened),np.array(out))
        bg=Image.new('RGBA',(out.width*2,out.height),(45,50,60,255));bg.alpha_composite(original);bg.alpha_composite(out,(out.width,0));bg.convert('RGB').save(folder/'comparison.png')
        report.append({'texture':i,'file':row['file'],'labels':len(metrics),'size':out.size,'archives':row['archives'],'metrics':metrics,'source_sha256':hashlib.sha256(Path(row['english']).read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256((folder/row['file']).read_bytes()).hexdigest(),'original_file_preserved':not bool(metrics)})
    (W/'texture-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'textures':len(report),'translated_textures':sum(bool(r['labels']) for r in report),'labels':len(labels),'pixel_and_dds_roundtrip_verified':True}),flush=True)
