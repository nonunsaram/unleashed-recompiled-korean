"""Prepare the review4 playtest without shadowing UnleasHD's gauge choice."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from bounded_archive_tool import unpack

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
NEXT = ROOT / 'Build/Development-v105d-Playtest/UnleashedKorean'
WORK = ROOT / 'Build/Review4-RingEnergy/Pack/+Sonic'
INSPECTED = ROOT / 'Build/Review4-RingEnergy/ArchiveInspection/korean-base/+Sonic'
GAME = ROOT / 'Analysis/Full-Text-Extraction/Archives/base-common/BaseGame/English/Sonic/Sonic/mat_playscreen_en_003.dds'
TARGET = 'mat_playscreen_en_003.dds'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert PREVIOUS.is_dir() and INSPECTED.is_dir() and GAME.is_file()
    assert not NEXT.exists() and not WORK.parent.exists()
    assert sha(INSPECTED / TARGET) == sha(GAME), 'The Korean copy must exactly match the base game'
    old_members = {p.name: sha(p) for p in INSPECTED.iterdir() if p.is_file()}
    assert set(old_members) == {TARGET, 'mat_playscreen_en_001.dds', 'mat_playscreen_en_002.dds', 'mat_qte_en_001.dds'}
    shutil.copytree(PREVIOUS, NEXT)
    shutil.copytree(INSPECTED, WORK)
    (WORK / TARGET).unlink()
    packer = ROOT / 'Tools/HedgeArcPack/HedgeArcPack.exe'
    subprocess.run([str(packer), str(WORK)], input='hh\n', text=True,
                   capture_output=True, check=True, timeout=30)
    packed = WORK.parent
    source = NEXT / 'Languages/English'
    for ext in ('.arl', '.ar.00'):
        assert (packed / ('+Sonic' + ext)).is_file()
        shutil.copy2(packed / ('+Sonic' + ext), source / ('+Sonic' + ext))
    verify = ROOT / 'Build/Review4-RingEnergy/PackCheck/+Sonic.ar.00'
    verify.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / '+Sonic.ar.00', verify)
    unpack(verify)
    actual = {p.name: sha(p) for p in (verify.parent / '+Sonic').iterdir() if p.is_file()}
    assert actual == {name: digest for name, digest in old_members.items() if name != TARGET}

    ini_path = NEXT / 'mod.ini'
    ini = ini_path.read_text(encoding='utf-8-sig')
    assert ini.count('Version="1.0.5-review3"') == 1
    ini_path.write_text(ini.replace('Version="1.0.5-review3"', 'Version="1.0.5-review4"', 1), encoding='utf8')
    readme_path = NEXT / 'README-1.0.5-REVIEW-KO.md'
    readme = readme_path.read_text(encoding='utf8')
    assert '# 한국어 패치 1.0.5-review3 플레이 테스트 후보' in readme
    readme = readme.replace('# 한국어 패치 1.0.5-review3 플레이 테스트 후보',
                            '# 한국어 패치 1.0.5-review4 플레이 테스트 후보', 1)
    readme += ('\nRING ENERGY는 UnleasHD의 게이지 선택 파일을 사용하도록 한국어 아카이브에서 '
               '게임 원본과 동일한 저해상도 복사본만 제거했습니다. UnleasHD를 끄면 게임 원본이 적용됩니다. '
               '테일즈 이벤트 자막과 일본어 글자 페이지는 글자 배치가 달라 영문 HD 파일로 대체하지 않았습니다.\n')
    readme_path.write_text(readme, encoding='utf8')
    result = {'passed': True, 'version': '1.0.5-review4', 'removed': TARGET,
              'removedBytesEqualBaseGame': True, 'remainingMembersVerified': 3,
              'unleasHdGaugeCanSupplyTexture': True, 'gameplayVerified': False,
              'publicRelease': False}
    report = NEXT.parent / 'verification.json'
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
