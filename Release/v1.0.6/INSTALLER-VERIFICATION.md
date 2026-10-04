# Installer safety contract

Source of truth: the embedded manifest. state.json never authorizes writes. Paths are fixed to UnleashedRecomp.exe and, for verified legacy recovery, patched/default.xex. Original backups are never overwritten. Unknown EXEs and missing/corrupt required backups fail before writes. A known legacy XEX is also detected after a partially completed old restore.

The XEX is restored first, then the EXE is atomically replaced. Ordinary failures roll both back. An abrupt process termination can leave the stock XEX with the old EXE; the next restore/install recognizes that verified intermediate state. Retained original backups permit recovery. This is recoverable sequencing, not filesystem-wide atomicity across two files. No unverified reverse patch is attempted.

EXE families: v1.0.0 df253ffa… (82,896,896 bytes); initial v1.0.1 18de8ced… (82,903,552); reviewed v1.0.1 through v1.0.5 f8869e8b… (90,183,680). The public v1.0.1 record describes the reviewed family. The early package is retained locally; its public distribution is unconfirmed.

All game archive files must match the v1.0.5 approvedGameFiles record. Existing graphics/translation and the latest EXE delta are unchanged. Testing is restricted to synthetic inputs and disposable copies. No real game, user configuration, mods or save data is modified by release tests.

Build requirements: Windows, Python 3.10+, PowerShell 7, .NET Framework compiler, verified private v1.0.5 Full ZIP. Run prepare_release_v106.py with prior ZIP, prior record, NEW staging directory, Release/v1.0.6/release-record.json; test_full_backend_v106.py and test_full_release_v106.py; then package_independent_final.py with staging, NEW output directory, release record and clean source snapshot. Final verification invokes Verify-InstallerManifest.ps1 via static PEReader, without loading the assembly. See test-results.json and verification.json for recorded results.
