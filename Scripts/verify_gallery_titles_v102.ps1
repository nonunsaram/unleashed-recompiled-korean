# Read the four shipped gallery tables against the reviewed 68 video titles.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$python=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $python (Join-Path $PSScriptRoot 'prepare_gallery_inputs_v102.py')
if($LASTEXITCODE-ne0){throw 'Gallery input preparation failed'}
$work=Join-Path $projectRoot 'Build/Development-v102/GalleryAudit'
$converseDir=Join-Path $projectRoot 'Tools/Converse/net8.0'
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'Amicitia.IO.dll'))|Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $converseDir 'libfco.dll'))|Out-Null
$endianness=[Amicitia.IO.Binary.Endianness]::Big
$encoding=[Text.Encoding]::UTF8
$readObject=[Amicitia.IO.Binary.BinaryObjectReader].GetMethods()|Where-Object {$_.Name-eq'ReadObject'-and$_.IsGenericMethod-and$_.GetParameters().Count-eq0}|Select-Object -First 1
. (Join-Path $PSScriptRoot 'subtitle_resource_functions_v102.ps1')
$layout=Get-Content -Raw (Join-Path $projectRoot 'Build/PlayableModWork/common-atlas.json')|ConvertFrom-Json
$expected=Get-Content -Raw (Join-Path $work 'expected.json')|ConvertFrom-Json -AsHashtable
$results=@();$failures=@()
foreach($archive in @('Town_EULabo_Common','Town_PetraLabo_Common')){
 $folder=Join-Path $work "$archive/+$archive"
 $fte=Read-BinaryObject (Join-Path $folder 'fte_ConverseMain.fte') ([libfco.FontTexture])
 $oldCount=$fte.Characters.Count-$layout.Count
 $glyphs=@{0="`n"}
 for($i=0;$i-lt$layout.Count;$i++){
  $c=$fte.Characters[$oldCount+$i]
  if($c.CharacterID-ne200+$oldCount+$i){throw 'Unexpected font glyph mapping'}
  $glyphs[[int]$c.CharacterID]=[string]$layout[$i].character
 }
 foreach($name in @('MediaRoomJP_list.fco','MediaRoom_list.fco')){
  $fco=Read-BinaryObject (Join-Path $folder $name) ([libfco.FontConverse])
  foreach($g in 201..268){
   $actual=-join @($fco.Groups[$g].Cells[0].Message|ForEach-Object {if($glyphs.ContainsKey([int]$_)){$glyphs[[int]$_]}else{"{GLYPH:$_}"}})
   $entry=@{archive=$archive;file=$name;group=$g;actual=$actual;expected=$expected[[string]$g]}
   $entry.passed=($actual-replace'\s','')-ceq($expected[[string]$g]-replace'\s','')
   $results+=,$entry
   if(!$entry.passed){$failures+=,$entry}
  }
 }
}
@{passed=$failures.Count-eq0;cells=$results.Count;failures=$failures;results=$results;gameLaunched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $work 'verification.json')
if($failures.Count){throw "$($failures.Count) gallery title mismatches; see verification.json"}
Write-Host "Verified $($results.Count) gallery title cells across both labs and both region tables."
