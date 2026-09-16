$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/FinalAudit-v104'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[libfco.FontConverse].Assembly # Force assembly resolution before reflection.
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$index=Get-Content -Raw (Join-Path $work 'archive-index.json')|ConvertFrom-Json
$layout=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$evidence=Get-Content -Raw (Join-Path $work 'reference-evidence.json')|ConvertFrom-Json
foreach($x in $evidence.preservedOriginalFiles){if((Get-FileHash -LiteralPath $x.file).Hash.ToLower()-ne$x.sha256){throw 'Preserved original changed'}}
$externalReferences=0;$dynamicIds=0;$preservedIds=0
$inputRows=Get-Content -Raw (Join-Path $projectRoot 'Build/Translation-v103/resource-input.json')|ConvertFrom-Json
$fcos=@{};$ftes=@{};$failures=[Collections.Generic.List[object]]::new();$fcoCount=0;$fteCount=0;$cells=0;$glyphs=0;$bound=0;$unbound=0
foreach($entry in $index){
 foreach($p in (Get-ChildItem -LiteralPath $entry.folder -Filter '*.fte')){
  $fte=Read-BinaryObject $p.FullName ([libfco.FontTexture]);$ftes[$p.FullName]=$fte;$fteCount++
  $ids=[Collections.Generic.HashSet[int]]::new()
  foreach($g in $fte.Characters){
   $glyphs++
   if(!$ids.Add([int]$g.CharacterID)){$failures.Add(@{kind='duplicateGlyphId';file=$p.FullName;id=[int]$g.CharacterID})}
   if($g.TextureIndex-lt0 -or $g.TextureIndex-ge$fte.Textures.Count){$failures.Add(@{kind='textureIndex';file=$p.FullName});continue}
   $v=@($g.TopLeft.X,$g.TopLeft.Y,$g.BottomRight.X,$g.BottomRight.Y)
   $badUV=$false;foreach($uv in $v){if([double]::IsNaN($uv)-or[double]::IsInfinity($uv)-or$uv-lt-0.00001-or$uv-gt1.00001){$badUV=$true}}
   if($badUV){$failures.Add(@{kind='glyphUV';file=$p.FullName;id=[int]$g.CharacterID;uv=$v})}
  }
  foreach($texture in $fte.Textures){
   if(!(Test-Path -LiteralPath (Join-Path $entry.folder ($texture.Name+'.dds')))){if($texture.Name-in$evidence.externalTextureNames){$externalReferences++}else{$failures.Add(@{kind='missingTexture';file=$p.FullName;texture=[string]$texture.Name})}}
  }
 }
 foreach($p in (Get-ChildItem -LiteralPath $entry.folder -Filter '*.fco')){
  $fco=Read-BinaryObject $p.FullName ([libfco.FontConverse]);$fcos[$p.FullName]=$fco;$fcoCount++
  $fontPath=[IO.Path]::ChangeExtension($p.FullName,'.fte')
  if(!$ftes.ContainsKey($fontPath)){$fontPath=Join-Path $entry.folder 'fte_ConverseMain.fte'}
  $font=$ftes[$fontPath];$ids=[Collections.Generic.HashSet[int]]::new();$null=$ids.Add(0)
  if($font){foreach($g in $font.Characters){$null=$ids.Add([int]$g.CharacterID)}}
  foreach($group in $fco.Groups){foreach($cell in $group.Cells){
   $cells++
   if($font){$bound++;foreach($id in $cell.Message){if(!$ids.Contains([int]$id)){if([int]$id-in$evidence.dynamicCommandIds){$dynamicIds++}elseif($p.FullName-in$evidence.preservedOriginalFiles.file-and[int]$id-in@(218,229,230)){$preservedIds++}else{$failures.Add(@{kind='unmappedMessageId';file=$p.FullName;id=[int]$id})}}}}else{$unbound++}
  }}
 }
}
$variants=@{'BaseGame'='BaseGame';'Apotos & Shamar Adventure Pack'='ApotosShamar';'Chun-nan Adventure Pack'='ChunNan';'Empire City & Adabat Adventure Pack'='AllDLC';'Holoska Adventure Pack'='Holoska';'Mazuri Adventure Pack'='Mazuri';'Spagonia Adventure Pack'='Spagonia'}
$physical=0
foreach($group in $inputRows){
 if($group.cutscene){throw 'Unexpected cutscene change in v103 input'}
 $relative=if($group.archive-eq'WorldMap'){'WorldMapVariants/'+$variants[[string]$group.package]+'/Languages/English/WorldMap.ar.00'}else{'Languages/English/+'+$group.archive+'.ar.00'}
 $entry=@($index|Where-Object archive -EQ $relative);if($entry.Count-ne1){throw "Missing archive $relative"}
 $folder=$entry[0].folder;$font=$ftes[(Join-Path $folder 'fte_ConverseMain.fte')]
 $oldCount=$font.Characters.Count-$layout.Count;$mapping=@{0="`n"}
 for($i=0;$i-lt$layout.Count;$i++){$g=$font.Characters[$oldCount+$i];if($g.CharacterID-ne200+$oldCount+$i){throw 'Unexpected common glyph map'};$mapping[[int]$g.CharacterID]=[string]$layout[$i].character}
 foreach($row in $group.rows){
  $fco=$fcos[(Join-Path $folder $row.fco_file)];$cell=$fco.Groups[[int]$row.group_index].Cells[[int]$row.cell_index]
  $actual=-join @($cell.Message|ForEach-Object {if($mapping.ContainsKey([int]$_)){$mapping[[int]$_]}else{"{GLYPH:$_}"}})
  if($actual-cne$row.korean){$failures.Add(@{kind='translationMismatch';line=$row.line_id;expected=$row.korean;actual=$actual})};$physical++
 }
}
$galleryExpected=Get-Content -Raw (Join-Path $projectRoot 'Build/Development-v102/GalleryAudit/expected.json')|ConvertFrom-Json -AsHashtable
$gallery=0
foreach($archive in @('Town_EULabo_Common','Town_PetraLabo_Common')){
 $entry=@($index|Where-Object archive -EQ "Languages/English/+$archive.ar.00")[0];$folder=$entry.folder;$font=$ftes[(Join-Path $folder 'fte_ConverseMain.fte')];$oldCount=$font.Characters.Count-$layout.Count;$mapping=@{0="`n"}
 for($i=0;$i-lt$layout.Count;$i++){$mapping[[int]$font.Characters[$oldCount+$i].CharacterID]=[string]$layout[$i].character}
 foreach($name in @('MediaRoomJP_list.fco','MediaRoom_list.fco')){
  $fco=$fcos[(Join-Path $folder $name)]
  foreach($g in 201..268){
   $actual=-join @($fco.Groups[$g].Cells[0].Message|ForEach-Object {if($mapping.ContainsKey([int]$_)){$mapping[[int]$_]}else{"{GLYPH:$_}"}})
   if(($actual-replace'\s','')-cne($galleryExpected[[string]$g]-replace'\s','')){$failures.Add(@{kind='galleryTitle';archive=$archive;group=$g})};$gallery++
  }
 }
}
$result=@{passed=$failures.Count-eq0;fcoFiles=$fcoCount;fteFiles=$fteCount;glyphRecords=$glyphs;serializedCells=$cells;fontBoundCells=$bound;externalFontCells=$unbound;currentTranslationCells=$physical;galleryTitleCells=$gallery;externalSharedTextureReferences=$externalReferences;preservedDynamicCommandInstances=$dynamicIds;knownUnrestoredOriginalGlyphInstances=$preservedIds;failures=@($failures.ToArray())}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $work 'tables-verification.json')
$result|Select-Object passed,fcoFiles,fteFiles,glyphRecords,serializedCells,fontBoundCells,externalFontCells,currentTranslationCells,galleryTitleCells|ConvertTo-Json
Write-Host "Failures: $($failures.Count)"
if($failures.Count){exit 1}
