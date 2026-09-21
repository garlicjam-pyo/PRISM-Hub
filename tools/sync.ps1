# tools/sync.ps1 -- 두 컴퓨터 간 작업 동기화 도우미 (Windows PowerShell)
# 사용: 작업 시작 전  .\tools\sync.ps1 start      (원격 최신 반영)
#       작업 끝난 뒤  .\tools\sync.ps1 end "메시지" (커밋 + 푸시)
param([string]$mode = "start", [string]$msg = "")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
switch ($mode) {
  "start" {
    git fetch origin
    $local = git rev-parse HEAD; $remote = git rev-parse origin/main
    if ((git status --porcelain) -ne $null) { Write-Host "주의: 커밋되지 않은 변경이 있습니다. 먼저 end 로 커밋하거나 stash 하세요." -ForegroundColor Yellow; git status --short; exit 1 }
    git pull --ff-only origin main
    Write-Host ("동기화 완료: " + (git log -1 --oneline)) -ForegroundColor Green
    Write-Host "남은 항목은 README 8절, 진행 이력은 logs/EXECUTION_LOG.md 참조."
  }
  "end" {
    if ($msg -eq "") { $msg = Read-Host "커밋 메시지" }
    git add -A
    git commit -m $msg
    git pull --rebase origin main
    git push origin main
    Write-Host ("푸시 완료: " + (git log -1 --oneline)) -ForegroundColor Green
  }
  default { Write-Host "mode 는 start 또는 end" }
}
