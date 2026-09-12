# Subtitle FCO/FTE generation helpers extracted from the reviewed v1.0.0 builder.
function Read-BinaryObject([string] $path, [Type] $type) {
    $reader = [Amicitia.IO.Binary.BinaryObjectReader]::new($path, $endianness, $encoding)
    try { return $readObject.MakeGenericMethod($type).Invoke($reader, @()) }
    finally { $reader.Dispose() }
}

function Write-BinaryObject([string] $path, [Type] $type, [object] $value) {
    $writer = [Amicitia.IO.Binary.BinaryObjectWriter]::new($path, $endianness, $encoding)
    try { $writeObject.MakeGenericMethod($type).Invoke($writer, @($value)) }
    finally { $writer.Dispose() }
}

function Invoke-HedgeArcPack([string] $directory) {
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $hedgeArcPack
    $startInfo.ArgumentList.Add($directory)
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardInput = $true
    $process = [Diagnostics.Process]::Start($startInfo)
    $process.StandardInput.WriteLine('hh')
    $process.StandardInput.Close()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "Archive packing failed for $directory." }
}

function Get-GlyphWidth([string] $glyph) {
    switch ($glyph) {
        '!' { return 10 }; '?' { return 15 }; ',' { return 8 }; '.' { return 8 }
        '…' { return 28 }; "'" { return 8 }; '"' { return 14 }; ':' { return 9 }
        ';' { return 9 }; '(' { return 13 }; ')' { return 13 }; '[' { return 13 }
        ']' { return 13 }; '~' { return 18 }
    }
    if ([int][char]$glyph -le 0x7F) { return 18 }
    return 28
}

