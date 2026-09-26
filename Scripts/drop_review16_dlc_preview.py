"""Drop the DLC world-map preview correction from the review16 candidate.

Removes Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00 and +WorldMap.arl (which hold
only mat_stage_ss_082.dds) from the development folder and both local ZIPs, updates
the documentation, and verifies:
  * the loader then has no Korean provider for that image in any of the
    7 DLC x 2 UI-profile x 5 logo selections, so UnleasHD (installed below) supplies it;
  * ConfigSchema.json / mod.ini options are unchanged and every option folder still exists;
  * the remaining 1,079 archive members are byte-identical to the previous ZIPs.

No texture is edited. The two dev-folder files are moved (not deleted) into
Build/Review16-DropPreview-Work/removed-from-dev. Run without arguments for a
read-only check; pass --apply to write.
"""
from __future__ import annotations

import configparser
import csv
import hashlib
import io
import json
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fix_review16_docs import (ar_members, build_source_zip, from_lf, sha, to_lf)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "publish/unleashed-recompiled-korean"
DOCS = PUBLIC / "Release/v1.0.5-review16"
OUTPUT = ROOT / "outputs/GameBanana-1.0.5-Review16-Candidate"
AUDIT = ROOT / "outputs/Review16-Independent-Audit"
MOD = ROOT / "Build/Development-v105p-Playtest/UnleashedKorean"
WORK = ROOT / "Build/Review16-DropPreview-Work"
UH = ROOT / "UnleashedRecomp-Windows/mods/UnleasHD-1440p"
MODSDB = ROOT / "UnleashedRecomp-Windows/mods/ModsDB.ini"
EDITIONS = ("Basic", "Full")
TARGET = "mat_stage_ss_082.dds"
TARGET_SHA = "8bca80b074631607a46108cbbe05543090ef522b06675dec4764f66e4c3fb007"
DROP = ["Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00", "Compatibility/UnleasHD-1.4.2/+WorldMap.arl"]
# UnleasHD 1.4.2 1440p: MainMod/+WorldMap.ar.03 holds mat_stage_ss_082.dds
# (member sha256 fc5f16a4…, decoded from this exact file in the 2026-09-26 audit).
UH_PROVIDER = ("MainMod/+WorldMap.arl", "MainMod/+WorldMap.ar.03",
               "e26b1a3e23dcb8e0a5951fd04d971cf2d5501d59fcfcb572a0ba9920ce087114")
CSV_NAME = "UnleasHD-permission-texture-list.csv"
JSON_NAME = "provider-and-permission-audit.json"
REPORT = AUDIT / "허락범위-및-HD수정파일-요약보고서.md"

EXCLUDED_KO = ("**월드맵 DLC 미리보기 수정본 제외:** 엠파이어 시티 스카이스크레이퍼 스캠퍼 밤 Act 2 미리보기 수정은 "
               "UnleasHD 쪽 표시라서 이번 버전에서 제외했습니다. HD 프로필에서는 아래 UnleasHD의 원본 미리보기가 표시됩니다.")
