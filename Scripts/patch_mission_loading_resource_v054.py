from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
P=R/'Build/Korean Full UI Playtest/Native/patched/default.xex'
data=bytearray(P.read_bytes());off=0x4000+0x24e5c0;name=b'StageLoad_list\0'
assert data[off:off+len(name)] in (bytes(len(name)),name)
data[off:off+len(name)]=name;P.write_bytes(data)
p=R/'Build/NativeUIWork/resources-report.json';report=json.loads(p.read_text())
report['patched_xex_sha256']=hashlib.sha256(data).hexdigest()
report['mission_loading_resource']={'name':name[:-1].decode(),'address':0x8224e5c0,'file_offset':off,'storage':'zero padding at the end of the original read-only data section'}
p.write_text(json.dumps(report,indent=2));print('Loading resource name installed in XEX read-only padding')