function Patch-SubtitleFile {
    param(
        [Parameter(Mandatory)] [string] $ArchiveName,
        [Parameter(Mandatory)] [string] $ArchiveDirectory,
        [Parameter(Mandatory)] [string] $FcoFile,
        [Parameter(Mandatory)] [object[]] $Rows
    )

    $stem = [IO.Path]::GetFileNameWithoutExtension($FcoFile)
    $fcoPath = Join-Path $ArchiveDirectory $FcoFile
    $ftePath = Join-Path $ArchiveDirectory "$stem.fte"
    $fco = Read-BinaryObject $fcoPath ([libfco.FontConverse])
    $fte = Read-BinaryObject $ftePath ([libfco.FontTexture])
    $originalTextureNames = @($fte.Textures | ForEach-Object { [string]$_.Name })

    $textureName = "${stem}_000"
    $textureIndex = -1
    for ($index = 0; $index -lt $fte.Textures.Count; $index++) {
        if ($fte.Textures[$index].Name -eq $textureName) { $textureIndex = $index; break }
    }
    if ($textureIndex -lt 0) { throw "$ArchiveName/$FcoFile has no text texture named $textureName." }
    $ddsPath = Join-Path $ArchiveDirectory "$textureName.dds"
    $texture = $fte.Textures[$textureIndex]
    $atlasWidth = [int]$texture.Size.X
    $atlasHeight = [int]$texture.Size.Y
    # FTE files also contain common material textures before their subtitle
    # atlases. Only the numbered textures belonging to this FCO stem may be
    # used as font pages. Treating every FTE texture as a subtitle page corrupts
    # glyph IDs as soon as a long scene spills past its first atlas.
    $pageTextureIndices = [Collections.Generic.List[int]]::new()
    $pageTextureIndices.Add($textureIndex)
    for ($index = 0; $index -lt $fte.Textures.Count; $index++) {
        if ($index -eq $textureIndex) { continue }
        if ($fte.Textures[$index].Name -match ('^' + [regex]::Escape($stem) + '_\d{3}$')) {
            $pageTextureIndices.Add($index)
        }
    }
    $atlasMaps = [Collections.Generic.List[object]]::new()
    for ($pageIndex = 0; $pageIndex -lt $pageTextureIndices.Count; $pageIndex++) {
        $pageTextureIndex = $pageTextureIndices[$pageIndex]
        $pageTexture = $fte.Textures[$pageTextureIndex]
        $expectedPageName = "${stem}_$($pageIndex.ToString('000'))"
        if ($pageTexture.Name -ne $expectedPageName) {
            throw "$ArchiveName/$FcoFile subtitle texture order is not contiguous: expected $expectedPageName, found $($pageTexture.Name)."
        }
        $pageTexture.Size = [Numerics.Vector2]::new([single]$atlasWidth, [single]$atlasHeight)
        $fte.Textures[$pageTextureIndex] = $pageTexture
        $pageDdsPath = Join-Path $ArchiveDirectory "$($pageTexture.Name).dds"
        if (-not (Test-Path -LiteralPath $pageDdsPath -PathType Leaf)) {
            throw "$ArchiveName/$FcoFile is missing subtitle atlas $pageDdsPath."
        }
        $pageMap = [Collections.Generic.List[object]]::new()
        $pageMap.Add([ordered]@{ character = ''; id = -1; rect = @(0, 0, $atlasWidth, $atlasHeight) })
        $atlasMaps.Add($pageMap)
    }

    $rowByCoordinate = @{}
    foreach ($row in $Rows) {
        $coordinate = "$($row.group_index)/$($row.cell_index)"
        if ($rowByCoordinate.ContainsKey($coordinate)) { throw "Duplicate subtitle coordinate: $ArchiveName/$FcoFile/$coordinate" }
        $rowByCoordinate[$coordinate] = $row
    }

    $texts = [Collections.Generic.List[string]]::new()
    foreach ($row in $Rows) {
        if (-not [string]::IsNullOrEmpty([string]$row.korean)) { $texts.Add([string]$row.korean) }
    }

    $spaceId = $null
    $spaceCharacterIndex = $null
    $availableCharacterIndices = [Collections.Generic.List[int]]::new()
    for ($index = 0; $index -lt $fte.Characters.Count; $index++) {
        $character = $fte.Characters[$index]
        if ($character.TextureIndex -ne $textureIndex) { continue }
        $height = [Math]::Abs([double]$character.BottomRight.Y - [double]$character.TopLeft.Y)
        $width = [Math]::Abs([double]$character.BottomRight.X - [double]$character.TopLeft.X)
        if ($null -eq $spaceId -and $height -lt 0.00001 -and $width -gt 0) {
            $spaceId = [int]$character.CharacterID
            $spaceCharacterIndex = $index
        }
    }
    $nextCharacterId = 1 + (($fte.Characters | Measure-Object CharacterID -Maximum).Maximum)
    if ($null -eq $spaceId) {
        $spaceCharacter = [libfco.Character]::new()
        $spaceCharacter.CharacterID = $nextCharacterId++
        $spaceCharacter.TextureIndex = $textureIndex
        $spaceCharacter.TopLeft = [Numerics.Vector2]::Zero
        $spaceCharacter.BottomRight = [Numerics.Vector2]::new([single](14 / $atlasWidth), [single]0)
        $fte.Characters.Add($spaceCharacter)
        $spaceCharacterIndex = $fte.Characters.Count - 1
        $spaceId = [int]$spaceCharacter.CharacterID
    }

    # Reuse only character entries that already belong to this subtitle's text
    # atlases. Entries on the common material textures must remain untouched.
    for ($index = 0; $index -lt $fte.Characters.Count; $index++) {
        if ($index -eq $spaceCharacterIndex) { continue }
        if ([int]$fte.Characters[$index].CharacterID -eq 0) { continue }
        if ($pageTextureIndices.Contains([int]$fte.Characters[$index].TextureIndex)) {
            $availableCharacterIndices.Add($index)
        }
    }
    $spaceCharacter = $fte.Characters[$spaceCharacterIndex]
    $spaceCharacter.BottomRight = [Numerics.Vector2]::new(
        [single]($spaceCharacter.TopLeft.X + (14 / $atlasWidth)), $spaceCharacter.TopLeft.Y)
    $fte.Characters[$spaceCharacterIndex] = $spaceCharacter

    function Get-CharacterKey([string] $glyph, [int] $lineIndex, [bool] $isMultiline) {
        if ($glyph -eq ' ' -or $glyph -eq "`n") { return $glyph }
        return "normal|$glyph"
    }

    # PowerShell's default ordered dictionaries compare string keys without
    # regard to case. Subtitle atlases need distinct entries for pairs such as
    # E/e; otherwise "Excellent!" is serialized as "ExcEllEnt!".
    $characterIds = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
    $characterIds[' '] = $spaceId
    $characterIds["`n"] = 0
    $glyphLocations = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
    $glyphLocations[' '] = [ordered]@{
        texture_index = $textureIndex
        top_left = @([single]$spaceCharacter.TopLeft.X, [single]$spaceCharacter.TopLeft.Y)
        bottom_right = @([single]$spaceCharacter.BottomRight.X, [single]$spaceCharacter.BottomRight.Y)
    }
    $x = 0; $y = 0; $glyphHeight = 36; $spacing = 2; $availableCursor = 0; $pageIndex = 0
    foreach ($text in $texts) {
        $isMultiline = $text.Contains("`n")
        $lineIndex = 0
        foreach ($glyphValue in $text.ToCharArray()) {
            $glyph = [string]$glyphValue
            if ($glyph -eq "`r") { continue }
            $characterKey = Get-CharacterKey $glyph $lineIndex $isMultiline
            if ($glyph -eq "`n") { $lineIndex++; continue }
            if ($characterIds.Contains($characterKey)) { continue }
            $glyphWidth = Get-GlyphWidth $glyph
            if ($x + $glyphWidth -gt $atlasWidth) { $x = 0; $y += $glyphHeight + $spacing }
            if ($y + $glyphHeight -gt $atlasHeight) {
                $pageIndex++
                $x = 0; $y = 0
                if ($pageIndex -ge $pageTextureIndices.Count) {
                    throw "$ArchiveName/$FcoFile font atlases cannot hold all translated glyphs."
                }
            }
            if ($availableCursor -ge $availableCharacterIndices.Count) {
                $newCharacter = [libfco.Character]::new()
                $newCharacter.CharacterID = $nextCharacterId++
                $newCharacter.TextureIndex = $pageTextureIndices[$pageIndex]
                $newCharacter.TopLeft = [Numerics.Vector2]::Zero
                $newCharacter.BottomRight = [Numerics.Vector2]::Zero
                $fte.Characters.Add($newCharacter)
                $availableCharacterIndices.Add($fte.Characters.Count - 1)
            }
            $characterIndex = $availableCharacterIndices[$availableCursor++]
            $character = $fte.Characters[$characterIndex]
            $id = [int]$character.CharacterID
            $character.TextureIndex = $pageTextureIndices[$pageIndex]
            $character.TopLeft = [Numerics.Vector2]::new([single]($x / $atlasWidth), [single]($y / $atlasHeight))
            $character.BottomRight = [Numerics.Vector2]::new(
                [single](($x + $glyphWidth) / $atlasWidth), [single](($y + $glyphHeight) / $atlasHeight))
            $fte.Characters[$characterIndex] = $character
            $characterIds[$characterKey] = $id
            $glyphLocations[$characterKey] = [ordered]@{
                texture_index = $pageTextureIndices[$pageIndex]
                top_left = @([single]$character.TopLeft.X, [single]$character.TopLeft.Y)
                bottom_right = @([single]$character.BottomRight.X, [single]$character.BottomRight.Y)
            }
            $lineOffset = 0
            $punctuationOffset = if ($glyph -eq ',' -or $glyph -eq '.') { 8 } elseif ($glyph -eq '~') { 3 } elseif ($glyph -eq '…') { 2 } else { 0 }
            $atlasMaps[$pageIndex].Add([ordered]@{
                character = $glyph; id = $id
                rect = @($x, $y, ($x + $glyphWidth), ($y + $glyphHeight))
                vertical_offset = $lineOffset + $punctuationOffset
            })
            $x += $glyphWidth + $spacing
        }
    }

    function Convert-ToMessage([string] $text) {
        $ids = [Collections.Generic.List[int]]::new()
        $isMultiline = $text.Contains("`n")
        $lineIndex = 0
        foreach ($glyphValue in $text.ToCharArray()) {
            $glyph = [string]$glyphValue
            if ($glyph -eq "`r") { continue }
            $characterKey = Get-CharacterKey $glyph $lineIndex $isMultiline
            if (-not $characterIds.Contains($characterKey)) { throw "No character ID assigned for '$glyph'." }
            $ids.Add([int]$characterIds[$characterKey])
            if ($glyph -eq "`n") { $lineIndex++ }
        }
        return [int[]]$ids.ToArray()
    }

    $replaced = 0
    for ($groupIndex = 0; $groupIndex -lt $fco.Groups.Count; $groupIndex++) {
        $group = $fco.Groups[$groupIndex]
        for ($cellIndex = 0; $cellIndex -lt $group.Cells.Count; $cellIndex++) {
            $cell = $group.Cells[$cellIndex]
            $coordinate = "$groupIndex/$cellIndex"
            if ($rowByCoordinate.ContainsKey($coordinate)) {
                $row = $rowByCoordinate[$coordinate]
                if (-not [string]::IsNullOrEmpty([string]$row.korean)) {
                    $cell.Message = Convert-ToMessage ([string]$row.korean)
                    $cell.SubCells.Clear()
                    $cell.Highlights.Clear()
                    $replaced++
                }
                elseif ($cell.Message.Count -gt 0) {
                    throw "$ArchiveName/$FcoFile/$coordinate has Japanese text but no Korean translation."
                }
            }
            elseif ($cell.Message.Count -gt 0) {
                throw "$ArchiveName/$FcoFile contains an untracked non-empty cell at $coordinate."
            }
        }
    }
    if ($replaced -ne $texts.Count) { throw "$ArchiveName/$FcoFile replaced $replaced of $($texts.Count) target cells." }

    $null = Write-BinaryObject $ftePath ([libfco.FontTexture]) $fte
    # FTE serialization assigns character IDs from the saved texture grouping.
    # Read it back and bind every Korean glyph to that final ID before saving FCO.
    $savedFte = Read-BinaryObject $ftePath ([libfco.FontTexture])
    $finalCharacterIds = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
    $finalCharacterIds["`n"] = 0
    foreach ($entry in $glyphLocations.GetEnumerator()) {
        $location = $entry.Value
        $matches = @($savedFte.Characters | Where-Object {
            $_.TextureIndex -eq $location.texture_index -and
            [Math]::Abs([double]$_.TopLeft.X - [double]$location.top_left[0]) -lt 0.000001 -and
            [Math]::Abs([double]$_.TopLeft.Y - [double]$location.top_left[1]) -lt 0.000001 -and
            [Math]::Abs([double]$_.BottomRight.X - [double]$location.bottom_right[0]) -lt 0.000001 -and
            [Math]::Abs([double]$_.BottomRight.Y - [double]$location.bottom_right[1]) -lt 0.000001
        })
        if ($matches.Count -lt 1) { throw "Could not resolve the final FTE ID for '$($entry.Key)' in $ArchiveName/$FcoFile." }
        $finalCharacterIds[$entry.Key] = [int]$matches[0].CharacterID
    }
    $characterIds = $finalCharacterIds
    foreach ($row in $Rows) {
        if ([string]::IsNullOrEmpty([string]$row.korean)) { continue }
        $cell = $fco.Groups[[int]$row.group_index].Cells[[int]$row.cell_index]
        $cell.Message = Convert-ToMessage ([string]$row.korean)
    }
    $null = Write-BinaryObject $fcoPath ([libfco.FontConverse]) $fco

    # Validate the serialized files, not only the in-memory objects. This is
    # especially important for version-0 FTEs, whose reader derives IDs from
    # character order and texture page.
    $verifiedFte = Read-BinaryObject $ftePath ([libfco.FontTexture])
    $verifiedFco = Read-BinaryObject $fcoPath ([libfco.FontConverse])
    if ($verifiedFte.Textures.Count -ne $originalTextureNames.Count) {
        throw "$ArchiveName/$FcoFile changed the FTE texture count."
    }
    for ($index = 0; $index -lt $originalTextureNames.Count; $index++) {
        if ([string]$verifiedFte.Textures[$index].Name -ne $originalTextureNames[$index]) {
            throw "$ArchiveName/$FcoFile changed texture $index from $($originalTextureNames[$index]) to $($verifiedFte.Textures[$index].Name)."
        }
    }
    $verifiedCharactersById = @{}
    foreach ($character in $verifiedFte.Characters) {
        $id = [int]$character.CharacterID
        if ($verifiedCharactersById.ContainsKey($id)) { throw "$ArchiveName/$FcoFile has duplicate serialized character ID $id." }
        $verifiedCharactersById[$id] = $character
    }
    foreach ($row in $Rows) {
        if ([string]::IsNullOrEmpty([string]$row.korean)) { continue }
        $expectedIds = @(Convert-ToMessage ([string]$row.korean))
        $verifiedCell = $verifiedFco.Groups[[int]$row.group_index].Cells[[int]$row.cell_index]
        $actualIds = @($verifiedCell.Message)
        if ((Compare-Object $expectedIds $actualIds -SyncWindow 0).Count -ne 0) {
            throw "$ArchiveName/$FcoFile/$($row.group_index)/$($row.cell_index) changed message IDs during serialization."
        }
        foreach ($id in $actualIds) {
            if ([int]$id -eq 0) { continue }
            if (-not $verifiedCharactersById.ContainsKey([int]$id)) {
                throw "$ArchiveName/$FcoFile references missing character ID $id."
            }
            $character = $verifiedCharactersById[[int]$id]
            if (-not $pageTextureIndices.Contains([int]$character.TextureIndex)) {
                throw "$ArchiveName/$FcoFile references character ID $id on non-subtitle texture $($character.TextureIndex)."
            }
        }
    }
    for ($renderPage = 0; $renderPage -lt $atlasMaps.Count; $renderPage++) {
        $pageName = "${stem}_$($renderPage.ToString('000'))"
        $pageDdsPath = Join-Path $ArchiveDirectory "$pageName.dds"
        $mapPath = Join-Path $ArchiveDirectory "$pageName.atlas-map.json"
        ConvertTo-Json -InputObject ([object[]]$atlasMaps[$renderPage].ToArray()) -Depth 4 |
            Set-Content -LiteralPath $mapPath -Encoding utf8
        & $python (Join-Path $projectRoot 'Scripts/patch_opening_atlas.py') $pageDdsPath $mapPath $font $pageDdsPath
        if ($LASTEXITCODE -ne 0) { throw "Atlas patch failed for $ArchiveName/$FcoFile page $renderPage." }
        Remove-Item -LiteralPath $mapPath
        Remove-Item -LiteralPath ([IO.Path]::ChangeExtension($pageDdsPath, '.preview.png'))
    }
    return $replaced
}
