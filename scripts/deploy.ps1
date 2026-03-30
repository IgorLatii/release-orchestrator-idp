param(
    [string]$Server = "deploy@20.251.155.82"
)

$ErrorActionPreference = "Stop"
$AppDir = "/opt/release-orchestrator-idp"

Write-Host "==> Creating archive"

if (Test-Path "project.tar.gz") {
    Remove-Item "project.tar.gz" -Force
}

tar -czf project.tar.gz `
  --exclude=".git" `
  --exclude=".venv" `
  --exclude="__pycache__" `
  .

Write-Host "==> Copy project to VM"
scp project.tar.gz "${Server}:/tmp/project.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "Copy project failed" }

Write-Host "==> Copy env"
scp infra/docker/.env.prod "${Server}:${AppDir}/env/prod.env"
if ($LASTEXITCODE -ne 0) { throw "Copy env failed" }

Write-Host "==> Deploying"
ssh $Server "mkdir -p $AppDir/repo && rm -rf $AppDir/repo/*"
if ($LASTEXITCODE -ne 0) { throw "Prepare remote dir failed" }

ssh $Server "tar -xzf /tmp/project.tar.gz -C $AppDir/repo"
if ($LASTEXITCODE -ne 0) { throw "Extract archive failed" }

ssh $Server "rm -f /tmp/project.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "Cleanup archive failed" }

ssh $Server "cd $AppDir/repo/infra/docker && docker compose --env-file $AppDir/env/prod.env -f compose.prod.yml up -d --build"
if ($LASTEXITCODE -ne 0) { throw "Remote docker compose failed" }

Write-Host "==> Deploy finished"