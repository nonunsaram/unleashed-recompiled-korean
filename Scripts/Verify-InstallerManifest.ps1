param([Parameter(Mandatory)][string]$Installer,[Parameter(Mandatory)][string]$Manifest)
$ErrorActionPreference='Stop'
# Static PE metadata only: never load or execute the target assembly.
$stream=[IO.File]::OpenRead((Resolve-Path -LiteralPath $Installer))
$pe=[System.Reflection.PortableExecutable.PEReader]::new($stream)
try {
    $md=[System.Reflection.Metadata.PEReaderExtensions]::GetMetadataReader($pe)
    $found=0
    foreach($handle in $md.ManifestResources) {
        $resource=$md.GetManifestResource($handle)
        if($md.GetString($resource.Name) -ne 'KoreanFullManifest'){continue}
        if(-not $resource.Implementation.IsNil){throw 'Manifest resource is not embedded'}
        $found++
        $section=$pe.GetSectionData($pe.PEHeaders.CorHeader.ResourcesDirectory.RelativeVirtualAddress)
        $reader=$section.GetReader([int]$resource.Offset,$section.Length-[int]$resource.Offset)
        $length=$reader.ReadInt32()
        if($length -le 0 -or $length -gt 1048576){throw 'Manifest size invalid'}
        $embedded=$reader.ReadBytes($length)
    }
    if($found -ne 1){throw 'Expected exactly one embedded KoreanFullManifest'}
    $external=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Manifest))
    if($embedded.Length -ne $external.Length){throw 'Embedded/external manifest byte lengths differ'}
    for($i=0;$i -lt $embedded.Length;$i++) {
        if($embedded[$i] -ne $external[$i]){throw "Embedded/external manifest bytes differ at $i"}
    }
    [ordered]@{passed=$true;bytes=$embedded.Length;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($embedded)).ToLowerInvariant()} | ConvertTo-Json -Compress
} finally {$pe.Dispose();$stream.Dispose()}
