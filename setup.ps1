$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'ps5/tools/setup.py'
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $script @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $script @args
} else {
    throw 'Install Python 3.11 or newer, then run this script again.'
}
exit $LASTEXITCODE
