"""Apply development logo/config fixes without making a release ZIP."""
from pathlib import Path
import configparser, json, shutil

R = Path(__file__).resolve().parents[1]

def configure(root):
    root = Path(root)
    ini_path = root/'mod.ini'
    ini = configparser.ConfigParser(interpolation=None)
    ini.optionxform = str
    ini.read(ini_path, encoding='utf-8-sig')
    schema_path = root/'ConfigSchema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8-sig'))
    # HMM writes each element to the INI section named by its group.
    # IncludeDir keys MUST belong to Main, not a cosmetic Compatibility group.
    main = next(g for g in schema['Groups'] if g['Name'] == 'Main')
    main['DisplayName'] = '한국어 패치 설정'
    schema['Groups'] = [g for g in schema['Groups'] if g['Name'] not in ('Compatibility', 'TitleLogo')]
    main['Elements'] = [e for e in main['Elements'] if e['Name'] not in ('IncludeDir2', 'IncludeDir3')]
    compatibility = [
        {'DisplayName': '사용 안 함', 'Value': 'Compatibility/None'},
        {'DisplayName': 'UnleasHD 1.4.2', 'Value': 'Compatibility/UnleasHD-1.4.2'}]
    logos = [
        {'DisplayName': '게임 기본값', 'Value': 'TitleLogos/Default'},
        {'DisplayName': '소닉 언리쉬드 (영문 원본)', 'Value': 'TitleLogos/Original'},
        {'DisplayName': '소닉 월드 어드벤처 (일본어 원본)', 'Value': 'TitleLogos/Japanese'}]
    report_path = R/'Build/TitleLogo-v102/verification.json'
    report = json.loads(report_path.read_text(encoding='utf8'))
    if report['customReady']:
        logos.append({'DisplayName': '소닉 월드 어드벤처 (한국어 편집)', 'Value': 'TitleLogos/Custom'})
    defaults = {'IncludeDir2': 'Compatibility/None', 'IncludeDir3': 'TitleLogos/Default'}
    for key, title, kind, values, description in [
        ('IncludeDir2', 'UnleasHD 호환', 'UnleasHDCompatibility', compatibility,
         ['UnleasHD 1.4.2 사용 시 선택하세요.', '한국어 패치를 UnleasHD보다 위에 두고 저장한 뒤 게임을 다시 시작하세요.']),
        ('IncludeDir3', '타이틀 로고', 'TitleLogoVariant', logos,
         ['한국어 메뉴를 유지하면서 타이틀 화면의 로고를 선택합니다.',
          '게임 기본값은 기존 로고 설정을 따릅니다. 로고 모드를 함께 쓰면 한국어 패치를 위에 두세요.',
          '한국어 편집은 일본어판 로고의 상단 문구를 한국어로 표시합니다.' if report['customReady'] else '사용자 편집 로고는 수정 원본을 받은 뒤 선택지에 추가됩니다.'])]:
        current = ini['Main'].get(key, defaults[key]).strip('"')
        if ini.has_section('Compatibility') and key == 'IncludeDir2':
            current = ini['Compatibility'].get(key, current).strip('"')
        if current not in {v['Value'] for v in values}:
            current = defaults[key]
        ini['Main'][key] = '"'+current+'"'
        main['Elements'].append({'Name': key, 'DisplayName': title, 'Description': description,
            'Type': kind, 'DefaultValue': defaults[key], 'Value': current})
        schema['Enums'][kind] = [{**v, 'Description': v.get('Description', [])} for v in values]
    if ini.has_section('Compatibility'):
        ini.remove_section('Compatibility')
    ini['Main']['IncludeDirCount'] = '4'
    ini['Desc']['Version'] = '"1.0.2"'
    with ini_path.open('w', encoding='utf8', newline='\n') as stream:
        ini.write(stream, space_around_delimiters=False)
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    for values in (compatibility, logos):
        for option in values:
            (root/option['Value']).mkdir(parents=True, exist_ok=True)
    for variant in report['variants']:
        destination = root/'TitleLogos'/variant['name']
        for name in ('+Title.ar.00', '+Title.arl'):
            shutil.copy2(R/'Build/TitleLogo-v102/Variants'/variant['name']/name, destination/name)
    compat = root/'Compatibility/UnleasHD-1.4.2/Languages/English'
    compat.mkdir(parents=True, exist_ok=True)
    for name in ('+WorldMap.ar.00', '+WorldMap.arl'):
        shutil.copy2(R/'Build/UnleasHD-Compatibility-v102/Archive'/name, compat/name)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mod_root', type=Path)
    configure(parser.parse_args().mod_root)
