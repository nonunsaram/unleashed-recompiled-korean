$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $projectRoot 'Build/PlayableModWork/subtitle-functions.ps1')
$inputs=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/mission-fields-v056-input.json')|ConvertFrom-Json
$layout=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$reports=@();$count=0
foreach($g in $inputs){
 $direct=$g.archive-eq'WorldMap';$stem=if($direct){'WorldMap'}else{'+'+$g.archive}
 $relative=if($direct){if($g.package-eq'BaseGame'){'DirectArchives/game/Languages/English'}else{"DirectArchives/dlc/$($g.package)/Languages/English"}}else{'Mod/Languages/English'}
 $source=Join-Path $projectRoot "Build/FieldMission-v056/$relative"
 $folder=Join-Path $projectRoot "Build/Separation-v058/Fields/$($g.package)/$($g.archive)"
 New-Item -ItemType Directory -Force $folder|Out-Null
 Get-ChildItem -LiteralPath $source -Filter "$stem.ar*"|Copy-Item -Destination $folder
 $s=[Diagnostics.ProcessStartInfo]::new();$s.FileName=Join-Path $projectRoot 'Tools/HedgeArcPack/HedgeArcPack.exe';$s.ArgumentList.Add((Join-Path $folder "$stem.ar.00"));$s.UseShellExecute=$false;$s.RedirectStandardInput=$true;$s.RedirectStandardOutput=$true;$s.RedirectStandardError=$true;$s.CreateNoWindow=$true
 $p=[Diagnostics.Process]::Start($s);$p.StandardInput.WriteLine('');$p.StandardInput.Close();$o=$p.StandardOutput.ReadToEndAsync();$e=$p.StandardError.ReadToEndAsync();$p.WaitForExit();if($p.ExitCode-ne0){throw $e.Result}
 $unpacked=Join-Path $folder $stem
 $fte=Read-BinaryObject (Join-Path $unpacked 'fte_ConverseMain.fte') ([libfco.FontTexture])
 $oldCount=$fte.Characters.Count-$layout.Count
 $ids=[Collections.Generic.Dictionary[string,int]]::new([StringComparer]::Ordinal);$ids.Add("`n",0)
 for($i=0;$i-lt$layout.Count;$i++){$ids.Add([string]$layout[$i].character,[int]$fte.Characters[$oldCount+$i].CharacterID)}
 $fco=Read-BinaryObject (Join-Path $unpacked 'StageList_list.fco') ([libfco.FontConverse])
 $roleCounts=@{}
 foreach($r in $g.rows){
  if([string]::IsNullOrEmpty($r.korean)-or$r.cell-notin@('NameTag','Explanation','Hint','Worldmap')){continue}
  $group=$fco.Groups[[int]$r.group_index]
  $cells=@($group.Cells|Where-Object {$_.Name-ceq$r.cell})
  if($cells.Count-ne1){throw "Ambiguous field name: $($r.line_id) $($r.cell)"}
  $cell=$cells[0]
  if($group.Cells[[int]$r.cell_index].Name-cne$r.cell){throw 'Index/name mismatch'}
  $v=[Collections.Generic.List[int]]::new()
  foreach($t in [regex]::Matches($r.korean,'\{GLYPH:(\d+)\}|[^\r]')){if($t.Groups[1].Success){$v.Add([int]$t.Groups[1].Value)}else{$v.Add($ids[$t.Value])}}
  if(($cell.Message-join' ')-ne($v-join' ')){throw "Text mismatch: $($r.line_id)"}
  $count++;$roleCounts[$r.cell]++
 }
 $reports+=@{package=$g.package;archive=$g.archive;roles=$roleCounts;sha256=(Get-FileHash (Join-Path $source "$stem.ar.00")).Hash}
}
@{passed=$true;physical_cells=$count;field_selection='Cell.Name';archives=$reports;game_launched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $projectRoot 'Build/Separation-v058/field-verification.json')
Write-Host "Verified $count named cells in $($reports.Count) archives."
