# Rebuild only the reviewed dialogue archives, keeping all v1.0.0 UI/mission assets.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot ('Build/Translation-v101/ArchiveWork-'+[Guid]::NewGuid().ToString('N'))
$output=Join-Path $projectRoot 'Build/Translation-v101/Resources'
$baseline=Join-Path $projectRoot 'Build/GameBanana-1.0.0/Basic/UnleashedKorean'
$archiveRoot=Join-Path $projectRoot 'Analysis/Full-Text-Extraction/Archives'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
$hedgeArcPack=Join-Path $projectRoot 'Tools/HedgeArcPack/HedgeArcPack.exe'
$python=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$font=Join-Path $projectRoot 'Tools/Fonts/LINESeedKR-Rg.ttf'
New-Item -ItemType Directory -Force $work,$output|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions.ps1')
function Arc([string]$target,[string]$answer){
 $s=[Diagnostics.ProcessStartInfo]::new();$s.FileName=$hedgeArcPack;$s.ArgumentList.Add($target)
 $s.UseShellExecute=$false;$s.RedirectStandardInput=$true;$s.RedirectStandardOutput=$true;$s.RedirectStandardError=$true;$s.CreateNoWindow=$true
 $p=[Diagnostics.Process]::Start($s);$p.StandardInput.WriteLine($answer);$p.StandardInput.Close()
 $stdout=$p.StandardOutput.ReadToEndAsync();$stderr=$p.StandardError.ReadToEndAsync();$p.WaitForExit()
 if($p.ExitCode-ne0){throw "Archive tool failed: $($stderr.Result) $($stdout.Result)"}
}
$inputs=Get-Content -Raw (Join-Path $projectRoot 'Build/Translation-v101/resource-input.json')|ConvertFrom-Json
$layout=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$reports=[Collections.Generic.List[object]]::new();$patches=[Collections.Generic.List[object]]::new()
foreach($g in $inputs){
 $stem='+'+$g.archive
 $relative=if($g.cutscene){'Inspire/subtitle/English'}else{'Languages/English'}
 $parent=Join-Path $baseline $relative;$folder=Join-Path $work "$($g.package)/$($g.archive)"
 New-Item -ItemType Directory -Force $folder|Out-Null
 Get-ChildItem -LiteralPath $parent -Filter "$stem.ar*"|Copy-Item -Destination $folder
 Arc (Join-Path $folder "$stem.ar.00") ''
 $unpacked=Join-Path $folder $stem;$before=@{}
 Get-ChildItem -LiteralPath $unpacked -File|ForEach-Object {$before[$_.Name]=(Get-FileHash -LiteralPath $_.FullName).Hash}
 $allowed=[Collections.Generic.HashSet[string]]::new();$changed=0
 if($g.cutscene){
  foreach($fg in ($g.rows|Group-Object fco_file)){
   $fcoFile=$fg.Name;$fcoStem=[IO.Path]::GetFileNameWithoutExtension($fcoFile)
   $jp=Join-Path $archiveRoot "$($g.source_kind)/$($g.package)/Japanese/$($g.archive)/$($g.archive)"
   Copy-Item -LiteralPath (Join-Path $jp $fcoFile),(Join-Path $jp "$fcoStem.fte") -Destination $unpacked -Force
   Get-ChildItem -LiteralPath $jp -Filter "${fcoStem}_*.dds"|Copy-Item -Destination $unpacked -Force
   $null=$allowed.Add($fcoFile);$null=$allowed.Add("$fcoStem.fte")
   Get-ChildItem -LiteralPath $unpacked -Filter "${fcoStem}_*.dds"|ForEach-Object {$null=$allowed.Add($_.Name)}
   $patched=@(Patch-SubtitleFile $g.archive $unpacked $fcoFile $fg.Group)
   $changed+=@($fg.Group|Where-Object {$_.before-ne$_.korean}).Count
  }
 }else{
  $fte=Read-BinaryObject (Join-Path $unpacked 'fte_ConverseMain.fte') ([libfco.FontTexture])
  $oldCount=$fte.Characters.Count-$layout.Count
  $ids=[Collections.Generic.Dictionary[string,int]]::new([StringComparer]::Ordinal);$ids.Add("`n",0)
  for($i=0;$i-lt$layout.Count;$i++){
   $c=$fte.Characters[$oldCount+$i];if($c.CharacterID-ne200+$oldCount+$i){throw 'Unexpected installed glyph map'}
   $ids.Add([string]$layout[$i].character,[int]$c.CharacterID)
  }
  function Encode([string]$text){
   $v=[Collections.Generic.List[int]]::new()
   foreach($t in [regex]::Matches($text,'\{GLYPH:(\d+)\}|[^\r]')){
    if($t.Groups[1].Success){$v.Add([int]$t.Groups[1].Value)}else{$v.Add($ids[$t.Value])}
   };return ,([int[]]$v.ToArray())
  }
  foreach($fg in ($g.rows|Group-Object fco_file)){
   $p=Join-Path $unpacked $fg.Name;$fco=Read-BinaryObject $p ([libfco.FontConverse]);$messages=@{}
   for($i=0;$i-lt$fco.Groups.Count;$i++){for($j=0;$j-lt$fco.Groups[$i].Cells.Count;$j++){
    $messages["$i/$j"]=($fco.Groups[$i].Cells[$j].Message-join' ')
   }}
   foreach($r in $fg.Group){
    $cell=$fco.Groups[[int]$r.group_index].Cells[[int]$r.cell_index]
    if(($cell.Message-join' ')-ne((Encode $r.before)-join' ')){throw "Baseline text mismatch: $($r.translation_key)"}
    $cell.Message=Encode $r.korean;$cell.MainColor.End=$cell.Message.Count-1
    $messages["$($r.group_index)/$($r.cell_index)"]=$cell.Message-join' ';$changed++
   }
   Write-BinaryObject $p ([libfco.FontConverse]) $fco
   $check=Read-BinaryObject $p ([libfco.FontConverse])
   for($i=0;$i-lt$check.Groups.Count;$i++){for($j=0;$j-lt$check.Groups[$i].Cells.Count;$j++){
    if(($check.Groups[$i].Cells[$j].Message-join' ')-ne$messages["$i/$j"]){throw "Changed unrelated cell: $($fg.Name)/$i/$j"}
   }}
   $null=$allowed.Add($fg.Name)
  }
 }
 $expected=@{}
 Get-ChildItem -LiteralPath $unpacked -File|ForEach-Object {
  $hash=(Get-FileHash -LiteralPath $_.FullName).Hash;$expected[$_.Name]=$hash
  if(-not$allowed.Contains($_.Name)-and$before[$_.Name]-ne$hash){throw "Changed unrelated file: $($_.Name)"}
 }
 if($expected.Count-ne$before.Count){throw 'Archive member count changed'}
 Arc $unpacked 'hh'
 $verify=Join-Path $folder 'Verify';New-Item -ItemType Directory -Force $verify|Out-Null
 Get-ChildItem -LiteralPath $folder -Filter "$stem.ar*"|Copy-Item -Destination $verify
 Arc (Join-Path $verify "$stem.ar.00") ''
 foreach($name in $expected.Keys){if((Get-FileHash -LiteralPath (Join-Path $verify "$stem/$name")).Hash-ne$expected[$name]){throw "Archive round-trip mismatch: $name"}}
 $out=Join-Path $output $relative;New-Item -ItemType Directory -Force $out|Out-Null
 Get-ChildItem -LiteralPath $folder -Filter "$stem.ar*"|ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination $out -Force
  $patches.Add([pscustomobject]@{relative="$relative/$($_.Name)";before_sha256=(Get-FileHash (Join-Path $parent $_.Name)).Hash.ToLower();after_sha256=(Get-FileHash $_.FullName).Hash.ToLower()})
 }
 $reports.Add([pscustomobject]@{archive=$g.archive;package=$g.package;changed_physical_cells=$changed;verified_rows=$g.rows.Count;retained_files=$before.Count-$allowed.Count;roundtrip_verified=$true})
 Write-Host "$($g.archive): $changed changed cells, archive round-trip verified"
}
[ordered]@{passed=$true;archives=$reports;patches=$patches;game_launched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $projectRoot 'Build/Translation-v101/resource-verification.json')
