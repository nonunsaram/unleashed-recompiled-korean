param([string]$PythonPath = "python")
$ErrorActionPreference = 'Stop'
# Configuration cases now run with the complete EXE-only backend suite.
& $PythonPath (Join-Path $PSScriptRoot 'test_full_backend_v101.py')
exit $LASTEXITCODE
