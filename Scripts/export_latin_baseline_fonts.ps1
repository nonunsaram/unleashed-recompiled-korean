param([string]$IndexFile="archive-index.json")
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/LatinBaseline-Audit'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$index=Get-Content -Raw (Join-Path $work $IndexFile)|ConvertFrom-Json
$count=0
foreach($entry in ($index|Group-Object sha256|ForEach-Object {$_.Group[0]})){
 $records=@()
 foreach($path in (Get-ChildItem -LiteralPath $entry.folder -Filter '*.fco')){
  $ftePath=[IO.Path]::ChangeExtension($path.FullName,'.fte')
  if(!(Test-Path -LiteralPath $ftePath)){throw "Missing FTE: $ftePath"}
  $fte=Read-BinaryObject $ftePath ([libfco.FontTexture]);$fco=Read-BinaryObject $path.FullName ([libfco.FontConverse])
  $glyphs=@(foreach($c in $fte.Characters){
   $t=$fte.Textures[[int]$c.TextureIndex]
   @{id=[int]$c.CharacterID;texture=[string]$t.Name;rect=@([Math]::Round($c.TopLeft.X*$t.Size.X),[Math]::Round($c.TopLeft.Y*$t.Size.Y),[Math]::Round($c.BottomRight.X*$t.Size.X),[Math]::Round($c.BottomRight.Y*$t.Size.Y))}
  })
  $cells=@(for($i=0;$i-lt$fco.Groups.Count;$i++){for($j=0;$j-lt$fco.Groups[$i].Cells.Count;$j++){
   $c=$fco.Groups[$i].Cells[$j];@{group=$i;cell=$j;ids=@($c.Message|ForEach-Object {[int]$_})}
  }})
  $records+=@{file=$path.Name;fteVersion=[int]$fte.Header.Version;glyphs=$glyphs;cells=$cells}
 }
 $layoutPath=if($IndexFile-eq'archive-index.json'){Join-Path (Split-Path $entry.folder) 'font-layouts.json'}else{Join-Path $work ('FixedLayouts/'+$entry.archive+'.json')}
 New-Item -ItemType Directory -Force (Split-Path $layoutPath)|Out-Null
 ConvertTo-Json -InputObject @($records) -Depth 8|Set-Content -LiteralPath $layoutPath -Encoding utf8
 $count++
}
Write-Host "Exported $count unique shipped subtitle font layouts."
