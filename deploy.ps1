# 점검 후 커밋하고 git push origin main 으로 배포 (Cloudflare Pages가 push를 받아 자동 빌드)
# 사용법: .\deploy.ps1 "커밋 메시지"
param([Parameter(Mandatory = $true)][string]$Message)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$git = "F:\Tools\Git\cmd\git.exe"
& F:\Tools\Python313\python.exe check.py
if ($LASTEXITCODE -ne 0) { throw "점검 실패" }
& $git add -A
& $git commit -m $Message
& $git push origin main
