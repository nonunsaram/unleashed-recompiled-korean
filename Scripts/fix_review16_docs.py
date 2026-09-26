"""Correct review16 documentation only, then repackage the local candidate ZIPs.

What this script changes
- UnleasHD-permission-texture-list.csv (+ provider-and-permission-audit.json):
  three split-archive paths (.ar.00 -> .ar.01, verified by opening the archives)
  and a new `source` column (UnleasHD 1.4.2 1440p / UnleasHD 4K repository).
- Provenance wording in README/CHANGELOG/upload notes, one scope line in
  HD-ASSET-AUDIT-KO.md.
- Basic/Full ZIPs are rebuilt by copying every existing entry and replacing only
  the documentation entries (and Source.zip in Full). The installer EXE, patches,
  DDS files and game archives are copied unchanged, and every archive member is
  verified byte-identical to the previous ZIP.

Game textures and archive contents are never written. Run without arguments for
a read-only check; pass --apply to write.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "publish/unleashed-recompiled-korean"
DOCS = PUBLIC / "Release/v1.0.5-review16"
OUTPUT = ROOT / "outputs/GameBanana-1.0.5-Review16-Candidate"
AUDIT = ROOT / "outputs/Review16-Independent-Audit"
MOD = ROOT / "Build/Development-v105p-Playtest/UnleashedKorean"
WORK = ROOT / "Build/Review16-DocFix-Work"
EDITIONS = ("Basic", "Full")
REV_4K = "c7a709743926a94eb4b9337c54d9abdb103fb8f1"
SRC_1440 = "UnleasHD 1.4.2 1440p"
SRC_4K = f"UnleasHD 4K repo {REV_4K}"
EXPECTED_MOVES = {
    ("Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap", "mat_worldmap_en_002.dds"),
    ("TitleLogos/Korean/+Title", "mat_title_004.dds"),
    ("TitleLogos/Custom/+Title", "mat_title_004.dds"),
}
CSV_NAME = "UnleasHD-permission-texture-list.csv"
JSON_NAME = "provider-and-permission-audit.json"
# Files written after packaging; the original Source.zip never contained them.
POST_PACKAGE = {"SHA256SUMS.txt", "CANDIDATE-VERIFY.md", "release-verification.json"}

UI_KO = "UI 호환 파일(HUD·상점·월드맵·대화 이름표·DLC 미리보기)"
TEXT_EDITS = {
    "readme": [(
        "이 검토본의 HD 파일은 설치된 UnleasHD 자산으로 만들었으며, 공개 배포 조건이 확인되기 전까지 로컬 시험용입니다.",
        f"이 검토본에 포함된 UnleasHD 파생 그림 중 {UI_KO}은 UnleasHD 1.4.2(1440p), 한국어 추가 타이틀 로고와 발광 이미지는 "
        "UnleasHD 4K 저장소 자료(리비전 c7a70974)를 바탕으로 만들었습니다. 공개 배포 조건이 확인되기 전까지 로컬 시험용입니다.",
    )],
    "changelog": [(
        "이 검토본은 설치된 UnleasHD 자산으로 만든 HD 호환 파일을 포함합니다.",
        f"이 검토본은 UnleasHD 자료를 바탕으로 수정한 HD 파일을 포함합니다. {UI_KO}은 UnleasHD 1.4.2(1440p), "
        f"한국어 추가 타이틀 로고 두 종류와 발광 이미지는 UnleasHD 4K 저장소 자료(리비전 {REV_4K})가 바탕입니다.",
    )],
    "readme_en": [(
        "The review build includes compatibility files derived from a locally installed UnleasHD mod.",
        "The review build includes UnleasHD-derived files. The UI compatibility files (HUD, shop, world map, "
        "dialogue nameplate, DLC preview) are based on UnleasHD 1.4.2 (1440p); the optional Korean title logos "
        "and their glow textures are based on assets from the UnleasHD 4K repository (revision c7a70974).",
    )],
    "upload": [(
        "HD 호환 폴더는 설치된 UnleasHD 1.4.2(1440p) 자산을 바탕으로 만들어졌으며,",
        "HD 호환 폴더의 UI 파일은 UnleasHD 1.4.2(1440p), 한국어 추가 타이틀 로고는 "
        "UnleasHD 4K 저장소 자료(리비전 c7a70974)를 바탕으로 만들어졌으며,",
    )],
    "review_notes": [(
        "이 후보는 설치된 UnleasHD 자산을 바탕으로 로컬에서 생성한 것으로 공개 재배포용이 아닙니다.",
        "이 후보의 UnleasHD 파생 파일은 UI 호환 파일이 UnleasHD 1.4.2(1440p), 한국어 추가 타이틀 로고가 "
        "UnleasHD 4K 저장소 자료(리비전 c7a70974)를 바탕으로 로컬에서 만든 것으로 공개 재배포용이 아닙니다.",
    )],
    "hd_audit": [(
        "- 유지: 직접 만든 한국어 글꼴·자막과 게임 원본 기반 한국어 오프닝 로고. 모든 유지 리소스는 review15와 동일합니다.\n",
        "- 유지: 직접 만든 한국어 글꼴·자막과 게임 원본 기반 한국어 오프닝 로고. 모든 유지 리소스는 review15와 동일합니다.\n"
        "- 허락 범위 밖: TitleLogos 네 종류(Original·Japanese·Korean·Custom)의 `ui_title.yncp`는 게임 원본을 수정한 파일이며 "
        "UnleasHD 허락 범위가 아닙니다. `mat_title_en_002.dds`(타이틀 언어 선택 문구)는 한국어 언어명을 직접 렌더링한 파일입니다.\n",
    )],
}
TEXT_TARGETS = {
    "readme": [DOCS / "README-BASIC-KO.md", DOCS / "README-FULL-KO.md"],
    "changelog": [DOCS / "CHANGELOG-KO.md", OUTPUT / "CHANGELOG-KO.md"],
    "readme_en": [DOCS / "README-EN.md"],
    "upload": [DOCS / "Upload-guide-KO.md", OUTPUT / "Upload-guide-KO.md"],
    "review_notes": [MOD / "README-1.0.5-REVIEW-KO.md"],
    "hd_audit": [DOCS / "HD-ASSET-AUDIT-KO.md", OUTPUT / "HD-ASSET-AUDIT-KO.md", MOD / "HD-ASSET-AUDIT-KO.md"],
}


def to_lf(blob: bytes) -> tuple[str, bool]:
    """Decode UTF-8 text, remembering whether it used CRLF line endings."""
    text = blob.decode("utf8")
    crlf = "\r\n" in text
    if crlf:
        assert text.count("\r\n") == text.count("\n"), "mixed line endings"
    return text.replace("\r\n", "\n"), crlf


def from_lf(text: str, crlf: bool) -> bytes:
    return (text.replace("\n", "\r\n") if crlf else text).encode("utf8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ar_members(data: bytes) -> list[tuple[str, bytes]]:
    """Parse one uncompressed Hedgehog Engine .ar part."""
    assert data[:4] == b"\0\0\0\0", "unexpected archive header"
    out, offset = [], struct.unpack_from("<I", data, 4)[0]
    while offset < len(data):
        size, length, start, _, _ = struct.unpack_from("<5I", data, offset)
        name = data[offset + 20:data.index(0, offset + 20, offset + start)].decode("utf8")
        out.append((name, data[offset + start:offset + start + length]))
        offset += size
    assert offset == len(data)
    return out


def base_of(archive: str) -> str:
    return re.sub(r"\.ar\.\d+$", "", archive)


def locate(read, names: list[str], base: str, file: str) -> tuple[str, bytes]:
    """Return (split part name, member bytes) for `file` among the parts of `base`."""
    parts = sorted(n for n in names if re.fullmatch(re.escape(base) + r"\.ar\.\d+", n))
    hits = [(p, d) for p in parts for n, d in ar_members(read(p)) if n == file]
    assert len(hits) == 1, (base, file, [h[0] for h in hits])
    return hits[0]


def all_members(zf: zipfile.ZipFile) -> dict[tuple[str, str], bytes]:
    result = {}
    for name in zf.namelist():
        if re.search(r"\.ar\.\d+$", name):
            for member, data in ar_members(zf.read(name)):
                key = (name, member)
                assert key not in result
                result[key] = data
    return result


def verify_parts() -> tuple[list[dict], dict]:
    copies = [AUDIT / CSV_NAME, OUTPUT / CSV_NAME, DOCS / CSV_NAME, MOD / CSV_NAME]
    blobs = {p: p.read_bytes() for p in copies}
    assert len(set(blobs.values())) == 1, "CSV copies differ before the fix"
    rows = list(csv.DictReader(io.StringIO(blobs[copies[0]].decode("utf-8-sig"), newline="")))
    assert len(rows) == 23 and "source" not in rows[0]
    assert csv_bytes(rows) == blobs[copies[0]], "CSV would not round-trip byte-identically"
    mod_names = [p.relative_to(MOD).as_posix() for p in MOD.rglob("*.ar.*")]
    zips = {ed: zipfile.ZipFile(OUTPUT / f"UnleashedRecompiled-Korean-1.0.5-Review16-{ed}.zip") for ed in EDITIONS}
    evidence = []
    for row in rows:
        base = base_of(row["archive"])
        part, data = locate(lambda n: (MOD / n).read_bytes(), mod_names, base, row["file"])
        assert sha(data) == row["sha256"], row
        for ed, zf in zips.items():
            names = [n[len("UnleashedKorean/"):] for n in zf.namelist()]
            zpart, zdata = locate(lambda n: zf.read("UnleashedKorean/" + n), names, base, row["file"])
            assert zpart == part and sha(zdata) == row["sha256"], (ed, row)
        moved = part != row["archive"]
        assert moved == ((base, row["file"]) in EXPECTED_MOVES), (row, part)
        if moved:
            assert row["archive"].endswith(".ar.00") and part.endswith(".ar.01")
        evidence.append({"file": row["file"], "csvArchive": row["archive"], "actualPart": part,
                         "sha256": row["sha256"], "presentInBasicAndFull": True})
        row["archive"] = part
        row["source"] = SRC_4K if row["category"] == "Korean title logo" else SRC_1440
    for zf in zips.values():
        zf.close()
    assert sum(r["source"] == SRC_4K for r in rows) == 4
    return rows, {"csvRows": evidence}


def csv_bytes(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def json_bytes(rows: list[dict]) -> bytes:
    blob = (DOCS / JSON_NAME).read_bytes()
    assert blob == (OUTPUT / JSON_NAME).read_bytes()
    text, crlf = to_lf(blob)
    data = json.loads(text)
    assert from_lf(json.dumps(data, ensure_ascii=False, indent=2) + "\n", crlf) == blob
    by_key = {(base_of(r["archive"]), r["file"]): r for r in rows}
    retained = data["retainedModifiedUnleasHDArtwork"]
    assert len(retained) == 23
    for item in retained:
        row = by_key[(base_of(item["archive"]), item["file"])]
        assert item["sha256"] == row["sha256"]
        item["archive"], item["source"] = row["archive"], row["source"]
    return from_lf(json.dumps(data, ensure_ascii=False, indent=2) + "\n", crlf)


def edited_texts() -> dict[Path, bytes]:
    result = {}
    for key, paths in TEXT_TARGETS.items():
        for path in paths:
            text, crlf = to_lf(result.get(path, path.read_bytes()))
            for old, new in TEXT_EDITS[key]:
                assert text.count(old) == 1, (path, old[:40])
                text = text.replace(old, new)
            result[path] = from_lf(text, crlf)
    return result


def build_source_zip(destination: Path) -> list[str]:
    tracked = subprocess.check_output(
        ["git", "-c", f"safe.directory={PUBLIC.as_posix()}", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=PUBLIC).decode("utf8").splitlines()
    allowed = {".py", ".cjs", ".cs", ".ps1", ".md", ".txt", ".json", ".cpp", ".h", ".patch", ".ttf", ".png", ".pdf", ".csv"}
    written = []
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(set(tracked)):
            path = PUBLIC / name
            if not path.is_file() or path.suffix.lower() not in allowed or path.stat().st_size >= 100 * 1024 * 1024:
                continue
            if name.startswith("Release/v1.0.5-review16/") and path.name in POST_PACKAGE:
                continue
            assert ".." not in Path(name).parts
            archive.write(path, "Source/" + name.replace("\\", "/"))
            written.append("Source/" + name)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any(n.lower().endswith((".dds", ".iso", ".xex", ".exe", ".zip")) or re.search(r"\.ar\.\d+$", n)
                       or n.lower().endswith(".arl") for n in names)
    return written


def repackage(edition: str, previous: Path, replacements: dict[str, bytes]) -> dict:
    name = previous.name
    destination = OUTPUT / name
    stamp = time.localtime()[:6]
    with zipfile.ZipFile(previous) as old:
        infos = old.infolist()
        assert set(replacements) <= {i.filename for i in infos}, set(replacements) - {i.filename for i in infos}
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as new:
            for info in infos:
                replaced = info.filename in replacements
                data = replacements[info.filename] if replaced else old.read(info)
                zi = zipfile.ZipInfo(info.filename, date_time=stamp if replaced else info.date_time)
                zi.compress_type = info.compress_type
                zi.external_attr = info.external_attr
                zi.create_system = info.create_system
                new.writestr(zi, data, compresslevel=9)
    with zipfile.ZipFile(previous) as old, zipfile.ZipFile(destination) as new:
        assert new.testzip() is None
        assert new.namelist() == old.namelist()
        unchanged = 0
        for info in old.infolist():
            if info.filename in replacements:
                assert new.read(info.filename) == replacements[info.filename]
            else:
                assert new.read(info.filename) == old.read(info), info.filename
                unchanged += 1
        old_members, new_members = all_members(old), all_members(new)
        assert len(old_members) == len(new_members) == 1080
        assert all(new_members[k] == v for k, v in old_members.items())
    return {"file": name, "bytes": destination.stat().st_size, "sha256": sha(destination.read_bytes()),
            "files": len(infos), "replacedEntries": sorted(replacements), "unchangedEntries": unchanged,
            "archiveMembersByteIdentical": 1080, "previousSha256": sha(previous.read_bytes())}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf8")
    apply = "--apply" in sys.argv[1:]
    rows, evidence = verify_parts()
    new_csv, new_json, texts = csv_bytes(rows), json_bytes(rows), edited_texts()
    print(json.dumps({"partsVerified": evidence["csvRows"], "textFiles": [str(p.relative_to(ROOT)) for p in texts]},
                     ensure_ascii=False, indent=1))
    if not apply:
        print("read-only check passed; rerun with --apply to write")
        return
    assert not WORK.exists()
    (WORK / "previous").mkdir(parents=True)
    previous = {}
    for ed in EDITIONS:
        src = OUTPUT / f"UnleashedRecompiled-Korean-1.0.5-Review16-{ed}.zip"
        previous[ed] = WORK / "previous" / src.name
        shutil.copy2(src, previous[ed])
        assert sha(previous[ed].read_bytes()) == sha(src.read_bytes())
    for path in (AUDIT / CSV_NAME, OUTPUT / CSV_NAME, DOCS / CSV_NAME, MOD / CSV_NAME):
        path.write_bytes(new_csv)
    for path in (DOCS / JSON_NAME, OUTPUT / JSON_NAME):
        path.write_bytes(new_json)
    for path, blob in texts.items():
        path.write_bytes(blob)
    source = WORK / "Source.zip"
    source_names = build_source_zip(source)
    with zipfile.ZipFile(OUTPUT / previous["Full"].name) as full:
        old_source = set(zipfile.ZipFile(io.BytesIO(full.read("UnleashedKorean/Source.zip"))).namelist())
    added, removed = sorted(set(source_names) - old_source), sorted(old_source - set(source_names))
    assert not removed and set(added) <= {"Source/Scripts/fix_review16_docs.py"}, (added, removed)
    records = []
    for ed in EDITIONS:
        replacements = {
            "UnleashedKorean/" + CSV_NAME: new_csv,
            "UnleashedKorean/HD-ASSET-AUDIT-KO.md": (MOD / "HD-ASSET-AUDIT-KO.md").read_bytes(),
            "UnleashedKorean/README-1.0.5-REVIEW-KO.md": (MOD / "README-1.0.5-REVIEW-KO.md").read_bytes(),
            "UnleashedKorean/README-KO.md": (DOCS / f"README-{ed.upper()}-KO.md").read_bytes(),
            "UnleashedKorean/README-EN.md": (DOCS / "README-EN.md").read_bytes(),
            "UnleashedKorean/CHANGELOG-KO.md": (DOCS / "CHANGELOG-KO.md").read_bytes(),
        }
        if ed == "Full":
            replacements["UnleashedKorean/BASIC-README-KO.md"] = (DOCS / "README-BASIC-KO.md").read_bytes()
            replacements["UnleashedKorean/Source.zip"] = source.read_bytes()
        records.append(repackage(ed, previous[ed], replacements))
    with zipfile.ZipFile(OUTPUT / records[0]["file"]) as b, zipfile.ZipFile(OUTPUT / records[1]["file"]) as f:
        assert all_members(b) == all_members(f)
    sums_text, sums_crlf = to_lf((DOCS / "SHA256SUMS.txt").read_bytes())
    sums = from_lf("".join(f"{r['sha256']}  {r['file']}\n" for r in records), sums_crlf)
    for path in (OUTPUT / "SHA256SUMS.txt", DOCS / "SHA256SUMS.txt"):
        path.write_bytes(sums)
    verify_blob = (DOCS / "CANDIDATE-VERIFY.md").read_bytes()
    assert verify_blob == (OUTPUT / "CANDIDATE-VERIFY.md").read_bytes()
    verify_md, verify_crlf = to_lf(verify_blob)
    for r in records:
        line = f"| {r['file']} | {r['bytes']:,} | {r['sha256']} |"
        verify_md, n = re.subn(rf"(?m)^\| {re.escape(r['file'])} \|.*\|$", line, verify_md)
        assert n == 1
    anchor = "- 실제 게임의 모든 화면을 플레이 검증한 결과는 아닙니다."
    assert verify_md.count(anchor) == 1
    note = ("- 2026-09-26 문서 정정: 허락 요청 CSV의 분할 아카이브 경로 3건(.ar.00→.ar.01)과 출처 열, HD 자료 출처 문구"
            "(UI 호환 파일 1440p / 한국어 타이틀 로고 4K 저장소), `ui_title.yncp`·언어 선택 문구 설명을 고쳐 ZIP을 다시 묶었습니다. "
            "아카이브 내부 리소스 1,080개와 설치 도구·패치·DDS는 정정 전 ZIP과 바이트 단위로 동일합니다.\n")
    verify_md = verify_md.replace(anchor, note + anchor)
    for path in (DOCS / "CANDIDATE-VERIFY.md", OUTPUT / "CANDIDATE-VERIFY.md"):
        path.write_bytes(from_lf(verify_md, verify_crlf))
    package_text, package_crlf = to_lf((OUTPUT / "package-verification.json").read_bytes())
    package = json.loads(package_text)
    package["archives"] = [{k: r[k] for k in ("file", "bytes", "sha256", "files")} for r in records]
    package["documentationFix"] = {"date": "2026-09-26", "archiveMembersByteIdentical": 1080,
                                   "previousArchives": [{"file": r["file"], "sha256": r["previousSha256"]} for r in records],
                                   "replacedEntries": {r["file"]: r["replacedEntries"] for r in records}}
    (OUTPUT / "package-verification.json").write_bytes(
        from_lf(json.dumps(package, ensure_ascii=False, indent=2) + "\n", package_crlf))
    result = {"passed": True, **evidence, "archives": records, "sourceZipAdded": added,
              "sourceZipExcludedPostPackageFiles": sorted(POST_PACKAGE)}
    (WORK / "docfix-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in ("passed", "archives", "sourceZipAdded")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
