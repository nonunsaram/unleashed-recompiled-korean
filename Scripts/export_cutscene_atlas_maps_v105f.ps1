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
$rows=Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Build/Review6-ResolutionSplit/cutscene-physical.json')|ConvertFrom-Json
$maps=[Collections.Generic.List[object]]::new()
$mismatches=[Collections.Generic.List[object]]::new()
foreach($group in ($rows|Group-Object archive)){
 $archive=[string]$group.Name
 $dir=Join-Path $root "Build/FinalAudit-v104/Archives/Inspire/subtitle/English/+$archive/+$archive"
 foreach($fileGroup in ($group.Group|Group-Object fco_file)){
  $fcoFile=[string]$fileGroup.Name
  $stem=[IO.Path]::GetFileNameWithoutExtension($fcoFile)
  $fte=Read-BinaryObject (Join-Path $dir "$stem.fte") ([libfco.FontTexture])
  $fco=Read-BinaryObject (Join-Path $dir $fcoFile) ([libfco.FontConverse])
  $byId=@{}
  foreach($glyph in $fte.Characters){
   $id=[int]$glyph.CharacterID
   if($byId.ContainsKey($id)){throw "Duplicate glyph ID: $archive/$fcoFile/$id"}
   $byId[$id]=$glyph
  }
  $entriesByTexture=@{}
  foreach($row in $fileGroup.Group){
   if([string]::IsNullOrEmpty([string]$row.korean)){continue}
   $message=@($fco.Groups[[int]$row.group_index].Cells[[int]$row.cell_index].Message)
   $letters=@(([string]$row.korean).ToCharArray())
   if($message.Count-ne$letters.Count){
    $mismatches.Add([ordered]@{archive=$archive;fco_file=$fcoFile;group_index=$row.group_index;cell_index=$row.cell_index;ids=$message.Count;characters=$letters.Count})
    continue
   }
   for($i=0;$i-lt$letters.Count;$i++){
    $letter=[string]$letters[$i]
    $id=[int]$message[$i]
    if($letter-eq"`n"){
     if($id-ne0){throw "Newline ID mismatch: $archive/$fcoFile"}
     continue
    }
    if(-not$byId.ContainsKey($id)){throw "Unknown glyph ID: $archive/$fcoFile/$id"}
    $glyph=$byId[$id]
    $texture=$fte.Textures[[int]$glyph.TextureIndex]
    $textureName="$($texture.Name).dds"
    $width=[int]$texture.Size.X;$height=[int]$texture.Size.Y
    if(-not(Test-Path -LiteralPath (Join-Path $dir $textureName) -PathType Leaf)){throw "Missing texture: $archive/$textureName"}
    if($width-ne512-or$height-ne512){throw "Unexpected texture size: $archive/$textureName"}
    $rect=@(
     [int][Math]::Round([double]$glyph.TopLeft.X*$width),
     [int][Math]::Round([double]$glyph.TopLeft.Y*$height),
     [int][Math]::Round([double]$glyph.BottomRight.X*$width),
     [int][Math]::Round([double]$glyph.BottomRight.Y*$height)
    )
    if(-not$entriesByTexture.ContainsKey($textureName)){$entriesByTexture[$textureName]=[Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)}
    $atlas=$entriesByTexture[$textureName]
    if($atlas.Contains($letter)){
     if([int]$atlas[$letter].id-ne$id){throw "Inconsistent glyph ID: $archive/$fcoFile/$letter"}
    }else{$atlas.Add($letter,[ordered]@{character=$letter;id=$id;rect=$rect})}
   }
  }
  foreach($textureName in ($entriesByTexture.Keys|Sort-Object)){
   $maps.Add([ordered]@{archive=$archive;stem=$stem;texture=$textureName;size=@(512,512);entries=@($entriesByTexture[$textureName].Values)})
  }
 }
 Write-Output "$archive : $(@($maps|Where-Object {$_.archive-eq$archive}).Count) translated pages"
}
$output=Join-Path $root 'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json'
ConvertTo-Json -InputObject $maps -Depth 8|Set-Content -LiteralPath $output -Encoding UTF8
$missing=Join-Path $root 'Build/Review6-ResolutionSplit/cutscene-map-mismatches.json'
ConvertTo-Json -InputObject $mismatches -Depth 5|Set-Content -LiteralPath $missing -Encoding UTF8
Write-Output "Pages=$($maps.Count) mismatches=$($mismatches.Count)"
