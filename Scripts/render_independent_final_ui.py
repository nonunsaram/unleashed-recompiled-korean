"""Render the four approved vector UI tiles. No game or UnleasHD input images.
Requires Pillow and numpy. Writes PNG tiles for the approved 2x texture atlas.
"""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

def contours(path):
 import re
 ts=re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?',path);i=0;polys=[];p=[];pos=(0,0)
 while i<len(ts):
  cmd=ts[i];i+=1
  if cmd in ('M','L'):
   pos=tuple(map(float,ts[i:i+2]));i+=2;p.append(pos)
  elif cmd=='C':
   v=list(map(float,ts[i:i+6]));i+=6;p0=pos;p1=v[:2];p2=v[2:4];p3=v[4:6]
   for t in np.linspace(0,1,25)[1:]:p.append(tuple((1-t)**3*p0[k]+3*(1-t)**2*t*p1[k]+3*(1-t)*t*t*p2[k]+t**3*p3[k] for k in (0,1)))
   pos=tuple(p3)
  else:polys.append(p);p=[]
 return polys

def render_press():
    P='M0 16 L0 0 L8.2 0 C11 0 12 1.5 12 4.3 L12 5.3 C12 8 10.5 9.3 8.2 9.3 L2 9.3 L2 16 Z M2 2 L2 7.3 L8 7.3 C9.5 7.3 10 6.6 10 5 L10 4.3 C10 2.8 9.5 2 8 2 Z'
    RR='M0 16 L0 0 L8.2 0 C11 0 12 1.5 12 4.2 L12 5 C12 7.1 10.9 8.2 9.1 8.5 C10.6 8.8 11.3 9.6 11.6 11.1 L12.7 16 L10.5 16 L9.6 11.8 C9.2 10 8.5 9.1 6.4 9.1 L2 9.1 L2 16 Z M2 2 L2 7.2 L7.7 7.2 C9.4 7.2 10 6.6 10 4.7 C10 2.9 9.5 2 7.8 2 Z'
    E='M0 0 L11 0 L11 2 L2 2 L2 7 L10 7 L10 9 L2 9 L2 14 L11 14 L11 16 L0 16 Z'
    S='M12 4.8 L10 4.8 L10 3.9 C10 2.3 9 1.8 7.6 1.8 L4.5 1.8 C2.8 1.8 2 2.7 2 4.2 L2 5.1 C2 6.2 2.6 6.8 4.1 7 L8.1 7.5 C10.8 7.8 12 9 12 11.3 L12 12.1 C12 14.6 10.4 16 8 16 L4 16 C1.5 16 0 14.5 0 12 L0 11.1 L2 11.1 L2 12 C2 13.5 2.8 14.2 4.3 14.2 L7.8 14.2 C9.3 14.2 10 13.5 10 12 L10 11.5 C10 10.1 9.4 9.5 7.8 9.3 L3.8 8.8 C1.2 8.5 0 7.2 0 5 L0 4.1 C0 1.6 1.7 0 4.2 0 L7.9 0 C10.5 0 12 1.4 12 3.9 Z'
    T='M0 0 L13 0 L13 2 L7.5 2 L7.5 16 L5.5 16 L5.5 2 L0 2 Z'
    A='M0 16 L5.7 0 L8.1 0 L14 16 L11.7 16 L10.43 12.2 L3.49 12.2 L2.2 16 Z M4.1 10.3 L9.8 10.3 L6.9 2 Z'
    glyphs={'P':P,'R':RR,'E':E,'S':S,'T':T,'A':A}
    placements=list(zip('PRESSSTART',[56,70,85,98,112,133,147,159,174,188]))
    def contours(path):
     import re
     ts=re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?',path);i=0;polys=[];p=[];pos=(0,0)
     while i<len(ts):
      cmd=ts[i];i+=1
      if cmd in ('M','L'):
       pos=tuple(map(float,ts[i:i+2]));i+=2;p.append(pos)
      elif cmd=='C':
       v=list(map(float,ts[i:i+6]));i+=6;p0=pos;p1=v[:2];p2=v[2:4];p3=v[4:6]
       for t in np.linspace(0,1,25)[1:]:p.append(tuple((1-t)**3*p0[k]+3*(1-t)**2*t*p1[k]+3*(1-t)*t*t*p2[k]+t**3*p3[k] for k in (0,1)))
       pos=tuple(p3)
      else:polys.append(p);p=[]
     return polys
    scale=24;mask=Image.new('L',(256*scale,26*scale));d=ImageDraw.Draw(mask)
    for ch,x in placements:
     for n,poly in enumerate(contours(glyphs[ch])):d.polygon([((a+x)*scale,(b+2)*scale) for a,b in poly],fill=255 if n==0 else 0)
    # Approved final fill expansion: 0.75 source pixels.
    mask=mask.filter(ImageFilter.MaxFilter(19))
    # Narrow dark edge and subtle lower shadow, preserving original silver vertical shading.
    edge=mask.filter(ImageFilter.MaxFilter(25));shadow=Image.new('L',mask.size);shadow.paste(edge,(0,18));shadow=shadow.filter(ImageFilter.GaussianBlur(6)).point(lambda v:round(v*.6))
    layer=Image.new('RGBA',mask.size);layer.putalpha(shadow)
    border=Image.new('RGBA',mask.size,(24,25,26,255));border.putalpha(edge);layer=Image.alpha_composite(layer,border)
    y=np.arange(mask.height)/scale;lum=np.clip(255-(y-4)*7,155,255).astype('uint8');rgb=np.repeat(lum[:,None],mask.width,axis=1);arr=np.stack([rgb,rgb,rgb,np.array(mask)],axis=2);layer=Image.alpha_composite(layer,Image.fromarray(arr))
    layer=layer.resize((512,52),Image.Resampling.LANCZOS)

    return layer

