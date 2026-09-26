"""Convert opening overlays to the game's original legacy DXT5 DDS format."""

from pathlib import Path
import hashlib
import json
import shutil
import subprocess

from PIL import Image


ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Build/OPLogoInvestigation'
TEXCONV=WORK/'Tools/texconv.exe'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert TEXCONV.is_file()
    report=json.loads((WORK/'build-report.json').read_text(encoding='utf8'))
    for variant in ('Korean','Custom'):
        source=WORK/'Variants'/variant/'Loading/OPmovie_titlelogo_EN.dds'
        assert Image.open(source).size==(1280,720)
        assert source.read_bytes()[84:88]!=b'DXT5', 'Already compressed; rebuild first'
        stage=WORK/'Compressed'/variant
        stage.mkdir(parents=True,exist_ok=True)
        if variant == 'Custom':
            from rebuild_world_opening_original import main as rebuild_world
            rebuild_world()
            compressed=WORK/'OriginalBased/OPmovie_titlelogo_KR_World.dds'
        else:
            subprocess.run([str(TEXCONV),'-nologo','-f','BC3_UNORM','-m','1','-y',
                            '-o',str(stage),str(source)],check=True)
            compressed=stage/source.name
        data=compressed.read_bytes()
        assert len(data)==921728 and data[:4]==b'DDS ' and data[84:88]==b'DXT5'
        assert Image.open(compressed).size==(1280,720)
        for language in ('EN','JP'):
            target=source.with_name(f'OPmovie_titlelogo_{language}.dds')
            shutil.copy2(compressed,target)
            report[variant][f'{language}sha256']=digest(target)
        assert source.read_bytes()==source.with_name('OPmovie_titlelogo_JP.dds').read_bytes()
        report[variant]['ddsFormat']='BC3_UNORM; DXT5; one mip; 1280x720'
        report[variant]['decodedDdsRoundTrip']=True
    (WORK/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
