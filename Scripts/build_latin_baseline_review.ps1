$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/LatinBaseline-Audit'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
$hedgeArcPack=Join-Path $projectRoot 'Tools/HedgeArcPack/HedgeArcPack.exe'
$python=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$font=Join-Path $projectRoot 'Tools/Fonts/LINESeedKR-Rg.ttf'
$latinWidths=Get-Content -Raw (Join-Path $work 'latin-widths.json')|ConvertFrom-Json -AsHashtable
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_baseline.ps1')
$jobs=Get-Content -Raw (Join-Path $work 'fix-jobs.json')|ConvertFrom-Json
$reports=@()
foreach($job in $jobs){
 $count=0
 foreach($group in ($job.rows|Group-Object fco_file)){
  $count+=Patch-SubtitleFile $job.archive $job.folder $group.Name $group.Group
 }
 $reports+=@{archive=$job.archive;cells=$count;serializedTextVerified=$true}
 Write-Host "$($job.archive): $count subtitle cells rebuilt"
}
ConvertTo-Json -InputObject @($reports) -Depth 4|Set-Content -LiteralPath (Join-Path $work 'build-verification.json') -Encoding utf8
