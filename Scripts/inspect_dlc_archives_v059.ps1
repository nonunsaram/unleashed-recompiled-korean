$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$work=Join-Path $projectRoot 'Build/HMMWorldMap-v059/Inspection'
$game=Join-Path $projectRoot 'UnleashedRecomp-Windows'
$entries=@(@{name='BaseGame';path=(Join-Path $game 'game')})+@(Get-ChildItem (Join-Path $game 'dlc') -Directory|ForEach-Object {@{name=$_.Name;path=$_.FullName}})
foreach($entry in $entries){
 foreach($stem in @('#Application')){
  $dest=Join-Path $work "$($entry.name)/$stem"
  New-Item -ItemType Directory -Force $dest|Out-Null
  foreach($suffix in @('.ar.00','.arl')){Copy-Item -LiteralPath (Join-Path $entry.path "$stem$suffix") -Destination $dest}
  $s=[Diagnostics.ProcessStartInfo]::new();$s.FileName=Join-Path $projectRoot 'Tools/HedgeArcPack/HedgeArcPack.exe';$s.ArgumentList.Add((Join-Path $dest "$stem.ar.00"));$s.UseShellExecute=$false;$s.RedirectStandardInput=$true;$s.RedirectStandardOutput=$true;$s.RedirectStandardError=$true;$s.CreateNoWindow=$true
  $p=[Diagnostics.Process]::Start($s);$p.StandardInput.WriteLine('');$p.StandardInput.Close();$o=$p.StandardOutput.ReadToEndAsync();$e=$p.StandardError.ReadToEndAsync();$p.WaitForExit();if($p.ExitCode-ne0){throw $e.Result}
  Write-Host "$($entry.name): extracted $stem"
 }
}
