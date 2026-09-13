from pathlib import Path
import struct,json
R=Path(__file__).resolve().parents[1];W=R/'Build/UITextureWork'
def parse(path):
 b=path.read_bytes();base=b.index(b'nCPJ');u=lambda a:struct.unpack_from('>I',b,a)[0];f=lambda a:struct.unpack_from('>f',b,a)[0]
 p=lambda a:base+u(a) if u(a) else 0
 def s(a):
  off=p(a);return b[off:b.index(0,off)].decode() if off else ''
 result=[]
 def node(off,prefix):
  count=u(off);table=p(off+4);ids=p(off+8)
  for i in range(count):
   name=s(ids+8*i);idx=u(ids+8*i+4);sc=p(table+4*idx);subs=p(sc+32);subcount=u(sc+28)
   subimgs=[struct.unpack_from('>I4f',b,subs+20*j) for j in range(subcount)]
   groups=p(sc+40);dic=p(sc+48)
   casts=[]
   for j in range(u(sc+44)):
    cn=s(dic+12*j);group=u(dic+12*j+4);index=u(dic+12*j+8);cast=p(p(groups+16*group+4)+4*index);mat=p(cast+64);si=u(mat) if mat else 0xffffffff
    casts.append({'name':cn,'offset':cast,'kind':u(cast+4),'material':mat,'sub_index':si,'subimage':subimgs[si] if si<subcount else None,'font_text':s(cast+68),'font':s(cast+72),'corners':struct.unpack_from('>8f',b,cast+12)})
   result.append({'name':prefix+'/'+name,'offset':sc,'subs':subs,'casts':casts})
  for i in range(u(off+12)):
   ids=p(off+20);idx=u(ids+i*8+4);node(p(off+16)+24*idx,prefix+'/'+s(ids+i*8))
 node(p(base+16),'')
 return result
if __name__=='__main__':
 for path in (W/'SceneProbe').rglob('*.yncp'):
  result=parse(path);(path.parent/(path.stem+'-parsed.json')).write_text(json.dumps(result,indent=2))
  for scene in result:
   for c in scene['casts']:
    if c['font_text'] or ('head' in c['name'] or 'title' in c['name']):print(scene['name'],c)
