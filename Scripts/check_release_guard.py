"""Release guard for the review16 package (read-only).

Fails (exit code 1) when any target ZIP or folder:
  1. contains Compatibility/UnleasHD-1.4.2/+WorldMap.ar.* or +WorldMap.arl
     (the excluded DLC world-map preview correction), at any depth, including nested ZIPs;
  2. contains mat_stage_ss_082.dds in any archive, as a loose file, in an .arl list,
     or its excluded Korean-corrected bytes under any name;
  3. has a permission CSV that is not exactly the approved 22 rows / 20 distinct files,
     or whose rows are not present with the listed hash;
  4. contains any texture whose hash matches an UnleasHD 1.4.2 1440p texture that is not in
     the CSV (checked against the installed UnleasHD-1440p mod when present, plus the frozen
     member-hash manifest for its compressed archives);
  5. contains a compressed or unreadable .ar archive (cannot be inspected);
  6. contains, under Compatibility/UnleasHD-1.4.2/ or TitleLogos/, a DDS that has an UnleasHD
     texture name but is neither in the CSV nor in the approved review16 baseline
     (a possible new UnleasHD-derived texture: ask the user before adding it).

Usage:
  python Scripts/check_release_guard.py                 # both candidate ZIPs + dev folder
  python Scripts/check_release_guard.py A.zip B.zip DIR  # explicit targets
  python Scripts/check_release_guard.py --json out.json ...
Nothing is written except the optional --json report.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_guard_data as DATA  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/GameBanana-1.0.5-Review16-Candidate"
MOD = ROOT / "Build/Development-v105p-Playtest/UnleashedKorean"
UNLEASHD = ROOT / "UnleashedRecomp-Windows/mods/UnleasHD-1440p"
DEFAULT_TARGETS = [OUTPUT / "UnleashedRecompiled-Korean-1.0.5-Review16-Basic.zip",
                   OUTPUT / "UnleashedRecompiled-Korean-1.0.5-Review16-Full.zip", MOD]
CSV_NAME = "UnleasHD-permission-texture-list.csv"
FORBIDDEN_PATH = re.compile(r"(^|/)Compatibility/UnleasHD-1\.4\.2/\+WorldMap\.(ar\.\d+|arl)$", re.I)
HD_PATH = re.compile(r"^(Compatibility/UnleasHD-1\.4\.2/|TitleLogos/)")
ARCHIVE = re.compile(r"\.ar\.\d+$", re.I)
XCOMPRESS = b"\x0f\xf5\x12\xee"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ar_members(data: bytes) -> list[tuple[str, bytes]]:
    if data[:4] != b"\0\0\0\0":
        raise ValueError("not an uncompressed .ar archive")
    out, offset = [], struct.unpack_from("<I", data, 4)[0]
    while offset < len(data):
        size, length, start, _, _ = struct.unpack_from("<5I", data, offset)
        if size < 21 or start + length > size or offset + size > len(data):
            raise ValueError("corrupt entry")
        name = data[offset + 20:data.index(0, offset + 20, offset + start)].decode("utf8")
        out.append((name, data[offset + start:offset + start + length]))
        offset += size
    if offset != len(data):
        raise ValueError("trailing bytes")
    return out


def iter_files(target: Path):
    """Yield (relative path, bytes) for every file of a ZIP (recursing into nested ZIPs) or folder."""
    def walk_zip(blob: bytes, prefix: str):
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                data = zf.read(info)
                yield prefix + info.filename, data
                if info.filename.lower().endswith(".zip"):
                    yield from walk_zip(data, prefix + info.filename + "!/")
    if target.is_dir():
        for path in sorted(target.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                rel = path.relative_to(target).as_posix()
                yield rel, data
                if path.suffix.lower() == ".zip":
                    yield from walk_zip(data, rel + "!/")
    else:
        yield from walk_zip(target.read_bytes(), "")


def mod_relative(path: str) -> str:
    """Path inside the mod folder: drop the 'UnleashedKorean/' ZIP prefix."""
    return path.split("UnleashedKorean/", 1)[1] if path.startswith("UnleashedKorean/") else path


def unleashd_reference() -> tuple[dict[str, str], set[str], list[str], list[str]]:
    """Hash -> origin and texture names of UnleasHD, verified against the installed mod when present."""
    hashes = dict(DATA.UNLEASHD_MEMBER_SHA256)
    names = {n.lower() for n in DATA.UNLEASHD_MEMBER_NAMES}
    notes, problems = [], []
    for rel, value in DATA.UNLEASHD_ARCHIVE_FILE_SHA256.items():
        hashes.setdefault(value, rel + " (compressed archive file)")
    if UNLEASHD.is_dir():
        installed = {p.relative_to(UNLEASHD).as_posix(): p for p in UNLEASHD.rglob("*") if p.is_file()}
        arcs = {k for k in installed if ARCHIVE.search(k)}
        if arcs != set(DATA.UNLEASHD_ARCHIVE_FILE_SHA256):
            problems.append("installed UnleasHD-1440p archive list differs from the frozen manifest "
                            f"(missing {sorted(set(DATA.UNLEASHD_ARCHIVE_FILE_SHA256) - arcs)[:5]}, extra {sorted(arcs - set(DATA.UNLEASHD_ARCHIVE_FILE_SHA256))[:5]})")
        for rel in sorted(arcs & set(DATA.UNLEASHD_ARCHIVE_FILE_SHA256)):
            if sha(installed[rel].read_bytes()) != DATA.UNLEASHD_ARCHIVE_FILE_SHA256[rel]:
                problems.append(f"installed UnleasHD archive changed since the manifest was frozen: {rel}")
        loose = 0
        for rel, path in installed.items():
            if ARCHIVE.search(rel) or path.suffix.lower() in (".arl", ".ini", ".json", ".md", ".txt"):
                continue
            hashes.setdefault(sha(path.read_bytes()), "UnleasHD-1440p/" + rel)
            names.add(path.name.lower())
            loose += 1
        notes.append(f"installed UnleasHD-1440p verified against the manifest; {loose} loose files hashed live")
    else:
        notes.append("UnleasHD-1440p is not installed here: using the frozen member manifest only "
                     "(loose UnleasHD files such as loading screens are not covered)")
    if problems:
        problems.append("update Scripts/release_guard_data.py only after the user approves the new UnleasHD version")
    return hashes, names, notes, problems


def check_target(target: Path, uh_hashes: dict[str, str], uh_names: set[str]) -> dict:
    failures = []
    approved = {(a, f): h for a, f, h in DATA.APPROVED_CSV}
    approved_hashes = set(approved.values())
    approved_base = {(re.sub(r"\.ar\.\d+$", "", a), f) for a, f, _ in DATA.APPROVED_CSV}
    members: dict[tuple[str, str], str] = {}
    csv_blob = None
    archives = members_count = 0
    for path, data in iter_files(target):
        rel = mod_relative(path.split("!/")[-1]) if "!/" in path else mod_relative(path)
        low = path.lower()
        if FORBIDDEN_PATH.search(rel) or FORBIDDEN_PATH.search(path):
            failures.append(f"[1] excluded DLC-preview archive present: {path}")
        digest = sha(data)
        if digest in DATA.FORBIDDEN_SHA256:
            failures.append(f"[2] excluded DLC-preview texture bytes present: {path}")
        if Path(low).name == DATA.FORBIDDEN_NAME:
            failures.append(f"[2] {DATA.FORBIDDEN_NAME} present as a loose file: {path}")
        if low.endswith(".arl") and DATA.FORBIDDEN_NAME.encode() in data:
            failures.append(f"[2] {DATA.FORBIDDEN_NAME} listed in {path}")
        if digest in uh_hashes and digest not in approved_hashes:
            failures.append(f"[4] unlisted UnleasHD file: {path} == {uh_hashes[digest]}")
        if "!/" not in path and path.endswith(CSV_NAME) and rel == CSV_NAME:
            csv_blob = data
        if ARCHIVE.search(low):
            archives += 1
            if data[:4] == XCOMPRESS:
                failures.append(f"[5] compressed archive cannot be inspected: {path}")
                continue
            try:
                entries = ar_members(data)
            except ValueError as error:
                failures.append(f"[5] unreadable archive {path}: {error}")
                continue
            base = re.sub(r"\.ar\.\d+$", "", rel)
            for name, blob in entries:
                members_count += 1
                h = sha(blob)
                members[(rel, name)] = h
                if name.lower() == DATA.FORBIDDEN_NAME or h in DATA.FORBIDDEN_SHA256:
                    failures.append(f"[2] excluded DLC-preview texture inside {path}: {name}")
                if h in uh_hashes and h not in approved_hashes:
                    failures.append(f"[4] unlisted UnleasHD texture inside {path}: {name} == {uh_hashes[h]}")
                if (name.lower().endswith(".dds") and HD_PATH.match(rel) and name.lower() in uh_names
                        and (base, name) not in approved_base
                        and DATA.HD_PATH_BASELINE.get(f"{base}|{name}") != h):
                    failures.append(f"[6] new or changed HD-path texture with an UnleasHD name, not in the CSV: "
                                    f"{rel}:{name} ({h[:12]}) - ask the user before packaging it")
        elif (low.endswith(".dds") and "!/" not in path and HD_PATH.match(rel)
              and Path(low).name in uh_names and DATA.HD_PATH_BASELINE.get(f"{rel}|") != digest):
            failures.append(f"[6] new or changed HD-path loose texture with an UnleasHD name: {rel} ({digest[:12]})")
    # [3] permission CSV
    if csv_blob is None:
        failures.append(f"[3] {CSV_NAME} is missing")
    else:
        rows = list(csv.DictReader(io.StringIO(csv_blob.decode("utf-8-sig"), newline="")))
        distinct = {r.get("sha256") for r in rows}
        if len(rows) != 22 or len(distinct) != 20:
            failures.append(f"[3] CSV has {len(rows)} rows / {len(distinct)} distinct files (expected 22 / 20)")
        listed = {(r.get("archive"), r.get("file")): r.get("sha256") for r in rows}
        if listed != approved:
            failures.append("[3] CSV rows differ from the approved review16 list "
                            f"(added {sorted(set(listed) - set(approved))[:3]}, removed {sorted(set(approved) - set(listed))[:3]})")
        if any(r.get("file", "").lower() == DATA.FORBIDDEN_NAME for r in rows):
            failures.append(f"[3] CSV still lists {DATA.FORBIDDEN_NAME}")
        for (arc, name), h in approved.items():
            if members.get((arc, name)) != h:
                failures.append(f"[3] CSV row not found with the listed hash: {arc}:{name}")
    return {"target": str(target), "passed": not failures, "archives": archives,
            "archiveMembers": members_count, "failures": failures}


def run(targets: list[Path]) -> dict:
    uh_hashes, uh_names, notes, problems = unleashd_reference()
    results = []
    for target in targets:
        if not target.exists():
            results.append({"target": str(target), "passed": False, "failures": ["target does not exist"]})
            continue
        results.append(check_target(target, uh_hashes, uh_names))
    passed = not problems and all(r["passed"] for r in results)
    return {"passed": passed, "unleashdReference": notes, "referenceProblems": problems, "results": results}


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf8")
    report_path = None
    if "--json" in argv:
        i = argv.index("--json")
        report_path = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    targets = [Path(a) for a in argv] or DEFAULT_TARGETS
    report = run(targets)
    for note in report["unleashdReference"]:
        print("note:", note)
    for problem in report["referenceProblems"]:
        print("FAIL reference:", problem)
    for r in report["results"]:
        print(("PASS" if r["passed"] else "FAIL"), r["target"],
              f"(archives {r.get('archives', 0)}, members {r.get('archiveMembers', 0)})")
        for failure in r["failures"][:40]:
            print("   ", failure)
        if len(r["failures"]) > 40:
            print(f"    ... {len(r['failures']) - 40} more")
    if report_path:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("RELEASE GUARD:", "PASSED" if report["passed"] else "FAILED")
    return 0 if report["passed"] else 1


def require_pass(targets: list[Path], label: str = "") -> None:
    """For packaging scripts: rename failed ZIPs to *-FAILED.zip and exit 1."""
    report = run(targets)
    if report["passed"]:
        print(f"release guard passed{(' for ' + label) if label else ''}")
        return
    for r in report["results"]:
        for failure in r["failures"][:20]:
            print("release guard:", r["target"], failure)
    for problem in report["referenceProblems"]:
        print("release guard:", problem)
    for target in targets:
        if target.is_file() and target.suffix.lower() == ".zip" and not target.stem.endswith("-FAILED"):
            failed, n = target.with_name(target.stem + "-FAILED.zip"), 1
            while failed.exists():  # never overwrite or delete an earlier result
                n += 1
                failed = target.with_name(f"{target.stem}-FAILED-{n}.zip")
            target.rename(failed)
            print("release guard: renamed", target.name, "->", failed.name)
    raise SystemExit("RELEASE GUARD FAILED - do not publish; see AGENTS.md")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