UI_OLD, UI_NEW = "(HUD·상점·월드맵·대화 이름표·DLC 미리보기)", "(HUD·상점·월드맵·대화 이름표)"
EDITS = {
    "changelog": [
        ("HUD·상점·미디어룸·월드맵·이름표·한국어 추가 타이틀 로고·미리보기 수정본과 글꼴·자막·오프닝은",
         "HUD·상점·미디어룸·월드맵·이름표·한국어 추가 타이틀 로고와 글꼴·자막·오프닝은"),
        ("- 설치된 HD 모드의 공급 파일 32개,", f"- {EXCLUDED_KO}\n- 설치된 HD 모드의 공급 파일 32개,"),
        ("- **월드맵 미리보기:** 엠파이어 시티 스카이스크레이퍼 스캠퍼 밤 Act 2의 `SUB STAGE 02` 대체 표시와 사진 왼쪽 흰 선을 수정했습니다.\n", ""),
        (UI_OLD, UI_NEW),
    ],
    "readme_ko": [(UI_OLD, UI_NEW)],
    "readme_en": [
        ("corrects three character names, updates the Empire City night Act 2 preview, and synchronizes",
         "corrects three character names, and synchronizes"),
        ("(HUD, shop, world map, dialogue nameplate, DLC preview)", "(HUD, shop, world map, dialogue nameplate)"),
        ("Redistribution permission for the retained modified UnleasHD artwork is still pending.",
         "The Empire City night Act 2 world-map preview correction is no longer included because it only changed "
         "UnleasHD's own image; the HD profile shows the original UnleasHD preview. "
         "Redistribution permission for the retained modified UnleasHD artwork is still pending."),
    ],
    "credits": [("한국어 UI·이름표·한국어 추가 타이틀 로고와 DLC 미리보기 수정본에는", "한국어 UI·이름표·한국어 추가 타이틀 로고에는")],
    "gamebanana": [("스카이스크레이퍼 스캠퍼 밤 Act 2의 월드맵 미리보기를 수정했고, 한국어 타이틀 로고를",
                    "한국어 타이틀 로고를")],
    "hd_audit": [
        ("대화 이름표 1개, DLC 미리보기 수정본 1개, 한국어 추가 타이틀 그림 4개. 총 **23개 경로**",
         "대화 이름표 1개, 한국어 추가 타이틀 그림 4개. 총 **22개 경로**"),
        ("- 허락 범위 밖: TitleLogos",
         "- 제외: DLC 미리보기 수정본(`Compatibility/UnleasHD-1.4.2/+WorldMap`, `mat_stage_ss_082.dds`). UnleasHD 쪽 표시 수정이라 "
         "이번 버전에서 뺐으며, HD 프로필에서는 아래 UnleasHD의 원본 미리보기가 표시됩니다.\n- 허락 범위 밖: TitleLogos"),
        ("한국어 문구 수정 외에 DLC 미리보기 수정본과 한국어 추가 타이틀 그림도 포함되기 때문입니다.",
         "한국어 문구 수정 외에 한국어 추가 타이틀 그림도 포함되기 때문입니다."),
        ("nameplate and optional Korean title-logo atlases, plus a world-map preview atlas with a DLC-preview correction.",
         "nameplate and optional Korean title-logo atlases."),
        ("these 23 file instances", "these 22 file instances"),
    ],
    "review_notes": [
        ("엠파이어 시티의 스카이스크레이퍼 스캠퍼 밤 Act 2 미리보기에서 UnleasHD가 DLC 사진 대신 표시하던 `SUB STAGE 02`를 수정했습니다. "
         "HD 호환 옵션에서 DLC 원본의 해당 사진 한 칸만 확대해 표시하며 다른 칸은 유지합니다. 이 장면을 게임에서 확인해 주십시오.\n\n", ""),
        ("월드맵 스카이스크레이퍼 스캠퍼 밤 Act 2 사진의 왼쪽 흰 선을 수정했습니다. 실제 사진 칸의 시작점에 맞춰 4픽셀 왼쪽으로 옮겼습니다. "
         "다른 미리보기 칸과 UI 자산은 그대로입니다.\n\n", ""),
        ("수정된 UnleasHD 그림의 배포 허락은 요청 중입니다.",
         "수정된 UnleasHD 그림의 배포 허락은 요청 중입니다. 월드맵 DLC 미리보기 수정본(엠파이어 시티 스카이스크레이퍼 스캠퍼 밤 Act 2)은 "
         "UnleasHD 쪽 표시라서 이번 버전에서 제외했습니다. HD 프로필에서는 아래 UnleasHD의 원본 미리보기가 표시됩니다."),
    ],
    "report": [
        ("\n## 결론\n",
         "\n> 2026-09-26 추가: 이후 DLC 미리보기 수정본(`mat_stage_ss_082.dds`)을 review16 후보에서 제외했습니다. 아래 허락 요청 범위와 "
         "수량은 22개/20종 기준으로 고쳤습니다. '독립 검증 결과' 절은 제외 전 ZIP을 검사한 기록입니다.\n\n## 결론\n"),
        (", ③ 한국어 추가 타이틀 로고 두 종류와 발광 이미지, ④ DLC 미리보기 복구 이미지**입니다. 세 항목으로만 적으려면 첫 항목에 미리보기까지 "
         "명시해야 하며, DM에서는 네 범주로 나누는 것이 정확합니다.",
         ", ③ 한국어 추가 타이틀 로고 두 종류와 발광 이미지**입니다. DLC 미리보기 복구 이미지는 UnleasHD 쪽 표시 수정이라 후보에서 "
         "제외했으므로 요청 범위에서 뺍니다."),
        ("UnleasHD 유래 수정 이미지 23개 배치 경로이며, 파일 내용 중복을 제외하면 21종입니다.",
         "UnleasHD 유래 수정 이미지 22개 배치 경로이며, 파일 내용 중복을 제외하면 20종입니다."),
        ("| DLC 미리보기 복구 | 1 | 2048×1024 UnleasHD 월드맵 미리보기 아틀라스에서 엠파이어 시티 밤 Act 2의 SUB STAGE 02 대체 그림을 게임 DLC "
         "사진으로 복구하고 경계를 보정했습니다. 다른 칸은 HD 그림이 남습니다. 한국어 번역 이미지가 아니어도 허락 범위에 포함해야 합니다. |\n", ""),
        ("| 합계 | **23** | 내용 기준 21종.", "| 합계 | **22** | 내용 기준 20종."),
        ("UI·이름표·미리보기는 주로 1440p 자료이며", "UI·이름표는 주로 1440p 자료이며"),
        ("2. 위 네 범주의 선택된 UnleasHD 기반 이미지와 한국어·미리보기 수정본을", "2. 위 세 범주의 선택된 UnleasHD 기반 이미지와 한국어 수정본을"),
        ("in four categories: Korean-edited UI atlases (including the world map), the dialogue nameplate atlas, two optional "
         "Korean title-logo variants with their glow textures, and a world-map preview atlas with an Empire City night Act 2 "
         "DLC-preview correction. This amounts to 23 texture file instances, or 21 distinct files by content.",
         "in three categories: Korean-edited UI atlases (including the world map), the dialogue nameplate atlas, and two optional "
         "Korean title-logo variants with their glow textures. This amounts to 22 texture file instances, or 20 distinct files by content."),
        ("- UnleasHD-permission-texture-list.csv: 확인된 23개 경로, 크기, SHA-256. 기존 review16 목록과 동일합니다.",
         "- UnleasHD-permission-texture-list.csv: 22개 경로, 크기, SHA-256, 출처. 분할 파트 경로 정정과 DLC 미리보기 제외를 반영했습니다."),
    ],
}
TARGETS = {
    "changelog": [DOCS / "CHANGELOG-KO.md"],
    "readme_ko": [DOCS / "README-BASIC-KO.md", DOCS / "README-FULL-KO.md"],
    "readme_en": [DOCS / "README-EN.md"],
    "credits": [DOCS / "CREDITS.md"],
    "gamebanana": [DOCS / "GameBanana-update.md"],
    "hd_audit": [DOCS / "HD-ASSET-AUDIT-KO.md", MOD / "HD-ASSET-AUDIT-KO.md"],
    "review_notes": [MOD / "README-1.0.5-REVIEW-KO.md"],
    "report": [REPORT],
}
# Candidate-folder copies that must stay identical to the Release folder.
MIRRORED = ["CHANGELOG-KO.md", "GameBanana-update.md", "HD-ASSET-AUDIT-KO.md", CSV_NAME, JSON_NAME]


