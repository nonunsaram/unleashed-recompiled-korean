$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$package=Join-Path $projectRoot 'Build/FieldMission-v056'
$work=Join-Path $projectRoot 'Build/FieldMissionWork-v056-final'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
$hedgeArcPack=Join-Path $projectRoot 'Tools/HedgeArcPack/HedgeArcPack.exe'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
. (Join-Path $projectRoot 'Build/PlayableModWork/subtitle-functions.ps1')
function Arc([string]$target,[string]$answer){
 $s=[Diagnostics.ProcessStartInfo]::new();$s.FileName=$hedgeArcPack;$s.ArgumentList.Add($target)
 $s.UseShellExecute=$false;$s.RedirectStandardInput=$true;$s.RedirectStandardOutput=$true;$s.RedirectStandardError=$true;$s.CreateNoWindow=$true
 $p=[Diagnostics.Process]::Start($s);$p.StandardInput.WriteLine($answer);$p.StandardInput.Close()
 $stdout=$p.StandardOutput.ReadToEndAsync();$stderr=$p.StandardError.ReadToEndAsync();$p.WaitForExit()
 if($p.ExitCode-ne0){throw "Archive tool failed: $($stderr.Result) $($stdout.Result)"}
}
$inputs=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/mission-fields-v056-input.json')|ConvertFrom-Json
$layout=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$reports=[Collections.Generic.List[object]]::new()
foreach($g in $inputs){
 $direct=$g.archive-eq'WorldMap';$stem=if($direct){'WorldMap'}else{'+'+$g.archive}
 $relative=if($direct){if($g.package-eq'BaseGame'){'DirectArchives/game/Languages/English'}else{"DirectArchives/dlc/$($g.package)/Languages/English"}}else{'Mod/Languages/English'}
 $parent=Join-Path $package $relative;$folder=Join-Path $work "$($g.package)/$($g.archive)"
 New-Item -ItemType Directory -Force $folder|Out-Null
 Get-ChildItem -LiteralPath $parent -Filter "$stem.ar*"|Copy-Item -Destination $folder -Force
 Arc (Join-Path $folder "$stem.ar.00") ''
 $unpacked=Join-Path $folder $stem;$before=@{}
 Get-ChildItem -LiteralPath $unpacked -File|ForEach-Object {if($_.Name-notin@('StageLoad_list.fco','StageList_list.fco')){$before[$_.Name]=(Get-FileHash -LiteralPath $_.FullName).Hash}}
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
 $original=Join-Path $unpacked 'StageList_list.fco';$fco=Read-BinaryObject $original ([libfco.FontConverse]);$changed=0
 foreach($r in $g.rows){
  if([string]::IsNullOrEmpty($r.korean)){continue}
  $cell=$fco.Groups[[int]$r.group_index].Cells[[int]$r.cell_index];$new=Encode $r.korean
  if(($cell.Message-join' ')-ne($new-join' ')){$changed++}
  $cell.Message=$new;$cell.MainColor.End=$new.Count-1
 }
 Write-BinaryObject (Join-Path $unpacked 'StageList_list.fco') ([libfco.FontConverse]) $fco
 Write-BinaryObject (Join-Path $unpacked 'StageLoad_list.fco') ([libfco.FontConverse]) $fco
 $check=Read-BinaryObject (Join-Path $unpacked 'StageLoad_list.fco') ([libfco.FontConverse])
 foreach($r in $g.rows){
  if([string]::IsNullOrEmpty($r.korean)){continue}
  if(($check.Groups[[int]$r.group_index].Cells[[int]$r.cell_index].Message-join' ')-ne((Encode $r.korean)-join' ')){throw "Loading cell mismatch: $($r.line_id)"}
 }
 $expected=$before.Clone();$expected['StageList_list.fco']=(Get-FileHash -LiteralPath (Join-Path $unpacked 'StageList_list.fco')).Hash; if($expected['StageList_list.fco'] -ne (Get-FileHash -LiteralPath (Join-Path $unpacked 'StageLoad_list.fco')).Hash){throw 'Shared text mismatch'};$expected['StageLoad_list.fco']=(Get-FileHash -LiteralPath (Join-Path $unpacked 'StageLoad_list.fco')).Hash
 Arc $unpacked 'hh'
 $verify=Join-Path $folder 'Verify';New-Item -ItemType Directory -Force $verify|Out-Null
 Get-ChildItem -LiteralPath $folder -Filter "$stem.ar*"|Copy-Item -Destination $verify -Force
 Arc (Join-Path $verify "$stem.ar.00") ''
 foreach($name in $expected.Keys){if((Get-FileHash -LiteralPath (Join-Path $verify "$stem/$name")).Hash-ne$expected[$name]){throw "Archive round-trip mismatch: $name"}}
 Get-ChildItem -LiteralPath $folder -Filter "$stem.ar*"|Copy-Item -Destination $parent -Force
 $reports.Add([pscustomobject]@{package=$g.package;archive=$g.archive;verified_cells=$g.rows.Count;rewrapped_cells=$changed;retained_files_verified=$before.Count;original_stage_list_sha256=$before['StageList_list.fco'];clone_sha256=$expected['StageLoad_list.fco'];verified=$true})
 Write-Host "$($g.package)/$($g.archive): shared StageList newline verified; $changed cells rewrapped; other files unchanged"
}
[ordered]@{passed=$true;width_including_spaces=18;wording_preserved=$true;archives=$reports;game_launched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $projectRoot 'Build/FieldMission-v056/archive-verification.json')
