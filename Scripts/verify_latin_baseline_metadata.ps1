$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/LatinBaseline-Audit'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$index=Get-Content -Raw (Join-Path $work 'archive-index.json')|ConvertFrom-Json
$jobs=Get-Content -Raw (Join-Path $work 'fix-jobs.json')|ConvertFrom-Json
$count=0
foreach($job in $jobs){
 $original=($index|Where-Object {$_.version-eq'v102'-and$_.archive-eq$job.archive}).folder
 foreach($p in Get-ChildItem -LiteralPath $original -Filter '*.fco'){
  $a=Read-BinaryObject $p.FullName ([libfco.FontConverse])
  $b=Read-BinaryObject (Join-Path $job.folder $p.Name) ([libfco.FontConverse])
  if($a.Groups.Count-ne$b.Groups.Count){throw 'Group count changed'}
  for($i=0;$i-lt$a.Groups.Count;$i++){
   if($a.Groups[$i].Cells.Count-ne$b.Groups[$i].Cells.Count){throw 'Cell count changed'}
   for($j=0;$j-lt$a.Groups[$i].Cells.Count;$j++){$b.Groups[$i].Cells[$j].Message=$a.Groups[$i].Cells[$j].Message;$count++}
  }
  $aj=ConvertTo-Json -InputObject $a -Depth 30 -Compress
  $bj=ConvertTo-Json -InputObject $b -Depth 30 -Compress
  if($aj-cne$bj){throw "Non-message FCO data changed: $($job.archive)/$($p.Name)"}
 }
}
@{passed=$true;cells=$count;nonMessageFcoPropertiesUnchanged=$true}|ConvertTo-Json|Set-Content (Join-Path $work 'metadata-verification.json')
Write-Host "Verified all non-message FCO properties for $count cells."
