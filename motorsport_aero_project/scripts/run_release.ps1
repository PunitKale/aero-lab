$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python=Join-Path (Split-Path $projectRoot) '.venv312/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) { $python=Join-Path $projectRoot '.venv/Scripts/python.exe' }
$commands=@(@('-m','src.pipeline','--draws','200','--search-seeds','5'),@('scripts/add_experiments.py'),@('-m','src.visualization'),@('scripts/build_workbook.py'),@('scripts/build_powerbi.py'),@('scripts/validate_powerbi.py'),@('-m','pytest','-q','--junitxml=reports/tests.xml'),@('-m','src.reporting'))
foreach ($arguments in $commands) {
    & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw "Release step failed: $arguments" }
}
& (Join-Path $PSScriptRoot 'recalculate_excel.ps1') -WorkbookPath (Join-Path $projectRoot 'outputs/aero-release/Motorsport_Aero_Engineering.xlsx')
& $python -m src.reporting