def nobom(text: str) -> str:
    return text.lstrip("\ufeff")


def edit_text(blob: bytes, edits: list[tuple[str, str]], path: Path) -> bytes:
    raw = blob.decode("utf8")
    mixed = "\r\n" in raw and raw.count("\r\n") != raw.count("\n")
    if mixed:  # edit in place without touching line endings
        text, crlf = raw, None
    else:
        text, crlf = to_lf(blob)
    for old, new in edits:
        assert text.count(old) == 1, (path.name, old[:50])
        text = text.replace(old, new)
    return text.encode("utf8") if mixed else from_lf(text, crlf)


def archive_names(read, names):
    out = {}
    for n in names:
        if re.search(r"\.ar\.\d+$", n):
            out[n] = [m for m, _ in ar_members(read(n))]
    return out


def check_drop_contents() -> None:
    ar, arl = (MOD / DROP[0]).read_bytes(), (MOD / DROP[1]).read_bytes()
    members = ar_members(ar)
    assert [m for m, _ in members] == [TARGET] and sha(members[0][1]) == TARGET_SHA, members and members[0][0]
    assert not list((MOD / DROP[0]).parent.glob("+WorldMap.ar.0[1-9]")), "unexpected extra split parts"
    names = re.findall(rb"[\x20-\x7e]{4,}", arl[8:])
    assert arl[:4] == b"ARL2" and [n.lstrip(b"\x14") for n in names] == [TARGET.encode()], arl
    for ed in EDITIONS:
        with zipfile.ZipFile(OUTPUT / f"UnleashedRecompiled-Korean-1.0.5-Review16-{ed}.zip") as z:
            assert z.read("UnleashedKorean/" + DROP[0]) == ar and z.read("UnleashedKorean/" + DROP[1]) == arl


