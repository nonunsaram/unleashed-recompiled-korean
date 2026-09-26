# Apply the two confirmed names to all physical game resources, adding the missing 폴 glyph.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$mod=Join-Path $root 'Build/Development-v105b-Playtest/UnleashedKorean'
$review=Join-Path $root 'Translation/review/proper-name-audit-v105b'
$work=Join-Path $root 'Build/TwoNames-v105b/ArchiveWork'
if(Test-Path -LiteralPath $work){throw "Refusing to overwrite $work"}
New-Item -ItemType Directory -Force $work|Out-Null
$hedgeArcPack=Join-Path $root 'Tools/HedgeArcPack/HedgeArcPack.exe'
$layout=Get-Content -Raw -LiteralPath (Join-Path $root 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$decision=Get-Content -Raw -LiteralPath (Join-Path $review 'name-edits.json')|ConvertFrom-Json
$edits=@{};foreach($item in $decision.catalog_entries){$edits[[string]$item.translation_key]=$item}
$rows=@($decision.physical_cells)
[Reflection.Assembly]::LoadFrom((Join-Path $root 'Tools/Converse/net8.0/Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $root 'Tools/Converse/net8.0/libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big;$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
$writeObject=[Amicitia.IO.Binary.BinaryObjectWriter].GetMethods()|Where-Object {$_.Name-eq'WriteObject'-and$_.IsGenericMethod-and$_.GetGenericArguments().Count-eq1}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
function Arc([string]$target,[string]$answer){
 $s=[Diagnostics.ProcessStartInfo]::new();$s.FileName=$hedgeArcPack;$s.ArgumentList.Add($target)
 $s.UseShellExecute=$false;$s.RedirectStandardInput=$true;$s.RedirectStandardOutput=$true;$s.RedirectStandardError=$true;$s.CreateNoWindow=$true
 $p=[Diagnostics.Process]::Start($s);$p.StandardInput.WriteLine($answer);$p.StandardInput.Close()
 $stdout=$p.StandardOutput.ReadToEndAsync();$stderr=$p.StandardError.ReadToEndAsync();$p.WaitForExit()
 if($p.ExitCode-ne0){throw "Archive tool failed: $($stderr.Result) $($stdout.Result)"}
}
$variant=@{'BaseGame'='BaseGame';'Apotos & Shamar Adventure Pack'='ApotosShamar';'Chun-nan Adventure Pack'='ChunNan';'Empire City & Adabat Adventure Pack'='AllDLC';'Holoska Adventure Pack'='Holoska';'Mazuri Adventure Pack'='Mazuri';'Spagonia Adventure Pack'='Spagonia'}
$reports=[Collections.Generic.List[object]]::new();$changedTotal=0
foreach($g in ($rows|Group-Object package,archive)){
 $group=@($g.Group);$archive=[string]$group[0].archive;$package=[string]$group[0].package
 $isWorld=$archive-eq'WorldMap';$stem=if($isWorld){'WorldMap'}else{'+'+$archive}
 $relative=if($isWorld){"WorldMapVariants/$($variant[$package])/Languages/English"}else{'Languages/English'}
 $parent=Join-Path $mod $relative;$folder=Join-Path $work ("$($variant[$package])/$archive")
 New-Item -ItemType Directory -Force $folder|Out-Null
 $archiveParts=@(Get-ChildItem -LiteralPath $parent -Filter "$stem.ar.*" -File);if(!$archiveParts){throw "Missing $parent/$stem"}
 foreach($part in $archiveParts){Copy-Item -LiteralPath $part.FullName -Destination $folder}
 Copy-Item -LiteralPath (Join-Path $parent "$stem.arl") -Destination $folder
 Arc (Join-Path $folder "$stem.ar.00") ''
 $unpacked=Join-Path $folder $stem
 $before=@{};Get-ChildItem -LiteralPath $unpacked -File|ForEach-Object {$before[$_.Name]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
 $fte=Read-BinaryObject (Join-Path $unpacked 'fte_ConverseMain.fte') ([libfco.FontTexture]);$oldCount=$fte.Characters.Count-$layout.Count
 $ids=[Collections.Generic.Dictionary[string,int]]::new([StringComparer]::Ordinal);$ids.Add("`n",0)
 $charactersById=[Collections.Generic.Dictionary[int,string]]::new();$charactersById.Add(0,"`n")
 for($i=0;$i-lt$layout.Count;$i++){
  $c=$fte.Characters[$oldCount+$i];if($c.CharacterID-ne200+$oldCount+$i){throw 'Unexpected installed glyph map'}
  $ids.Add([string]$layout[$i].character,[int]$c.CharacterID);$charactersById.Add([int]$c.CharacterID,[string]$layout[$i].character)
 }
 function Encode([string]$text){
  $v=[Collections.Generic.List[int]]::new()
  foreach($t in [regex]::Matches($text,'\{GLYPH:(\d+)\}|[^\r]')){
   if($t.Groups[1].Success){$v.Add([int]$t.Groups[1].Value)}else{if(!$ids.ContainsKey($t.Value)){throw "Missing glyph $($t.Value)"};$v.Add($ids[$t.Value])}
  };return ,([int[]]$v.ToArray())
 }
 function Decode([int[]]$message){return -join @($message|ForEach-Object {if($charactersById.ContainsKey([int]$_)){$charactersById[[int]$_]}else{"{GLYPH:$_}"}})}
 $glyph=Get-Content -Raw -LiteralPath (Join-Path $root 'Build/TwoNames-v105b/pol-glyph.json')|ConvertFrom-Json
 if($glyph.character-ne'폴'-or$glyph.texture-ne'fte_Korean_007'){throw 'Unexpected new glyph layout'}
 if(@($fte.Textures|Where-Object Name -EQ $glyph.texture).Count-ne0){throw 'New font page already exists'}
 $newTextureIndex=$fte.Textures.Count
 $newCharacter=[libfco.Character]::new()
 $newCharacter.TextureIndex=$newTextureIndex
 $newCharacter.TopLeft=[Numerics.Vector2]::new(0,0)
 $newCharacter.BottomRight=[Numerics.Vector2]::new((28/512.0),(35/512.0))
 $newCharacter.CharacterID=200+$fte.Characters.Count
 $fte.Textures.Add([libfco.TextureEntry]::new($glyph.texture,[Numerics.Vector2]::new(512,512)))
 $fte.Characters.Add($newCharacter)
 Write-BinaryObject (Join-Path $unpacked 'fte_ConverseMain.fte') ([libfco.FontTexture]) $fte
 $verifiedFont=Read-BinaryObject (Join-Path $unpacked 'fte_ConverseMain.fte') ([libfco.FontTexture])
 if($verifiedFont.Characters.Count-ne$fte.Characters.Count-or$verifiedFont.Textures.Count-ne$fte.Textures.Count){throw 'New glyph font roundtrip failed'}
 $newGlyphId=[int]$newCharacter.CharacterID
 $ids.Add('폴',$newGlyphId);$charactersById.Add($newGlyphId,'폴')
 Copy-Item -LiteralPath (Join-Path $root 'Build/TwoNames-v105b/fte_Korean_007.dds') -Destination $unpacked
 $changedFiles=[Collections.Generic.HashSet[string]]::new();$changed=0
 foreach($fg in ($group|Group-Object fco_file)){
  $p=Join-Path $unpacked $fg.Name;$fco=Read-BinaryObject $p ([libfco.FontConverse]);$messages=@{}
  for($i=0;$i-lt$fco.Groups.Count;$i++){for($j=0;$j-lt$fco.Groups[$i].Cells.Count;$j++){$messages["$i/$j"]=($fco.Groups[$i].Cells[$j].Message-join' ')}}
  foreach($r in $fg.Group){
   $e=$edits[[string]$r.translation_key];if(!$e){throw "Unknown key $($r.translation_key)"}
   $cell=$fco.Groups[[int]$r.group_index].Cells[[int]$r.cell_index]
   $actual=Decode ([int[]]$cell.Message)
   if(($actual-replace'\s','')-ne([string]$e.before-replace'\s','')){throw "Baseline mismatch $($r.translation_key) $archive/$($fg.Name) actual=[$actual] expected=[$($e.before)]"}
   $cell.Message=Encode ([string]$e.after);$cell.MainColor.End=$cell.Message.Count-1
   $messages["$($r.group_index)/$($r.cell_index)"]=$cell.Message-join' ';$changed++
  }
  Write-BinaryObject $p ([libfco.FontConverse]) $fco
  $check=Read-BinaryObject $p ([libfco.FontConverse])
  for($i=0;$i-lt$check.Groups.Count;$i++){for($j=0;$j-lt$check.Groups[$i].Cells.Count;$j++){if(($check.Groups[$i].Cells[$j].Message-join' ')-ne$messages["$i/$j"]){throw "Changed unrelated cell: $archive/$($fg.Name)/$i/$j"}}}
  $null=$changedFiles.Add($fg.Name)
 }
 $expected=@{};Get-ChildItem -LiteralPath $unpacked -File|ForEach-Object {$hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash;$expected[$_.Name]=$hash;if(!$changedFiles.Contains($_.Name)-and$_.Name-ne'fte_ConverseMain.fte'-and$_.Name-ne'fte_Korean_007.dds'-and$before[$_.Name]-ne$hash){throw "Changed unrelated file: $archive/$($_.Name)"}}
 if($expected.Count-ne($before.Count+1)){throw "Member count changed: $archive"}
 Arc $unpacked 'hh'
 $verify=Join-Path $folder 'Verify';New-Item -ItemType Directory -Force $verify|Out-Null
 Get-ChildItem -LiteralPath $folder -Filter "$stem.ar*" -File|Copy-Item -Destination $verify
 Arc (Join-Path $verify "$stem.ar.00") ''
 foreach($name in $expected.Keys){if((Get-FileHash -LiteralPath (Join-Path $verify "$stem/$name") -Algorithm SHA256).Hash-ne$expected[$name]){throw "Roundtrip mismatch: $archive/$name"}}
 foreach($file in (Get-ChildItem -LiteralPath $folder -File|Where-Object {$_.Name-like"$stem.ar*" -or$_.Name-eq"$stem.arl"})){Copy-Item -LiteralPath $file.FullName -Destination $parent -Force}
 $changedTotal+=$changed;$reports.Add([pscustomobject]@{package=$package;archive=$archive;changed_cells=$changed;changed_fco_files=@($changedFiles);other_files_preserved=$before.Count-$changedFiles.Count;roundtrip_verified=$true})
 Write-Host "$package/$archive $changed cells verified"
}
if($changedTotal-ne$rows.Count){throw "Physical cell count mismatch $changedTotal/$($rows.Count)"}
[ordered]@{passed=$true;catalog_entries=$edits.Count;physical_cells=$changedTotal;archive_count=$reports.Count;gameplay_verified=$false;archives=$reports}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $review 'resource-verification.json') -Encoding utf8
