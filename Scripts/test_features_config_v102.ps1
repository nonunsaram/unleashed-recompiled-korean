# Exercise the actual HMM schema loader, INI parser and save code in isolation.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$sourceRoot=Join-Path $projectRoot 'Analysis/ThirdPartySurvey/HedgeModManager/Source'
$work=Join-Path $projectRoot 'Build/Development-v102/HMMConfigTest'
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
$modRoot=Join-Path $projectRoot 'Build/Development-v102/UnleashedKorean'
$schemaPath=Join-Path $modRoot 'ConfigSchema.json'
$base=[HedgeModManager.UI.Models.ModConfig]::LoadSchemaFile($schemaPath).GetAwaiter().GetResult()
foreach($dlc in $base.Enums['WorldMapVariant']){
 foreach($compat in $base.Enums['UnleasHDCompatibility']){
  foreach($logo in $base.Enums['TitleLogoVariant']){
   $copy=Join-Path $work ("choice-$($results.Count).ini")
   Copy-Item -LiteralPath (Join-Path $modRoot 'mod.ini') -Destination $copy -Force
   $schema=[HedgeModManager.UI.Models.ModConfig]::LoadSchemaFile($schemaPath).GetAwaiter().GetResult()
   $schema.Load($copy).GetAwaiter().GetResult()|Out-Null
   $values=@{IncludeDir0=[string]$dlc.Value;IncludeDir2=[string]$compat.Value;IncludeDir3=[string]$logo.Value}
   foreach($group in $schema.Groups){
    foreach($element in $group.Elements){
     if($values.ContainsKey($element.Name)){
      if($group.Name-ne'Main'){throw 'IncludeDir configuration outside Main'}
      $element.Value=$values[$element.Name]
     }
    }
   }
   $schema.Save($copy,$true).GetAwaiter().GetResult()|Out-Null
   $reload=[HedgeModManager.UI.Models.ModConfig]::LoadSchemaFile($schemaPath).GetAwaiter().GetResult()
   $reload.Load($copy).GetAwaiter().GetResult()|Out-Null
   $ini=[HedgeModManager.Text.Ini]::FromFile($copy)
   foreach($key in $values.Keys){
    if([string]$ini.Groups['Main'][$key]-cne$values[$key]){throw "Incorrect loader section: $key"}
    $element=$reload.Groups[0].Elements|Where-Object Name -EQ $key
    if([string]$element.Value-cne$values[$key]){throw "Reload mismatch: $key"}
    if(!(Test-Path -LiteralPath (Join-Path $modRoot $values[$key]))){throw "Selected folder missing: $key"}
   }
   if($ini.Groups['Main']['IncludeDirCount']-ne4 -or $ini.Groups['Main']['IncludeDir1']-ne'.'){throw 'Common assets lost'}
   if($ini.Groups.ContainsKey('Compatibility')){throw 'Obsolete non-loader section remains'}
   $results+=@{dlc=$dlc.Value;compatibility=$compat.Value;logo=$logo.Value}
  }
 }
}
@{passed=$true;implementation='Actual HMM ModConfig.Load/Save and Ini';sources=$sources;choices=$results;game_launched=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding utf8 (Join-Path $projectRoot 'Build/Development-v102/hmm-config-verification.json')
Write-Host "HMM source configuration round-trip verified for $($results.Count) combinations."
