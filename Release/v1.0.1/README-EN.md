# Korean Translation v1.0.1 — Full

For Unleashed Recompiled v1.0.3 Windows x64. Full includes everything in Basic. **You do not need to install Basic first.** Enable only one edition.

Options and achievement translations now run entirely in the Windows EXE. **The utility never checks, backs up, patches or restores `patched/default.xex`.** This removes rejection caused by a different valid regional/digital XEX hash. Other game versions, platforms and custom-built Windows EXEs remain unsupported unless explicitly verified.

**Upgrading from v1.0.0 Full:** close the game and run **.exe 원본 복원 in the old Full utility first**. Then replace the HMM mod with the new Full ZIP and follow the steps below. Old Full also modified another game file; overwriting only the EXE would leave that change behind. The new utility detects the old Full EXE and stops with migration instructions. Keep the old utility and `korean-native-backup` until migration is complete. This preliminary restore is unnecessary for Basic users or a Full installation that failed during file validation.

1. Before installing Full, launch Unleashed Recompiled at least once and complete its initial setup. The first launch must create `config.toml`.
2. Install the Full ZIP through HedgeModManager (HMM).
3. Close the game, open the Full mod folder in HMM, and run `KoreanFullSetup.exe`.
4. Select the game's `UnleashedRecomp.exe` and click **.exe 한국어화 적용**. The utility automatically uses its parent folder and locates the required files and backup paths.
5. Enable the Korean mod and save in HMM. Select **English** text and enable **subtitles** in the game. Keep your preferred voice language.

With `portable.txt` beside the EXE, the utility checks `config.toml` in that folder. Otherwise it automatically checks `%APPDATA%\UnleashedRecomp\config.toml`, matching the game's Windows user-data location. Do not copy the configuration into the game folder.

If the configuration is missing, launch the game, complete initial setup, close it, and rerun the utility. If you have already launched it, check that you selected the correct EXE and are using the same Windows account. Missing or unsupported `Language` or `Subtitles` entries in `[System]` stop installation safely. Check the game version and configuration state; the utility never inserts missing keys.

Configuration checks are read-only. Installation, reinstallation and restoration preserve the entire configuration, including voice language. Basic does not use this setup utility or its configuration checks.

For all DLC, use the default HMM mod configuration. For partial DLC, select the first installed pack in the list; select No DLC if none is installed.

Before removing Full or switching to Basic, close the game, click **.exe 원본 복원**, then disable Full in HMM. Keep `korean-native-backup/Original/UnleashedRecomp.exe` for recovery. Restoration verifies the original EXE and works without `Support` or `config.toml`. Moving the entire game folder is supported when its backup moves with it. Keeping the HMM mod enabled retains the base translations. Saves and other mods' enabled states remain unchanged.

If interrupted, rerun the utility to install or restore. Corrupted backups and EXEs changed by another tool are rejected without being overwritten. Do not delete the backup or force a patch onto another EXE version.

Translation: nonunsaram; assistance: GPT-6 Astra. No game, DLC or completed game EXE/XEX is distributed. See Licenses and Support/Licenses for credits and licenses, and Source.zip for source code and the verification scope.

## v1.0.1 changes and other mods

Preserves Chip's name-form self-reference in 33 translation entries and restores Sonic's `Hey!` in one entry. Includes repeated regional copies: 74 dialogue cells across 17 archives. Full also corrects the Korean spelling of Werehog in achievements/options and replaces the EXE installation backend.

When using Denoised, Denoised DLC or Remastered UI, place the Korean patch above them in HMM, save, and restart the game. Keep Denoised DLC below both Denoised Base and Remastered UI. This follows the Denoised author's prior guidance; combined gameplay has not been verified. If corruption persists, disable Denoised DLC and compare. Its GameBanana page is currently private, preventing a fresh download for reproduction.

Basic requires no EXE utility or configuration validation. Full also does not require installing Basic first.