def check_loader(mod_root: Path) -> dict:
    """With the files gone, no Korean folder may supply the preview in any selection."""
    schema = json.loads(nobom(to_lf((mod_root / "ConfigSchema.json").read_bytes())[0]))
    enums = {k: [x["Value"] for x in v] for k, v in schema["Enums"].items()}
    elements = {e["Name"]: e for e in schema["Groups"][0]["Elements"]}
    assert enums["UnleasHDCompatibility"] == ["Compatibility/None", "Compatibility/UnleasHD-1.4.2"]
    assert len(enums["WorldMapVariant"]) == 7 and len(enums["TitleLogoVariant"]) == 5
    assert [elements[k]["DefaultValue"] for k in ("IncludeDir0", "IncludeDir1", "IncludeDir3")] == \
        ["WorldMapVariants/AllDLC", "Compatibility/None", "TitleLogos/Default"]
    ini = configparser.ConfigParser(interpolation=None)
    ini.read_string(nobom(to_lf((mod_root / "mod.ini").read_bytes())[0]))
    dirs = [ini["Main"][f"IncludeDir{i}"].strip('"') for i in range(int(ini["Main"]["IncludeDirCount"]))]
    assert dirs == ["WorldMapVariants/AllDLC", "Compatibility/None", ".", "TitleLogos/Default"], dirs
    for value in enums["WorldMapVariant"] + ["Compatibility/UnleasHD-1.4.2"]:
        assert (mod_root / value).is_dir() and any((mod_root / value).rglob("*.ar.*")), value
    providers = []
    for path in mod_root.rglob("*"):
        if path.is_file() and re.search(r"\.ar\.\d+$", path.name) and TARGET in [m for m, _ in ar_members(path.read_bytes())]:
            providers.append(path.relative_to(mod_root).as_posix())
        if path.is_file() and path.suffix == ".arl" and TARGET.encode() in path.read_bytes():
            providers.append(path.relative_to(mod_root).as_posix())
    combos = 0
    for dlc in enums["WorldMapVariant"]:
        for profile in enums["UnleasHDCompatibility"]:
            for logo in enums["TitleLogoVariant"]:
                # HMM include order (top wins): DLC variant, UI profile, mod root, logo variant.
                # A provider would be any archive in these folders whose member list has the image.
                chain = [mod_root / d for d in (dlc, profile, ".", logo)]
                hit = [p for p in providers if any((mod_root / p).resolve().is_relative_to(d.resolve()) for d in chain)]
                assert not hit, (dlc, profile, logo, hit)
                combos += 1
    return {"koreanProvidersOfPreview": providers, "selectionsChecked": combos,
            "uiProfiles": enums["UnleasHDCompatibility"], "dlcOptions": enums["WorldMapVariant"],
            "defaults": dirs}