def render_sega_new():
    ns={'E': 'M0 0 L11 0 L11 2 L2 2 L2 7 L10 7 L10 9 L2 9 L2 14 L11 14 L11 16 L0 16 Z', 'S': 'M12 4.8 L10 4.8 L10 3.9 C10 2.3 9 1.8 7.6 1.8 L4.5 1.8 C2.8 1.8 2 2.7 2 4.2 L2 5.1 C2 6.2 2.6 6.8 4.1 7 L8.1 7.5 C10.8 7.8 12 9 12 11.3 L12 12.1 C12 14.6 10.4 16 8 16 L4 16 C1.5 16 0 14.5 0 12 L0 11.1 L2 11.1 L2 12 C2 13.5 2.8 14.2 4.3 14.2 L7.8 14.2 C9.3 14.2 10 13.5 10 12 L10 11.5 C10 10.1 9.4 9.5 7.8 9.3 L3.8 8.8 C1.2 8.5 0 7.2 0 5 L0 4.1 C0 1.6 1.7 0 4.2 0 L7.9 0 C10.5 0 12 1.4 12 3.9 Z', 'A': 'M0 16 L5.7 0 L8.1 0 L14 16 L11.7 16 L10.43 12.2 L3.49 12.2 L2.2 16 Z M4.1 10.3 L9.8 10.3 L6.9 2 Z'}
    ns['contours']=contours
    G='M13 5 L11 5 C10.7 2.8 9.5 2 6.6 2 C3.4 2 2 3.4 2 6 L2 10.8 C2 13.4 3.5 14.8 6.6 14.8 C9.8 14.8 11 13.7 11 11.7 L11 9.4 L6.5 9.4 L6.5 7.4 L13 7.4 L13 11.7 C13 15.1 10.8 16.8 6.6 16.8 C2.2 16.8 0 14.9 0 11 L0 5.8 C0 1.9 2.2 0 6.6 0 C10.9 0 12.9 1.8 13 5 Z'
    N='M0 16 L0 0 L3 0 L9 10.5 L9 0 L12 0 L12 16 L9 16 L3 5.5 L3 16 Z'
    E='M0 0 L11 0 L11 3 L3 3 L3 6.5 L10 6.5 L10 9.5 L3 9.5 L3 13 L11 13 L11 16 L0 16 Z'
    WW='M0 0 L3 0 L5 11 L7.3 0 L10 0 L12.3 11 L14.3 0 L17.3 0 L14 16 L11 16 L8.65 5.8 L6.3 16 L3.3 16 Z'
    EX='M0 0 L3.8 0 L3.1 11.2 L0.7 11.2 Z M0.1 13 L3.7 13 L3.7 16 L0.1 16 Z'
    # Subpaths of ! are both filled; other glyphs here have no counters.
    def render(size,placements,kind):
     sc=16;mask=Image.new('L',(size[0]*sc,size[1]*sc));d=ImageDraw.Draw(mask)
     for path,x,y,sx,sy in placements:
      for poly in ns['contours'](path):d.polygon([((a*sx+x)*sc,(b*sy+y)*sc) for a,b in poly],fill=255)
     if kind=='silver':
      mask=mask.filter(ImageFilter.MaxFilter(9));edge=mask.filter(ImageFilter.MaxFilter(17));layer=Image.new('RGBA',mask.size,(24,25,26,255));layer.putalpha(edge);ys=np.arange(mask.height)/sc;val=np.clip(255-(ys-4)*7,155,255).astype('uint8');arr=np.repeat(val[:,None],mask.width,1);rgb=np.stack([arr,arr,arr],2)
     else:
      edge=mask.filter(ImageFilter.MaxFilter(39));layer=Image.new('RGBA',mask.size,(123,8,0,255));layer.putalpha(edge);ys=np.arange(mask.height)/sc;t=np.clip((ys-3)/16,0,1);vals=np.array([np.full(len(t),255),181+55*t,106-20*t],dtype='uint8').T;rgb=np.repeat(vals[:,None,:],mask.width,1)
     arr=np.dstack([rgb,np.array(mask)]);layer=Image.alpha_composite(layer,Image.fromarray(arr));return layer.resize((size[0]*2,size[1]*2),Image.Resampling.LANCZOS)
    # A has one counter; build its negative space after supersampled filled contours via a special path renderer.
    original_contours=ns['contours']
    def render_sega():
     sc=16;size=(65,22);mask=Image.new('L',(size[0]*sc,size[1]*sc));d=ImageDraw.Draw(mask)
     paths=[(ns['S'],5),(ns['E'],19),(G,31.5),(ns['A'],45.5)]
     for path,x in paths:
      for i,poly in enumerate(original_contours(path)):d.polygon([((a+x)*sc,(b+3)*sc) for a,b in poly],fill=255 if i==0 else 0)
     mask=mask.filter(ImageFilter.MaxFilter(9));edge=mask.filter(ImageFilter.MaxFilter(17));layer=Image.new('RGBA',mask.size,(24,25,26,255));layer.putalpha(edge);ys=np.arange(mask.height)/sc;v=np.clip(255-(ys-5)*7,155,255).astype('uint8');a=np.repeat(v[:,None],mask.width,1);layer=Image.alpha_composite(layer,Image.fromarray(np.stack([a,a,a,np.array(mask)],2)));return layer.resize((130,44),Image.Resampling.LANCZOS),[(p,x,3,1,1) for p,x in paths]
    sega,sp=render_sega();npth=[(N,3,3,0.92,0.94),(E,15,3,0.85,0.94),(WW,25.5,3,0.93,0.94),(EX,44,3,1,0.94)];new=render((53,24),npth,'gold')

    return sega,new

