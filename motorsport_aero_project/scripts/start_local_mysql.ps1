$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot
$workspaceRoot=Split-Path $projectRoot
$dataPath=Join-Path $workspaceRoot '.runtime/mysql-data'
$binary='C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe'
if (!(Test-Path -LiteralPath $dataPath)) { throw 'Isolated database directory missing. Configure your own MySQL and .env.' }
if (Get-NetTCPConnection -LocalPort 3307 -State Listen -ErrorAction SilentlyContinue) { Write-Output 'Port 3307 is already listening; no second server started.'; exit }
Start-Process -FilePath $binary -ArgumentList '--no-defaults',("--datadir=`"$dataPath`""),'--port=3307','--bind-address=127.0.0.1','--mysqlx=0','--log-error=mysql-error.log' -WindowStyle Hidden
Write-Output 'Started isolated localhost MySQL instance on port 3307.'
