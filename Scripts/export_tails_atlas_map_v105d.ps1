$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$converse=Join-Path $root 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converse 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converse 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big
$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$folder=Join-Path $root 'Build/Review4-FontInspection/ExStageTails_Common/+ExStageTails_Common'
$rows=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Build/Review4-RingEnergy/event-lines.json')|ConvertFrom-Json
$result=[Collections.Generic.List[object]]::new()
foreach($stem in @('evex_ex00_event','evex_ex01_event')){
 $fte=Read-BinaryObject (Join-Path $folder "$stem.fte") ([libfco.FontTexture])
 $fco=Read-BinaryObject (Join-Path $folder "$stem.fco") ([libfco.FontConverse])
 $index=-1
 for($i=0;$i-lt$fte.Textures.Count;$i++){if($fte.Textures[$i].Name-eq"${stem}_000"){$index=$i;break}}
 if($index-lt0){throw "Missing atlas $stem"}
 $texture=$fte.Textures[$index]
 if([int]$texture.Size.X-ne512-or[int]$texture.Size.Y-ne512){throw "Unexpected atlas size $stem"}
 $byId=@{}
 foreach($item in $fte.Characters){
  $id=[int]$item.CharacterID
  if($byId.ContainsKey($id)){throw "Repeated FTE ID $stem/$id"}
  $byId[$id]=$item
 }
 $byGlyph=[Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
 foreach($row in @($rows|Where-Object {$_.fco_file-eq"$stem.fco"})){
  $message=@($fco.Groups[[int]$row.group_index].Cells[[int]$row.cell_index].Message)
  $letters=@(([string]$row.korean).ToCharArray())
  if($message.Count-ne$letters.Count){throw "Message length mismatch $stem"}
  for($j=0;$j-lt$letters.Count;$j++){
   $glyph=[string]$letters[$j]
   $id=[int]$message[$j]
   if($glyph-eq"`n"){
    if($id-ne0){throw 'Newline ID mismatch'}
    continue
   }
   if(-not$byId.ContainsKey($id)){throw "Unknown ID $stem/$id"}
   $entry=$byId[$id]
   if([int]$entry.TextureIndex-ne$index){throw "Wrong texture index $stem/$id"}
   $rect=@(
    [int][Math]::Round([double]$entry.TopLeft.X*512),
    [int][Math]::Round([double]$entry.TopLeft.Y*512),
    [int][Math]::Round([double]$entry.BottomRight.X*512),
    [int][Math]::Round([double]$entry.BottomRight.Y*512)
   )
   if($byGlyph.Contains($glyph)){
    if([int]$byGlyph[$glyph].id-ne$id){throw "Inconsistent glyph ID $stem/$glyph"}
   }else{$byGlyph.Add($glyph,[ordered]@{character=$glyph;id=$id;rect=$rect})}
  }
 }
 $result.Add([ordered]@{stem=$stem;texture="${stem}_000.dds";size=@(512,512);entries=@($byGlyph.Values)})
}
$output=Join-Path $root 'Build/Review4-RingEnergy/tails-atlas-map.json'
ConvertTo-Json -InputObject $result -Depth 8|Set-Content -LiteralPath $output -Encoding utf8
Write-Output "Saved $output with $($result.Count) atlases"
