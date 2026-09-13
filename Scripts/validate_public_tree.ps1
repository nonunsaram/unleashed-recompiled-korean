[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$errors = [System.Collections.Generic.List[string]]::new()
$warnings = [System.Collections.Generic.List[string]]::new()

function Add-Error([string]$message) {
    $errors.Add($message)
}

$required = @(
    'README.md',
    'BUILDING.md',
    'LICENSE.md',
    'THIRD_PARTY_NOTICES.md',
    'SOURCE_SELECTION.md',
    '.gitignore',
    'Release/SHA256SUMS.txt',
    'Scripts/KoreanSupportSetup.cs',
    'Scripts/package_hmm_release_v059.py',
    'Scripts/verify_hmm_release_v059.py',
    'Patches/unleashed-recomp-v1.0.3-korean.patch',
    'Patches/modified/UnleashedRecomp/ui/button_guide.cpp',
    'Patches/modified/UnleashedRecomp/user/config.cpp',
    'Licenses/UnleashedRecomp-GPL-3.0.txt',
    'Licenses/MIT.txt',
    'Licenses/LINE-Seed-OFL.txt',
    'Tools/Fonts/LINESeedKR-Rg.ttf',
    'Tools/Fonts/LINESeedKR-Bd.ttf'
)

foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $root $relative) -PathType Leaf)) {
        Add-Error "필수 파일 누락: $relative"
    }
}

$all = @(Get-ChildItem -LiteralPath $root -Recurse -Force)
$files = @($all | Where-Object { -not $_.PSIsContainer -and $_.FullName -notmatch '[\\/]\.git[\\/]' })

foreach ($entry in $all) {
    if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        Add-Error "재분석 지점/심볼릭 링크 발견: $($entry.FullName.Substring($root.Length + 1))"
    }
}

foreach ($file in $files) {
    $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    if ($file.Length -gt 100MB) {
        Add-Error "100 MiB 초과 파일: $relative ($($file.Length) bytes)"
    }

    if ($file.Extension.ToLowerInvariant() -in @('.iso', '.xex', '.exe', '.dll', '.pdb', '.ar', '.arl', '.pac', '.pak', '.xma', '.dds', '.bin', '.zst', '.sav', '.save', '.zip', '.7z', '.rar', '.tar', '.gz', '.dmp', '.db', '.sqlite')) {
        Add-Error "금지된 실행/게임/압축 파일 형식: $relative"
    }

    if ($relative -match '^(Analysis|QA Saves|Installer Sources|Sonic Unleashed DLC Pack \[Xbox 360\]|Update File|UnleashedRecomp-Windows|outputs|korean-smoke-test|SpreadsheetBuild)/') {
        Add-Error "금지된 작업 경로: $relative"
    }

    if ($file.Length -ge 2) {
        $stream = [IO.File]::OpenRead($file.FullName)
        try {
            $first = $stream.ReadByte()
            $second = $stream.ReadByte()
            if ($first -eq 0x4d -and $second -eq 0x5a) {
                Add-Error "PE 실행 파일 헤더 발견: $relative"
            }
        }
        finally {
            $stream.Dispose()
        }
    }
}

foreach ($file in $files | Where-Object { $_.Extension.ToLowerInvariant() -in @('.md', '.txt', '.json', '.py', '.ps1', '.cs', '.cpp', '.gitignore', '.gitattributes', '.patch') -or $_.Name -in @('.gitignore', '.gitattributes') }) {
    $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    $text = [IO.File]::ReadAllText($file.FullName)
    foreach ($pattern in @(
        '(?i)github_pat_[A-Za-z0-9_]{20,}',
        '(?i)gh[pousr]_[A-Za-z0-9]{20,}',
        'AKIA[0-9A-Z]{16}',
        '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        '(?i)C:\\Users\\[^\\\s]+',
        '(?i)E:\\Vibecoding\\'
    )) {
        if ($text -match $pattern) {
            Add-Error "개인 경로 또는 비밀정보 패턴 발견: $relative / $pattern"
        }
    }
}

foreach ($file in $files | Where-Object { $_.Extension -eq '.json' }) {
    $relative = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    try {
        $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        Add-Error "JSON 구문 오류: $relative / $($_.Exception.Message)"
    }
}

# Current release checksums come from the reviewed manifest, not a stale v1.0.0 constant.
$releaseManifestPath = Join-Path $root 'Release/v1.0.2/manifest.json'
$releaseManifest = Get-Content -LiteralPath $releaseManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$expectedChecksums = @($releaseManifest.assets | ForEach-Object { $_.sha256 + '  ' + $_.file })
if ($releaseManifest.version -ne '1.0.2' -or $expectedChecksums.Count -ne 2) {
    Add-Error 'Current release manifest must contain both v1.0.2 packages.'
}
$checksumPath = Join-Path $root 'Release/SHA256SUMS.txt'
if (Test-Path -LiteralPath $checksumPath) {
    $actualChecksums = @((Get-Content -LiteralPath $checksumPath -Encoding UTF8) | Where-Object { $_.Trim() })
    if (($actualChecksums -join "`n") -cne ($expectedChecksums -join "`n")) {
        Add-Error 'Release/SHA256SUMS.txt 내용이 현재 릴리스 manifest와 다릅니다.'
    }
}

if (Test-Path -LiteralPath (Join-Path $root '.git')) {
    $tracked = @(& git -C $root ls-files)
    if ($LASTEXITCODE -ne 0) {
        Add-Error 'git ls-files 실행 실패'
    }
    foreach ($relative in $tracked) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $relative) -PathType Leaf)) {
            Add-Error "Git 인덱스가 없는 파일을 가리킵니다: $relative"
        }
    }
}
else {
    $warnings.Add('Git 저장소를 아직 초기화하지 않아 추적 후보는 파일 시스템 기준으로만 검사했습니다.')
}

Write-Host "검사 파일: $($files.Count)"
foreach ($warning in $warnings) {
    Write-Warning $warning
}
if ($errors.Count -gt 0) {
    foreach ($message in $errors) {
        Write-Error $message
    }
    exit 1
}

Write-Host '공개 트리 검사 통과'
