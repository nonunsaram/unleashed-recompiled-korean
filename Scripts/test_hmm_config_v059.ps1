# Exercise the actual HMM schema loader, INI parser and save code in isolation.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$sourceRoot=Join-Path $projectRoot 'Analysis/ThirdPartySurvey/HedgeModManager/Source'
$work=Join-Path $projectRoot 'Build/HMMWorldMap-v059/HMMConfigTest'
New-Item -ItemType Directory -Force $work|Out-Null
$names=@('Libraries/HedgeModManager.Text/Ini.cs','Libraries/HedgeModManager.Text/LineReader.cs','HedgeModManager.UI/Models/ModConfig.cs','HedgeModManager.UI/Converters/Json/StringDynamicConverter.cs','HedgeModManager.UI/Converters/Json/StringDoubleConverter.cs')
$paths=@();$sources=@()
foreach($name in $names){
 $source=Join-Path $sourceRoot $name;$dest=Join-Path $work ([IO.Path]::GetFileName($name))
 $text="#nullable enable`nusing System;`nusing System.IO;`nusing System.Linq;`nusing System.Collections.Generic;`nusing System.Threading.Tasks;`n"+[IO.File]::ReadAllText($source)
 [IO.File]::WriteAllText($dest,$text);$paths+=@($dest);$sources+=@(@{file=$name;sha256=(Get-FileHash -LiteralPath $source).Hash})
}
$stub=Join-Path $work 'ProgramStub.cs'
[IO.File]::WriteAllText($stub,@'
namespace HedgeModManager.UI {
 public static class Program {
  public static readonly System.Text.Json.JsonSerializerOptions JsonSerializerOptions = new() {
   PropertyNameCaseInsensitive = true, AllowTrailingCommas = true,
   ReadCommentHandling = System.Text.Json.JsonCommentHandling.Skip, WriteIndented = true
  };
 }
}
'@)
$paths+=@($stub)
Add-Type -Path $paths -IgnoreWarnings
$results=@()
foreach($edition in @('Basic','Full')){
 $modRoot=Join-Path $projectRoot "Build/GameBanana-1.0.0/$edition/UnleashedKorean"
 $schemaPath=Join-Path $modRoot 'ConfigSchema.json'
 $schema=[HedgeModManager.UI.Models.ModConfig]::LoadSchemaFile($schemaPath).GetAwaiter().GetResult()
 if($schema.IniFile-ne'mod.ini'){throw 'Config must address mod.ini'}
 foreach($option in $schema.Enums['WorldMapVariant']){
  $copy=Join-Path $work ($edition+'-'+([string]$option.Value).Replace('/','_')+'.ini')
  Copy-Item -LiteralPath (Join-Path $modRoot 'mod.ini') -Destination $copy -Force
  $schema.Load($copy).GetAwaiter().GetResult()|Out-Null
  $element=$schema.Groups[0].Elements[0]
  $element.Value=$option.Value
  $schema.Save($copy,$true).GetAwaiter().GetResult()|Out-Null
  $reload=[HedgeModManager.UI.Models.ModConfig]::LoadSchemaFile($schemaPath).GetAwaiter().GetResult()
  $reload.Load($copy).GetAwaiter().GetResult()|Out-Null
  if([string]$reload.Groups[0].Elements[0].Value-cne[string]$option.Value){throw 'Schema selection did not persist'}
  $ini=[HedgeModManager.Text.Ini]::FromFile($copy)
  if([string]$ini.Groups['Main']['IncludeDir0']-cne[string]$option.Value){throw 'Incorrect include directory'}
  if($ini.Groups['Main']['IncludeDirCount']-ne2 -or $ini.Groups['Main']['IncludeDir1']-ne'.'){throw 'Common include directory lost'}
  if($ini.Groups['Main']['ID']-ne'unleashed-recomp-korean'){throw 'Mod identity changed'}
  $asset=Join-Path $modRoot ([string]$option.Value+'/Languages/English/WorldMap.ar.00')
  if(!(Test-Path -LiteralPath $asset)){throw 'Selected archive is missing'}
  $results+=@(@{edition=$edition;option=[string]$option.Value;archive_sha256=(Get-FileHash -LiteralPath $asset).Hash})
 }
}
@{passed=$true;implementation='Actual HMM ModConfig.Load/Save and Ini source, compiled with implicit usings and Program JSON options stub';sources=$sources;choices=$results;hmm_gui_launched=$false;game_launched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $projectRoot 'Build/HMMWorldMap-v059/hmm-config-verification.json')
Write-Host "HMM source configuration round-trip verified for $($results.Count) edition/variant choices."
