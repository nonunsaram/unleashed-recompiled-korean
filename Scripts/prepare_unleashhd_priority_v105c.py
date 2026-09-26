"""Move the 1440p UI layer ahead of the base Korean append archives."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
REPORT = ROOT / 'Build/Development-v105c-Playtest/verification.json'
HD = ROOT / 'Build/UnleasHD-Compatibility-v105-HUD2/verification.json'


def main() -> None:
    assert OLD.is_dir() and not NEW.exists() and not REPORT.exists()
    hd = json.loads(HD.read_text(encoding='utf8'))
    assert hd['passed'] and (hd['textureCount'], hd['translatedTextureCount']) == (43, 15)
    shutil.copytree(OLD, NEW)
    ini_path = NEW / 'mod.ini'
    ini = ini_path.read_text(encoding='utf-8-sig')
    for needle in ('Version="1.0.5-review2"', 'IncludeDir0="WorldMapVariants/AllDLC"',
                   'IncludeDir1="."', 'IncludeDir2="Compatibility/None"', 'IncludeDirCount=4'):
        assert ini.count(needle) == 1, needle
    ini = ini.replace('Version="1.0.5-review2"', 'Version="1.0.5-review3"', 1)
    ini = ini.replace('IncludeDir1="."\nIncludeDir2="Compatibility/None"',
                      'IncludeDir1="Compatibility/None"\nIncludeDir2="."', 1)
    ini_path.write_text(ini, encoding='utf8')

    schema_path = NEW / 'ConfigSchema.json'
    schema = json.loads(schema_path.read_text(encoding='utf8'))
    options = [e for group in schema['Groups'] for e in group['Elements'] if e['Type'] == 'UnleasHDCompatibility']
    assert len(options) == 1 and options[0]['Name'] == 'IncludeDir2'
    assert options[0]['Value'] == 'Compatibility/None'
    options[0]['Name'] = 'IncludeDir1'
    options[0]['Description'] = [
        'UnleasHD 1.4.2 (1440p) 설치 시 선택하세요.',
        '한국어 패치를 UnleasHD보다 위에 두고 저장한 뒤 게임을 다시 시작하세요.',
        '호환 파일을 기본 한국어 파일보다 먼저 읽도록 하여 HUD·상점·결과 화면 등의 고해상도 UI를 적용합니다.',
    ]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

    readme_path = NEW / 'README-1.0.5-REVIEW-KO.md'
    readme = readme_path.read_text(encoding='utf8')
    assert '# 한국어 패치 1.0.5-review2 플레이 테스트 후보' in readme
    assert '낮·밤 스테이지의 HUD, 결과 화면, 상태 화면, 월드맵을 확인해 주십시오.' in readme
    readme = readme.replace('# 한국어 패치 1.0.5-review2 플레이 테스트 후보',
                            '# 한국어 패치 1.0.5-review3 플레이 테스트 후보', 1)
    readme = readme.replace('낮·밤 스테이지의 HUD, 결과 화면, 상태 화면, 월드맵을 확인해 주십시오.',
                            '낮·밤 스테이지의 HUD, 결과 화면, 상태 화면, 월드맵과 상점의 구매·판매를 확인해 주십시오.', 1)
    readme += ('\n이번 수정에서는 UnleasHD 호환 아카이브가 기본 한국어 아카이브보다 먼저 읽히도록 순서를 바로잡았습니다. '
               'TIME·SCORE·SPEED·RINGS·RING ENERGY와 구매·판매를 포함한 한국어 UI 고해상도 파일을 활성화합니다. '
               'HMM이 열려 있었다면 닫았다가 다시 열고 설정을 저장한 뒤 게임을 완전히 다시 실행해 주십시오.\n')
    readme_path.write_text(readme, encoding='utf8')

    labels = json.loads((ROOT / 'Translation/review/unleashhd-v105/ui-textures-ko-v104-full.json').read_text(encoding='utf8'))['labels']
    assert len(labels) == 149
    shop = [x for x in labels if x['texture'] == 26]
    assert {x['korean'] for x in shop} == {'구매', '판매'}
    result = {'passed': True, 'version': '1.0.5-review3', 'uiTextures': 43,
              'koreanizedHdTextures': 15, 'koreanLabels': 149,
              'shopLabels': ['구매', '판매'], 'compatibilityBeforeBase': True,
              'gameplayVerified': False, 'publicRelease': False}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
