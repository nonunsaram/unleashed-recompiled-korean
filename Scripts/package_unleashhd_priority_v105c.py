"""Create a local-only playtest ZIP with the corrected HD archive priority."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
ZIP = ROOT / 'outputs/UnleashedRecompiled-Korean-1.0.5-Review3-LocalPlaytest.zip'
META = ROOT / 'Build/Development-v105c-Playtest/package.json'
VERIFY = ROOT / 'Build/Development-v105c-Playtest/verification.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result = json.loads(VERIFY.read_text(encoding='utf8'))
    assert result['passed'] and not result['gameplayVerified'] and not result['publicRelease']
    assert not ZIP.exists() and not META.exists()
    files = sorted(p for p in MOD.rglob('*') if p.is_file())
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for path in files:
            out.write(path, 'UnleashedKorean/' + path.relative_to(MOD).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(files)
        assert all(name.startswith('UnleashedKorean/') for name in archive.namelist())
    data = {'file': str(ZIP), 'bytes': ZIP.stat().st_size, 'sha256': sha(ZIP),
            'files': len(files), 'edition': 'Basic', 'publicRelease': False}
    META.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    main()