def render_copyright():
    ns={'contours':contours}
    C='M16.8 11.4 L15.3 11.4 C15.2 9.8 14.4 9.1 12.5 9.1 C10.4 9.1 9.5 10.3 9.5 12.3 L9.5 15.7 C9.5 17.7 10.4 18.9 12.5 18.9 C14.4 18.9 15.2 18.2 15.3 16.6 L16.8 16.6 C16.7 19.1 15.2 20.4 12.5 20.4 C9.4 20.4 8 18.6 8 15.7 L8 12.3 C8 9.4 9.4 7.6 12.5 7.6 C15.2 7.6 16.7 8.9 16.8 11.4 Z'
    sc=20;mask=Image.new('L',(24*sc,24*sc));d=ImageDraw.Draw(mask)
    d.ellipse(tuple(v*sc for v in (3.8,12.75+(5.3-14)*0.95,21.2,12.75+(22.7-14)*0.95)),fill=255);d.ellipse(tuple(v*sc for v in (5.1,12.75+(6.6-14)*0.95,19.9,12.75+(21.4-14)*0.95)),fill=0)
    cm=Image.new('L',mask.size);cd=ImageDraw.Draw(cm)
    for poly in ns['contours'](C):cd.polygon([(x*sc,(12.75+(y-14)*0.85*0.95)*sc) for x,y in poly],fill=255)
    mask=Image.fromarray(np.maximum(np.array(mask),np.array(cm.filter(ImageFilter.MaxFilter(9)))))
    edge=mask.filter(ImageFilter.MaxFilter(17));layer=Image.new('RGBA',mask.size,(24,25,26,255));layer.putalpha(edge);v=np.clip(255-(np.arange(mask.height)/sc-7)*7,155,255).astype('uint8');arr=np.repeat(v[:,None],mask.width,1);layer=Image.alpha_composite(layer,Image.fromarray(np.stack([arr,arr,arr,np.array(mask)],2)));tile=layer.resize((48,48),Image.Resampling.LANCZOS)
    return tile

def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    sega,new=render_sega_new()
    for name,im in [('press-start',render_press()),('sega',sega),('new',new),('copyright',render_copyright())]:im.save(output/(name+'.png'))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
