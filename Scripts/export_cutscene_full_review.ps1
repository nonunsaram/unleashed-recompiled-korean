$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/CutsceneFullReview-20260914'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$index=Get-Content -Raw (Join-Path $work 'index.json')|ConvertFrom-Json
$records=@()
foreach($entry in $index){
 foreach($path in (Get-ChildItem -LiteralPath $entry.folder -Filter '*.fco')){
  $fte=Read-BinaryObject ([IO.Path]::ChangeExtension($path.FullName,'.fte')) ([libfco.FontTexture])
  $fco=Read-BinaryObject $path.FullName ([libfco.FontConverse])
  $glyphs=@(foreach($c in $fte.Characters){
   $t=$fte.Textures[[int]$c.TextureIndex]
   @{id=[int]$c.CharacterID;texture=[string]$t.Name;textureSize=@($t.Size.X,$t.Size.Y);rect=@([Math]::Round($c.TopLeft.X*$t.Size.X),[Math]::Round($c.TopLeft.Y*$t.Size.Y),[Math]::Round($c.BottomRight.X*$t.Size.X),[Math]::Round($c.BottomRight.Y*$t.Size.Y))}
  })
  $cells=@(for($i=0;$i-lt$fco.Groups.Count;$i++){for($j=0;$j-lt$fco.Groups[$i].Cells.Count;$j++){
   $c=$fco.Groups[$i].Cells[$j];@{group=$i;cell=$j;name=$c.Name;ids=@($c.Message|ForEach-Object {[int]$_});alignment=[string]$c.Alignment;mainColor=$c.MainColor;highlights=@($c.Highlights);subCells=@($c.SubCells)}
  }})
  $records+=@{archive=$entry.archive;file=$path.Name;folder=$entry.folder;fixed=$entry.fixed;glyphs=$glyphs;cells=$cells}
 }
}
ConvertTo-Json -InputObject @($records) -Depth 12|Set-Content -LiteralPath (Join-Path $work 'layouts.json') -Encoding utf8
$fco=Read-BinaryObject (Join-Path $projectRoot 'Build/Development-v102/GalleryAudit/Town_EULabo_Common/+Town_EULabo_Common/MediaRoom_list.fco') ([libfco.FontConverse])
$titles=Get-Content -Raw (Join-Path $projectRoot 'Build/Development-v102/GalleryAudit/expected.json')|ConvertFrom-Json -AsHashtable
$gallery=@(foreach($i in 201..268){@{position=$i-200;sequence=$fco.Groups[$i].Name;title=$titles[[string]$i]}})
ConvertTo-Json -InputObject @($gallery) -Depth 4|Set-Content -LiteralPath (Join-Path $work 'gallery.json') -Encoding utf8
Write-Host "Exported $($records.Count) subtitle tables and 68 gallery entries."
