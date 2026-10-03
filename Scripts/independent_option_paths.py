"""Preserve intentionally empty HMM option directories in file-only packages."""
from pathlib import Path
import json,configparser,itertools
EMPTY_OPTIONS=('Compatibility/None','TitleLogos/Default')
def ensure_option_directories(root):
 root=Path(root)
 for rel in EMPTY_OPTIONS:
  p=root/rel/'README.txt';p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text('This option intentionally supplies no game resources.\nKeep this directory so Hedge Mod Manager can validate its include path.\n',encoding='utf8')
def verify_option_directories(root):
 root=Path(root);schema=json.loads((root/'ConfigSchema.json').read_text(encoding='utf-8-sig'));groups=[schema['Enums'][k] for k in ('WorldMapVariant','UnleasHDCompatibility','TitleLogoVariant')]
 for group in groups:
  for option in group:assert (root/option['Value']).is_dir(),option['Value']
 c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(root/'mod.ini',encoding='utf-8-sig');main=c['Main'];assert main['IncludeDirCount'].strip('"')=='4';assert main['IncludeDir2'].strip('"')=='.'
 for i in range(4):assert (root/main['IncludeDir'+str(i)].strip('"')).is_dir()
 for combo in itertools.product(*groups):assert all((root/o['Value']).is_dir() for o in combo)
 return {'optionCombinations':len(list(itertools.product(*groups))),'allPathsExist':True,'fixedRootSlot':2}
