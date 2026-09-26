$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$libs=Join-Path $root 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $libs 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $libs 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big
$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$entries=@((Get-Content -Raw -Encoding UTF8 (Join-Path $root 'Translation/review/unleashhd-v105/residual-conflicts.json')|ConvertFrom-Json).entries|Where-Object {$_.file-like'fte_ConverseMain_*.dds'})
$report=[Collections.Generic.List[object]]::new()
foreach($group in ($entries|Group-Object archive)){
 $archive=[string]$group.Name
 $dir=Join-Path $root "Build/Review4-FontInspection/$archive/+$archive"
 $fte=Read-BinaryObject (Join-Path $dir 'fte_ConverseMain.fte') ([libfco.FontTexture])
 $indices=[Collections.Generic.HashSet[int]]::new()
 for($i=0;$i-lt$fte.Textures.Count;$i++){
  if($group.Group.file-contains("$($fte.Textures[$i].Name).dds")){$null=$indices.Add($i)}
 }
 if($indices.Count-ne$group.Count){throw "Atlas index mismatch: $archive"}
 $ids=[Collections.Generic.HashSet[int]]::new()
 foreach($glyph in $fte.Characters){if($indices.Contains([int]$glyph.TextureIndex)){$null=$ids.Add([int]$glyph.CharacterID)}}
 $files=[Collections.Generic.List[object]]::new()
 foreach($file in (Get-ChildItem -LiteralPath $dir -Filter '*.fco' -File)){
  $fco=Read-BinaryObject $file.FullName ([libfco.FontConverse])
  $total=0;$matches=0
  foreach($converse in $fco.Groups){foreach($cell in $converse.Cells){foreach($id in $cell.Message){
   if([int]$id-ne0){$total++;if($ids.Contains([int]$id)){$matches++}}
  }}}
  if($matches-gt0){$files.Add([ordered]@{file=$file.Name;matchingIds=$matches;totalIds=$total})}
 }
 $report.Add([ordered]@{archive=$archive;originalPageCount=$group.Count;originalGlyphIds=$ids.Count;overlappingFcoFiles=@($files)})
 Write-Output "$archive : original ID overlaps in $($files.Count) FCO files"
}
$output=Join-Path $root 'Translation/review/unleashhd-v105d/original-page-usage.json'
ConvertTo-Json -InputObject $report -Depth 8|Set-Content -LiteralPath $output -Encoding UTF8