def check_unleashd() -> dict:
    arl = (UH / UH_PROVIDER[0]).read_bytes()
    assert TARGET.encode() in arl
    assert sha((UH / UH_PROVIDER[1]).read_bytes()) == UH_PROVIDER[2]
    ini = configparser.ConfigParser(interpolation=None)
    ini.read_string(nobom(to_lf(MODSDB.read_bytes())[0]))
    main = ini["Main"]
    active = [main[f"ActiveMod{i}"].strip('"') for i in range(int(main["ActiveModCount"]))]
    paths = {k: v.strip('"') for k, v in ini["Mods"].items()}
    order = [Path(paths[a]).parent.name for a in active if a in paths]
    assert main.get("ReverseLoadOrder", "0") == "0"
    ko, uh = order.index("UnleashedKorean"), order.index("UnleasHD-1440p")
    assert ko < uh, order
    hd = configparser.ConfigParser(interpolation=None)
    hd.read_string(nobom(to_lf((UH / "mod.ini").read_bytes())[0]))
    assert hd["Main"]["IncludeDir0"].strip('"') == "MainMod"
    return {"installedOrderTopToBottom": order, "provider": "UnleasHD-1440p/" + UH_PROVIDER[1],
            "providerArchiveSha256": UH_PROVIDER[2]}


