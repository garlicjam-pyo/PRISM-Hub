# Synchronize the CURRENT branch; never implicitly push another branch's main.
param([ValidateSet('start','end')][string]$mode='start', [string]$msg='')
$ErrorActionPreference='Stop'
function Invoke-Git {
    & git @args
    if ($LASTEXITCODE -ne 0) { throw "git failed (exit $LASTEXITCODE): $args" }
}
Set-Location (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$branch = Invoke-Git symbolic-ref --quiet --short HEAD
if (Invoke-Git ls-files --unmerged) { throw 'Resolve merge conflicts before synchronizing.' }
if ((Test-Path (Invoke-Git rev-parse --git-path rebase-merge)) -or (Test-Path (Invoke-Git rev-parse --git-path rebase-apply))) {
    throw 'Finish the current rebase before synchronizing.'
}
if ($mode -eq 'end') {
    if ([string]::IsNullOrWhiteSpace($msg)) { throw 'Provide a commit message: sync.ps1 end "message"' }
    Invoke-Git add -A
    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 1) { Invoke-Git commit -m $msg }
    elseif ($LASTEXITCODE -ne 0) { throw 'Cannot inspect staged changes.' }
} elseif (Invoke-Git status --porcelain) {
    throw 'Working tree has changes. Commit or stash before start.'
}
Invoke-Git fetch origin
& git show-ref --verify --quiet "refs/remotes/origin/$branch"
if ($LASTEXITCODE -eq 0) {
    if ($mode -eq 'start') { Invoke-Git merge --ff-only "origin/$branch" }
    else { Invoke-Git rebase "origin/$branch" }
} elseif ($LASTEXITCODE -ne 1) { throw 'Cannot inspect remote branch.' }
if ($mode -eq 'end') { Invoke-Git push -u origin "HEAD:refs/heads/$branch" }
Write-Host "Synchronized branch: $branch"
