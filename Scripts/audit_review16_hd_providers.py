"""Audit actual installed HD providers and retained permission-request assets."""
from __future__ import annotations
import configparser, csv, hashlib, io, json, shutil, sys
from pathlib import Path
from PIL import Image
from bounded_archive_tool import unpack
from prepare_review16_hd_deduplication import ROOT, OLD, NEW, WORK, read_archive

def digest(blob): return hashlib.sha256(blob).hexdigest()
def size(blob): return list(Image.open(io.BytesIO(blob)).size)
def include_dirs(mod):
    ini=configparser.ConfigParser(interpolation=None)
    ini.read(mod/"mod.ini",encoding="utf-8-sig")
    return [mod/ini["Main"][f"IncludeDir{i}"].strip('"') for i in range(int(ini["Main"]["IncludeDirCount"]))]

def main():
    sys.stdout.reconfigure(encoding="utf8")
    report=json.loads((WORK/"verification.json").read_text(encoding="utf8"))
    hd=ROOT/"UnleashedRecomp-Windows/mods/UnleasHD-1440p"
    dirs=include_dirs(hd)
    sources={}
    rels=set()
    for row in report["removedUnchangedHdTextureInstances"]:
        relative=Path(row["archive"])
        relative=relative.relative_to("Compatibility/UnleasHD-1.4.2") if relative.parts[0]=="Compatibility" else Path("+Title.ar.00")
        rels.add(relative)
    for relative in sorted(rels):
        source=next((d/relative for d in dirs if (d/relative).is_file()),None)
        assert source is not None,relative
        folder=WORK/"InstalledHD"/relative.parent/source.name[:-6]
        folder.mkdir(parents=True)
        for part in [*source.parent.glob(source.name[:-6]+".ar.*"), source.with_name(source.name[:-6]+".arl")]:
            if part.is_file(): shutil.copy2(part,folder/part.name)
        unpack(folder/source.name)
        content={p.name:p.read_bytes() for p in (folder/source.name[:-6]).iterdir() if p.is_file()}
        sources[relative.as_posix()]=(source,content)
    checks=[]
    for row in report["removedUnchangedHdTextureInstances"]:
        relative=Path(row["archive"])
        is_title=relative.parts[0]=="TitleLogos"
        hd_rel=Path("+Title.ar.00") if is_title else relative.relative_to("Compatibility/UnleasHD-1.4.2")
        source,content=sources[hd_rel.as_posix()]
        data=content[row["file"]]
        if not is_title:
            assert digest(data)==row["sha256"],(source,row["file"])
            base=NEW/hd_rel
            if base.is_file(): assert row["file"] not in read_archive(base)
            compat=NEW/"Compatibility/UnleasHD-1.4.2"/hd_rel
            if compat.is_file(): assert row["file"] not in read_archive(compat)
        else:
            assert row["file"] not in read_archive(NEW/relative)
            # Game scenes use normalized UV coordinates: the atlas ratios must
            # remain identical when the lower HD mod supplies a different size.
            original=ROOT/"Build/TitleLogo-v102/Originals/Core/Title"/row["file"]
            a,b=size(data),list(Image.open(original).size)
            assert a[0]*b[1]==a[1]*b[0]
        checks.append({"removedArchive":row["archive"],"file":row["file"],
                       "provider":source.relative_to(ROOT).as_posix(),"providerSha256":digest(data),
                       "providerSize":size(data),"isTitle":is_title})
    # Enumerate the HD artwork still included for the permission request.
    initial=json.loads((ROOT/"Build/UnleasHD-Compatibility-v105-HUD2/verification.json").read_text(encoding="utf8"))
    retained=[]
    for item in initial["textures"]:
        if not item["labels"]: continue
        relative=Path("Compatibility/UnleasHD-1.4.2/Languages/English")/("+"+item["archive"]+".ar.00")
        data=read_archive(NEW/relative)[item["file"]]
        retained.append({"archive":relative.as_posix(),"file":item["file"],"category":"Korean UI",
                         "size":size(data),"sha256":digest(data),"unchangedFromReview15":True})
    extras=[
        ("Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap.ar.00","mat_worldmap_en_001.dds","Korean world map UI"),
        ("Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap.ar.00","mat_worldmap_en_002.dds","Korean world map UI"),
        ("Compatibility/UnleasHD-1.4.2/+Town_Common.ar.00","mat_talk_comon_002.dds","Korean nameplate"),
        ("Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00","mat_stage_ss_082.dds","DLC preview correction"),
    ]
    for variant in ("Korean","Custom"):
        for name in ("mat_title_001.dds","mat_title_004.dds"):
            extras.append((f"TitleLogos/{variant}/+Title.ar.00",name,"Korean title logo"))
    for path,name,category in extras:
        data=read_archive(NEW/Path(path))[name]
        assert data==read_archive(OLD/Path(path))[name]
        retained.append({"archive":path,"file":name,"category":category,"size":size(data),
                         "sha256":digest(data),"unchangedFromReview15":True})
    assert len(retained)==23
    # Verify all 7 DLC selections with the HD profile and all 5 title choices.
    # Lower HD providers must remain reachable; higher Korean edits must remain.
    combinations=[]
    ui_initial=[x for x in initial["textures"] if x["labels"]]
    for dlc in sorted((NEW/"WorldMapVariants").iterdir()):
        if not dlc.is_dir(): continue
        for logo in ("Default","Original","Japanese","Korean","Custom"):
            top=[dlc,NEW/"Compatibility/UnleasHD-1.4.2",NEW,NEW/"TitleLogos"/logo]
            for row in checks:
                rel=Path("+Title.ar.00") if row["isTitle"] else Path(row["removedArchive"]).relative_to("Compatibility/UnleasHD-1.4.2")
                providers=[(d/rel,read_archive(d/rel)) for d in top if (d/rel).is_file()]
                winner=next((p for p,c in providers if row["file"] in c),None)
                if row["isTitle"] and logo in ("Korean","Custom"):
                    assert winner==NEW/"TitleLogos"/logo/rel
                else: assert winner is None
            for row in ui_initial:
                rel=Path("Languages/English")/("+"+row["archive"]+".ar.00")
                winner=next(p/rel for p in top if (p/rel).is_file() and row["file"] in read_archive(p/rel))
                assert winner==NEW/"Compatibility/UnleasHD-1.4.2"/rel
            combinations.append({"dlc":dlc.name,"logo":logo,"uiProfile":"UnleasHD-1.4.2","passed":True})
    assert len(combinations)==35
    result={"passed":True,"version":"1.0.5-review16","installedHdProviderChecks":checks,
            "retainedModifiedUnleasHDArtwork":retained,"configurationChecks":combinations,
            "retainedKoreanHdGraphicsByteIdentical":True,"gameplayVerified":False,
            "verificationMethod":"Actual installed archive extraction plus loader-order and normalized-UV checks",
            "permissionPending":True}
    (WORK/"provider-and-permission-audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    with (WORK/"UnleasHD-permission-texture-list.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(retained[0]))
        writer.writeheader();writer.writerows(retained)
    print(json.dumps({"passed":True,"hdProviders":len(checks),"retainedModifiedHdArtwork":len(retained),
                      "configurationChecks":len(combinations),"logoSourceSizes":[x["providerSize"] for x in checks if x["isTitle"]],
                      "gameplayVerified":False}))
if __name__=="__main__":main()