def all_members(z: zipfile.ZipFile) -> dict:
    out = {}
    for n in z.namelist():
        if re.search(r"\.ar\.\d+$", n):
            for m, d in ar_members(z.read(n)):
                out[(n, m)] = d
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf8")
    apply = "--apply" in sys.argv[1:]
    check_drop_contents()
    for name in MIRRORED:
        assert (DOCS / name).read_bytes() == (OUTPUT / name).read_bytes(), name
    csv_copies = [AUDIT / CSV_NAME, OUTPUT / CSV_NAME, DOCS / CSV_NAME, MOD / CSV_NAME]
    csv_blob = csv_copies[0].read_bytes()
    assert all(p.read_bytes() == csv_blob for p in csv_copies)
    rows = list(csv.DictReader(io.StringIO(csv_blob.decode("utf-8-sig"), newline="")))
    keep = [r for r in rows if r["file"] != TARGET]
    assert len(rows) == 23 and len(keep) == 22 and len({r["sha256"] for r in keep}) == 20
    assert TARGET_SHA not in {r["sha256"] for r in keep}
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(keep)
    new_csv = buf.getvalue().encode("utf-8-sig")
    jtext, jcrlf = to_lf((DOCS / JSON_NAME).read_bytes())
    jdata = json.loads(jtext)
    retained = jdata["retainedModifiedUnleasHDArtwork"]
    jdata["retainedModifiedUnleasHDArtwork"] = [x for x in retained if x["file"] != TARGET]
    assert len(retained) == 23 and len(jdata["retainedModifiedUnleasHDArtwork"]) == 22
    jdata["excludedAfterReview"] = [{"archive": "Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00", "file": TARGET,
                                     "sha256": TARGET_SHA, "reason": "DLC preview correction changed only UnleasHD's own image"}]
    new_json = from_lf(json.dumps(jdata, ensure_ascii=False, indent=2) + "\n", jcrlf)
    texts = {}
    for key, paths in TARGETS.items():
        for path in paths:
            texts[path] = edit_text(texts.get(path, path.read_bytes()), EDITS[key], path)
    uh = check_unleashd()
    print(json.dumps({"dropContentsVerified": [TARGET], "unleashdProvider": uh,
                      "textFiles": [str(p.relative_to(ROOT)) for p in texts]}, ensure_ascii=False, indent=1))
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
        assert previous[ed].read_bytes() == src.read_bytes()
    removed = WORK / "removed-from-dev"
    for rel in DROP:
        (removed / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(MOD / rel), str(removed / rel))
        assert not (MOD / rel).exists() and (removed / rel).is_file()
    loader = check_loader(MOD)
    assert loader["koreanProvidersOfPreview"] == [] and loader["selectionsChecked"] == 70
    for p in csv_copies:
        p.write_bytes(new_csv)
    (DOCS / JSON_NAME).write_bytes(new_json)
    for path, blob in texts.items():
        path.write_bytes(blob)
    rv_text, rv_crlf = to_lf((DOCS / "release-verification.json").read_bytes())
    rv = json.loads(rv_text)
    assert rv["retainedModifiedHdArtworkInstances"] == 23
    rv["retainedModifiedHdArtworkInstances"] = 22
    rv["excludedDlcPreviewCorrection"] = "Compatibility/UnleasHD-1.4.2/+WorldMap (mat_stage_ss_082.dds)"
    (DOCS / "release-verification.json").write_bytes(from_lf(json.dumps(rv, ensure_ascii=False, indent=2) + "\n", rv_crlf))
    for name in MIRRORED:
        shutil.copyfile(DOCS / name, OUTPUT / name)
    source = WORK / "Source.zip"
    source_names = build_source_zip(source)
    with zipfile.ZipFile(previous["Full"]) as full:
        old_source = set(zipfile.ZipFile(io.BytesIO(full.read("UnleashedKorean/Source.zip"))).namelist())
    added, gone = sorted(set(source_names) - old_source), sorted(old_source - set(source_names))
    assert not gone and set(added) <= {"Source/Scripts/drop_review16_dlc_preview.py"}, (added, gone)
    stamp = time.localtime()[:6]
    records = []
    drop_entries = {"UnleashedKorean/" + d for d in DROP}
    for ed in EDITIONS:
        replacements = {
            "UnleashedKorean/" + CSV_NAME: new_csv,
            "UnleashedKorean/HD-ASSET-AUDIT-KO.md": (MOD / "HD-ASSET-AUDIT-KO.md").read_bytes(),
            "UnleashedKorean/README-1.0.5-REVIEW-KO.md": (MOD / "README-1.0.5-REVIEW-KO.md").read_bytes(),
            "UnleashedKorean/README-KO.md": (DOCS / f"README-{ed.upper()}-KO.md").read_bytes(),
            "UnleashedKorean/README-EN.md": (DOCS / "README-EN.md").read_bytes(),
            "UnleashedKorean/CHANGELOG-KO.md": (DOCS / "CHANGELOG-KO.md").read_bytes(),
            "UnleashedKorean/CREDITS.md": (DOCS / "CREDITS.md").read_bytes(),
        }
        if ed == "Full":
            replacements["UnleashedKorean/BASIC-README-KO.md"] = (DOCS / "README-BASIC-KO.md").read_bytes()
            replacements["UnleashedKorean/Source.zip"] = source.read_bytes()
        dest = OUTPUT / previous[ed].name
        with zipfile.ZipFile(previous[ed]) as old:
            infos = old.infolist()
            names = {i.filename for i in infos}
            assert set(replacements) <= names and drop_entries <= names
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as new:
                for info in infos:
                    if info.filename in drop_entries:
                        continue
                    rep = info.filename in replacements
                    zi = zipfile.ZipInfo(info.filename, date_time=stamp if rep else info.date_time)
                    zi.compress_type, zi.external_attr, zi.create_system = info.compress_type, info.external_attr, info.create_system
                    new.writestr(zi, replacements[info.filename] if rep else old.read(info), compresslevel=9)
        with zipfile.ZipFile(previous[ed]) as old, zipfile.ZipFile(dest) as new:
            assert new.testzip() is None
            assert new.namelist() == [n for n in old.namelist() if n not in drop_entries]
            unchanged = 0
            for n in new.namelist():
                if n in replacements:
                    assert new.read(n) == replacements[n]
                else:
                    assert new.read(n) == old.read(n), n
                    unchanged += 1
            om, nm = all_members(old), all_members(new)
            expected = {k: v for k, v in om.items() if k[0] != "UnleashedKorean/" + DROP[0]}
            assert len(om) == 1080 and len(nm) == 1079 and nm == expected
            assert not any(m == TARGET for _, m in nm)
            # every dev-folder file is in the ZIP byte-for-byte, except documents taken from Release/
            overridden = {"README-KO.md", "README-EN.md", "CHANGELOG-KO.md", "CREDITS.md", "mod.ini"}
            for path in MOD.rglob("*"):
                rel = path.relative_to(MOD).as_posix()
                if path.is_file() and rel not in overridden:
                    assert new.read("UnleashedKorean/" + rel) == path.read_bytes(), rel
            check_zip_loader = {n[len("UnleashedKorean/"):] for n in new.namelist()}
            assert not any(n.startswith("Compatibility/UnleasHD-1.4.2/+WorldMap") for n in check_zip_loader)
        records.append({"file": dest.name, "bytes": dest.stat().st_size, "sha256": sha(dest.read_bytes()),
                        "files": len(infos) - len(drop_entries), "previousSha256": sha(previous[ed].read_bytes()),
                        "removedEntries": sorted(drop_entries), "replacedEntries": sorted(replacements),
                        "unchangedEntries": unchanged, "archiveMembers": 1079})
    with zipfile.ZipFile(OUTPUT / records[0]["file"]) as b, zipfile.ZipFile(OUTPUT / records[1]["file"]) as f:
        assert all_members(b) == all_members(f)
    s_text, s_crlf = to_lf((DOCS / "SHA256SUMS.txt").read_bytes())
    sums = from_lf("".join(f"{r['sha256']}  {r['file']}\n" for r in records), s_crlf)
    for p in (OUTPUT / "SHA256SUMS.txt", DOCS / "SHA256SUMS.txt"):
        p.write_bytes(sums)
    vblob = (DOCS / "CANDIDATE-VERIFY.md").read_bytes()
    assert vblob == (OUTPUT / "CANDIDATE-VERIFY.md").read_bytes()
    vmd, vcrlf = to_lf(vblob)
    for r in records:
        vmd, n = re.subn(rf"(?m)^\| {re.escape(r['file'])} \|.*\|$", f"| {r['file']} | {r['bytes']:,} | {r['sha256']} |", vmd)
        assert n == 1
    old_line = "- 한국어 HD 수정 그림 23개 경로를 기본판·전체판 모두에서 이전 SHA-256과 대조했습니다."
    assert vmd.count(old_line) == 1
    vmd = vmd.replace(old_line, "- 한국어 HD 수정 그림 22개 경로를 기본판·전체판 모두에서 이전 SHA-256과 대조했습니다.")
    anchor = "- 실제 게임의 모든 화면을 플레이 검증한 결과는 아닙니다."
    assert vmd.count(anchor) == 1
    note = ("- 2026-09-26 DLC 미리보기 제외: `Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00`·`.arl`"
            "(`mat_stage_ss_082.dds` 하나)을 개발 폴더와 두 ZIP에서 뺐습니다. 70가지 선택 조합에서 한국어 패치가 이 이미지를 "
            "공급하지 않아 HD 프로필에서는 아래 UnleasHD 원본이 표시됩니다. 남은 아카이브 내부 리소스 1,079개는 이전 ZIP과 "
            "바이트 단위로 동일합니다.\n")
    vmd = vmd.replace(anchor, note + anchor)
    for p in (DOCS / "CANDIDATE-VERIFY.md", OUTPUT / "CANDIDATE-VERIFY.md"):
        p.write_bytes(from_lf(vmd, vcrlf))
    ptext, pcrlf = to_lf((OUTPUT / "package-verification.json").read_bytes())
    pkg = json.loads(ptext)
    pkg["archives"] = [{k: r[k] for k in ("file", "bytes", "sha256", "files")} for r in records]
    pkg["dlcPreviewExclusion"] = {"date": "2026-09-26", "removedEntries": sorted(drop_entries),
                                  "archiveMembers": 1079, "remainingMembersByteIdentical": True,
                                  "previousArchives": [{"file": r["file"], "sha256": r["previousSha256"]} for r in records]}
    (OUTPUT / "package-verification.json").write_bytes(from_lf(json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", pcrlf))
    result = {"passed": True, "loader": loader, "unleashd": uh, "archives": records, "sourceZipAdded": added,
              "movedFromDev": [str((removed / d).relative_to(ROOT)) for d in DROP]}
    (WORK / "drop-preview-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in ("passed", "loader", "archives", "sourceZipAdded")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
